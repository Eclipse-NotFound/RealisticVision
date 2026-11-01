"""Low-frequency CPU counters for one caller-owned Windows process handle.

No process discovery, window access, settings changes, or disk writes.  The
caller must keep the handle open until stop() returns and close it afterwards.
Lifecycle calls belong to the caller's thread; one sampler is used for one run.
"""

from __future__ import annotations

import copy
import ctypes
from ctypes import wintypes
import os
import threading
import time


class OwnedCpuSampler:
    """Collect cumulative counters every second, plus start/stop endpoints.

    start() and stop() return independent, JSON-compatible snapshots containing
    ``metadata`` and ``samples``.  The supplied PID is a label, not an ownership
    check: the caller is responsible for passing its own process's handle.
    """

    INTERVAL_SECONDS = 1.0

    def __init__(self, handle, pid):
        if os.name != "nt":
            raise OSError("OwnedCpuSampler requires Windows")
        handle_value = getattr(handle, "value", handle)
        if handle_value is None or int(handle_value) == 0:
            raise ValueError("A non-null caller-owned process handle is required")
        if int(pid) <= 0:
            raise ValueError("pid must be positive")
        self._handle = wintypes.HANDLE(int(handle_value))
        self._kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self._get_times = self._kernel.GetProcessTimes
        self._get_times.argtypes = [wintypes.HANDLE] + [
            ctypes.POINTER(wintypes.FILETIME)
        ] * 4
        self._get_times.restype = wintypes.BOOL
        self._get_cycles = self._kernel.QueryProcessCycleTime
        self._get_cycles.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(ctypes.c_ulonglong)
        ]
        self._get_cycles.restype = wintypes.BOOL
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._thread = None
        self._samples = []
        self._metadata = {
            "schema": 1,
            "sampler": "OwnedCpuSampler",
            "pid": int(pid),
            "pid_source": "caller-provided; not independently verified",
            "interval_seconds": self.INTERVAL_SECONDS,
            "status": "new",
            "handle_lifetime": "caller-managed; never closed by sampler",
            "counter_units": {
                "kernel_time_100ns": "100 ns",
                "user_time_100ns": "100 ns",
                "process_cycles": "raw CPU cycles; not elapsed time",
            },
            "sampling": "start/stop endpoints and one-second waits; no catch-up samples",
            "errors": [],
        }

    @staticmethod
    def _filetime(value):
        return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)

    @staticmethod
    def _error(api, exception=None):
        if exception is not None:
            return {"api": api, "error": repr(exception)}
        code = ctypes.get_last_error()
        return {"api": api, "winerror": code, "error": ctypes.FormatError(code).strip()}

    def _capture(self, reason):
        begin = time.perf_counter_ns()
        sample = {
            "reason": reason,
            "perf_counter_ns": begin,
            "time_ns": time.time_ns(),
            "kernel_time_100ns": None,
            "user_time_100ns": None,
            "process_cycles": None,
            "errors": [],
        }
        created, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
        try:
            if self._get_times(self._handle, ctypes.byref(created), ctypes.byref(exited),
                               ctypes.byref(kernel), ctypes.byref(user)):
                sample["kernel_time_100ns"] = self._filetime(kernel)
                sample["user_time_100ns"] = self._filetime(user)
            else:
                sample["errors"].append(self._error("GetProcessTimes"))
        except Exception as exc:
            sample["errors"].append(self._error("GetProcessTimes", exc))
        cycles = ctypes.c_ulonglong()
        try:
            if self._get_cycles(self._handle, ctypes.byref(cycles)):
                sample["process_cycles"] = int(cycles.value)
            else:
                sample["errors"].append(self._error("QueryProcessCycleTime"))
        except Exception as exc:
            sample["errors"].append(self._error("QueryProcessCycleTime", exc))
        sample["query_duration_ns"] = time.perf_counter_ns() - begin
        with self._lock:
            sample["sequence"] = len(self._samples)
            self._samples.append(sample)

    def _run(self):
        try:
            # An overdue wake produces one real sample, never invented zeros or
            # a burst of samples pretending to cover the missed interval.
            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                self._capture("interval")
        except Exception as exc:
            with self._lock:
                self._metadata["errors"].append({"stage": "worker", "error": repr(exc)})
            self._stop_event.set()

    def _snapshot(self):
        with self._lock:
            result = copy.deepcopy({"metadata": self._metadata, "samples": self._samples})
        result["metadata"]["sample_count"] = len(result["samples"])
        return result

    def start(self):
        if self._metadata["status"] != "new" or self._stop_event.is_set():
            raise RuntimeError("OwnedCpuSampler can only be started once")
        self._metadata["status"] = "running"
        self._capture("start")
        self._thread = threading.Thread(target=self._run, name="OwnedCpuSampler", daemon=True)
        self._thread.start()
        return self._snapshot()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
        if self._metadata["status"] == "running":
            self._capture("stop")
            with self._lock:
                self._metadata["status"] = "stopped"
        elif self._metadata["status"] == "new":
            with self._lock:
                self._metadata["status"] = "stopped_without_start"
        return self._snapshot()
