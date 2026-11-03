"""Re-read existing C1 evidence. No game launch or production-file writes.

Run from any directory with Python 3. Output defaults to audit.json beside this
script. Original JSON/SWF/source files remain untouched; hashes identify inputs.
"""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[2]
BUILD = MOD / "build"
OUTPUT = BUILD / "fire-exhaustive-output"
RUNS = ("c1grid-01c", "c1grid-02", "c1grid-diag-01", "c1grid-diag-02")


def fingerprint(path):
    return {"path": path.relative_to(MOD).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    result = {
        "date": "2026-11-03",
        "kind": "offline_reanalysis_not_new_runtime_test",
        "scope": "Existing C1 fixtures; no causal hit detection or player reproduction",
        "inputs": [fingerprint(MOD / p) for p in (
            "release/RealisticVisionMod.swf", "release/config.txt",
            "build/perf-20261102/src/RealisticVisionMod.as",
            "build/boundary-c1-output/baseline/src/RealisticVisionMod.as",
            "build/boundary-c1-output/inputs.json")],
        "checks": read_json(BUILD / "boundary-c1-output/checks-02/evidence/result.json"),
        "runs": [],
    }
    for name in RUNS:
        folder = OUTPUT / name
        data = read_json(folder / "evidence/result.json")
        probe = (folder / "CombatRenderProbeMod.as").read_text(encoding="utf-8-sig")
        source_paths = [folder / p / "RealisticVisionMod.as"
                        for p in ("rv-src", "vector-src", "candidate-src")]
        row = {
            "name": name, "scene": data.get("scene"),
            "inputs": [fingerprint(folder / p) for p in (
                "evidence/result.json", "analysis.json", "CombatRenderProbeMod.as",
                "rv.swf", "vector.swf", "candidate.swf")]
                + [fingerprint(p) for p in source_paths],
            "baseline_main_source_byte_equal": source_paths[0].read_bytes() == source_paths[1].read_bytes(),
            "baseline_swf_byte_equal": (folder / "rv.swf").read_bytes() == (folder / "vector.swf").read_bytes(),
            "probe_has_config_initialization_reference": any(
                token in probe for token in ("loadConfig(", "startup(", "applyVisionScale(", "fogSub=")),
            "profile_flag_false": "const PROFILE=false" in probe,
            "performance_summary": read_json(folder / "analysis.json"),
            "windows": [],
        }
        for index, case in enumerate(data["cases"]):
            positions = case["positions"]
            all_frames = case["allFrames"]
            profile = case["profile"]
            calls = case["calls"]
            rv_ms = sum(f["rv"] for f in all_frames)
            vision_wall = profile["applyVision"] + profile["updateWallSurface"]
            window = {
                "index": index, "variant": case["variant"],
                "warmup": case["warmup"], "sample_frames": len(case["frames"]),
                "profile_frames_including_warmup": calls["applyVision"],
                "all_frames": len(all_frames),
                "body_moved_sample_transitions": sum(
                    any(abs(a[j] - b[j]) > .01 for j in (0, 1))
                    for a, b in zip(positions, positions[1:])),
                "body_sample_transitions": max(0, len(positions) - 1),
                "fov_calls_including_warmup": calls["computeFov"],
                "fov_reasons_including_warmup": case.get("fovReasons"),
                "enemy_shot_lower_bound_not_hits": case["sampleNativeEnemyShotsLowerBound"],
                "unit_count_including_player_and_native_units": case["units"],
                "max_partial_enemies": case["maxPartialEnemies"],
                "rv_ms_including_warmup": rv_ms,
                "vision_plus_wall_ms_including_warmup": vision_wall,
                "vision_plus_wall_share_of_rv": round(vision_wall / rv_ms, 6),
                "fill_ms_per_call": round(profile["fillFogCache"] / calls["fillFogCache"], 6),
                "profile_inclusive_ms": profile,
                "calls_including_warmup": calls,
                "frame_fields": sorted(case["frames"][0]),
            }
            if positions and len(positions[0]) >= 6:
                window["live_eye_sample_span_xy"] = [
                    max(p[j] for p in positions) - min(p[j] for p in positions)
                    for j in (4, 5)]
            row["windows"].append(window)
        result["runs"].append(row)
    target = HERE / "audit.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": target.as_posix(), "runs": len(result["runs"]),
                      "windows": sum(len(r["windows"]) for r in result["runs"]),
                      "existing_pixel_checks": result["checks"]["checks"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
