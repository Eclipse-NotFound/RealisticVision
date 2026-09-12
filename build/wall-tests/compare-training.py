"""Compare captured AIR fog pixels, excluding scene animation; never synthesize images."""
import json
from pathlib import Path
from PIL import Image, ImageChops

mod = Path(__file__).resolve().parents[2]
root = mod / "build/wall-test-output/game"
baseline = json.loads((root / "baseline-training-data.json").read_text())
candidate = json.loads((root / "training-data.json").read_text())
assert baseline == candidate, "Training input differs; captures cannot establish a rendering regression."
stats = {"identical_training_input": True}
for mode in ["current", "classic"]:
    old = Image.open(root / f"baseline-training-{mode}-fog.png").convert("L")
    new = Image.open(root / f"training-{mode}-fog.png").convert("L")
    diff = ImageChops.difference(old, new)
    histogram = diff.histogram()
    changed = sum(histogram[1:])
    wall_diff = 0
    for tile in candidate["tiles"]:
        if tile["opac"] < 1:
            continue
        x, y = tile["x"] * 40, tile["y"] * 40
        wall_diff = max(wall_diff, diff.crop((x, y, x + 40, y + 40)).getextrema()[1])
    stats[mode] = {"changed_pixels": changed, "max_delta": diff.getextrema()[1], "wall_max_delta": wall_diff}
    assert wall_diff == 0, f"{mode} wall interior changed"
    if mode == "current":
        assert changed == 0, "Current mode fog changed"
    else:
        # Vertical profile across the lit right side of the protruding block.
        stats[mode]["right_side_y440"] = [
            {"x": x, "old": old.getpixel((x, 440)), "new": new.getpixel((x, 440))}
            for x in [960, 965, 970, 975, 980, 985, 1000]
        ]
        stats[mode]["corner_y399_half_shadow_rightmost"] = {
            name: max(x for x in range(860, 1020) if image.getpixel((x, 399)) <= 127)
            for name, image in [("old", old), ("new", new)]
        }
text = json.dumps(stats, ensure_ascii=False, indent=2) + "\n"
(root / "training-comparison.json").write_text(text, encoding="utf-8")
print(text)
