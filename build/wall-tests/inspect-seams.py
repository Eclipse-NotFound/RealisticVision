"""Read-only wall/floor boundary measurement on full-game seam captures."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageChops

root = Path(__file__).resolve().parent.parent / "wall-test-output/game"
prefix = "baseline-" if "--baseline" in sys.argv else ""
data = json.loads((root / f"{prefix}seams-data.json").read_text())
measurements = []
for state in data["states"]:
    name, mode = state["position"], state["mode"]
    actual = Image.open(root / f"{prefix}seams-{name}-{mode}-fog.png").convert("L")
    native = Image.open(root / f"{prefix}seams-{name}-native-fog.png").convert("L")
    tiles = {(t["x"], t["y"]): t for t in state["tiles"]}
    edges = []
    # Ladder sides, the upper floor and the thick wall's lower left corner.
    for y in range(560, 960):
        for x in range(120, 801):
            here = tiles.get((x // 40, y // 40), {})
            for dx, dy in [(1, 0), (0, 1)]:
                other = tiles.get(((x+dx) // 40, (y+dy) // 40), {})
                if (here.get("opac", 0) >= 1) == (other.get("opac", 0) >= 1):
                    continue
                a, b = actual.getpixel((x, y)), actual.getpixel((x+dx, y+dy))
                na, nb = native.getpixel((x, y)), native.getpixel((x+dx, y+dy))
                excess = abs(b-a) - abs(nb-na)
                edges.append({"point": [x,y], "direction": [dx,dy], "brightness": [a,b],
                              "native": [na,nb], "excess": excess})
    edges.sort(key=lambda e: e["excess"], reverse=True)
    result = {"mode": mode, "position": name, "eye": state["eye"],
              "sample_count": len(edges), "max_excess": edges[0]["excess"],
              "over_12": sum(e["excess"] > 12 for e in edges), "worst": edges[:8]}
    measurements.append(result)
report = {"region": [120, 560, 800, 959], "threshold": 12, "measurements": measurements}
if not prefix:
    baseline = json.loads((root / "baseline-seams-data.json").read_text())
    assert data == baseline, "Lighting, geometry, FOV or memory differ; comparison is invalid."
    report["identical_inputs"] = True
    report["version_differences"] = []
    for state in data["states"]:
        name, mode = state["position"], state["mode"]
        filename = f"seams-{name}-{mode}-fog.png"
        a = Image.open(root / filename).convert("L")
        b = Image.open(root / f"baseline-{filename}").convert("L")
        diff = ImageChops.difference(a, b)
        wall_max = 0
        for t in state["tiles"]:
            if t["opac"] >= 1:
                x, y = t["x"] * 40, t["y"] * 40
                wall_max = max(wall_max, diff.crop((x,y,x+40,y+40)).getextrema()[1])
        changed = sum(diff.histogram()[1:])
        assert wall_max == 0, "The reference comparison unexpectedly changed wall interiors."
        if mode == "current":
            assert changed == 0, "Current mode changed despite this being a classic comparison."
        report["version_differences"].append({"mode":mode,"position":name,"changed_pixels":changed,
                                             "wall_max_delta":wall_max,"max_delta":diff.getextrema()[1]})
(root / f"{prefix}seam-measurements.json").write_text(json.dumps(report, indent=2)+"\n")
for s in measurements:
    print(f'{prefix}{s["mode"]} {s["position"]}: max excess {s["max_excess"]}, over 12 {s["over_12"]}/{s["sample_count"]}, worst {s["worst"][0]["point"]}')
if not prefix:
    print("Identical input; current fog and all wall interiors unchanged.")
