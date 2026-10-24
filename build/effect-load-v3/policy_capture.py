"""Read only the newly created owned test process; never change its policy."""
import ctypes,json
from ctypes import wintypes as w
from pathlib import Path

def wrap(base, high_qos=False):
    class RecordedProcess(base):
        def __init__(self,command,*,cwd,stdout,stderr):
            super().__init__(command,cwd=cwd,stdout=stdout,stderr=stderr)
            data={'pid':self.pid,'fixture_changes_policy':high_qos,'sample':'startup only','lifetime':'owned test process only; ends with process'}
            try:
                class State(ctypes.Structure):
                    _fields_=[('Version',w.DWORD),('ControlMask',w.DWORD),('StateMask',w.DWORD)]
                api=self.k.GetProcessInformation
                api.argtypes=[w.HANDLE,ctypes.c_int,w.LPVOID,w.DWORD];api.restype=w.BOOL
                state=State(1,0,0)
                ok=bool(api(self._process,4,ctypes.byref(state),ctypes.sizeof(state)))
                data.update(read_ok=ok,error=0 if ok else ctypes.get_last_error(),version=state.Version,control_mask=state.ControlMask,state_mask=state.StateMask)
                if high_qos and ok:
                    target=State(1,state.ControlMask|1,state.StateMask & ~1)
                    setter=self.k.SetProcessInformation
                    setter.argtypes=[w.HANDLE,ctypes.c_int,w.LPVOID,w.DWORD];setter.restype=w.BOOL
                    applied=bool(setter(self._process,4,ctypes.byref(target),ctypes.sizeof(target)))
                    after=State(1,0,0);verified=bool(api(self._process,4,ctypes.byref(after),ctypes.sizeof(after)))
                    data.update(policy_applied=applied,policy_verified=verified and bool(after.ControlMask&1) and not bool(after.StateMask&1),after_control_mask=after.ControlMask,after_state_mask=after.StateMask)
            except Exception as error:data['read_error']=str(error)
            (Path(cwd)/'process-policy.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    return RecordedProcess
