"""Measure unedited Chrome review captures; this is not a photometric calibration."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "reports/lighting-v2"
# Screenshot pixels, excluding the browser UI, location badge and touch buttons.
ROI = (0, 142, 533, 340)


def measure(name):
    path = REVIEW / name
    with Image.open(path) as image:
        if image.size != (549, 668):
            raise ValueError(f"Re-check the measured video region for {name}")
        x0, y0, x1, y1 = ROI
        pixels = np.asarray(image.convert("RGB"))[y0:y1, x0:x1]
    return {
        "image": name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "nearWhitePercent": round(float(np.all(pixels >= 250, axis=2).mean() * 100), 3),
        "medianRgb": np.median(pixels, axis=(0, 1)).tolist(),
    }


def main():
    report = {
        "comparison": "Pool terrace, 2026-09-08 11:00 America/New_York",
        "utc": 1788879600,
        "sunElevationDegrees": 46.134,
        "sunAzimuthDegrees": 131.417,
        "estimatedDirectNormalLux": 90585.633,
        "exposureCompensationStops": -0.5,
        "nativeView": {"xCm": -80, "yCm": -1700, "zCm": -71.85, "yawDegrees": -160},
        "settings": {"gpu": "RTX 2060", "output": [768, 432], "screenPercentage": 50},
        "roiPixelsXYXY": ROI,
        "nearWhiteDefinition": "All three decoded 8-bit RGB channels >= 250",
        "before": measure("before-pool-11am.png"),
        "after": measure("after-pool-11am.png"),
        "scope": "One matched pool view. Measures displayed clipping, not lux, color accuracy or every possible viewpoint. Indoor comparison has slightly different yaw and is qualitative only.",
    }
    (REVIEW / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
