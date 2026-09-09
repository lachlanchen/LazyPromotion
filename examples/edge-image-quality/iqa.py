"""Small, interpretable image-quality baseline for CPU-side screening.

This module is deliberately not a medical or diagnostic classifier.  It exposes
simple measurements that can be calibrated against a buyer's labelled images.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class Thresholds:
    min_laplacian_variance: float = 80.0
    min_mean_luminance: float = 55.0
    max_mean_luminance: float = 200.0
    max_dark_fraction: float = 0.45
    max_bright_fraction: float = 0.45
    max_glare_fraction: float = 0.08


def _validate_image(image: np.ndarray) -> None:
    if not isinstance(image, np.ndarray):
        raise TypeError("image must be a NumPy array")
    if image.dtype != np.uint8:
        raise ValueError("image must use uint8 pixels")
    if image.ndim not in (2, 3):
        raise ValueError("image must be grayscale or BGR")
    if image.ndim == 3 and image.shape[2] != 3:
        raise ValueError("colour images must have exactly three BGR channels")
    if min(image.shape[:2]) < 32:
        raise ValueError("image must be at least 32 by 32 pixels")


def assess(image: np.ndarray, thresholds: Thresholds | None = None) -> dict[str, Any]:
    """Return interpretable quality metrics and a deterministic PASS/FAIL result."""

    _validate_image(image)
    thresholds = thresholds or Thresholds()
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.ndim == 2:
        saturation = np.zeros_like(gray)
        value = gray
    else:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        value = hsv[:, :, 2]

    metrics = {
        "laplacian_variance": round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 4),
        "mean_luminance": round(float(gray.mean()), 4),
        "dark_fraction": round(float(np.mean(gray <= 12)), 6),
        "bright_fraction": round(float(np.mean(gray >= 243)), 6),
        "glare_fraction": round(
            float(np.mean((value >= 245) & (saturation <= 32))), 6
        ),
    }

    reasons: list[str] = []
    if metrics["laplacian_variance"] < thresholds.min_laplacian_variance:
        reasons.append("blur_or_low_detail")
    if (
        metrics["mean_luminance"] < thresholds.min_mean_luminance
        or metrics["dark_fraction"] > thresholds.max_dark_fraction
    ):
        reasons.append("underexposed")
    if (
        metrics["mean_luminance"] > thresholds.max_mean_luminance
        or metrics["bright_fraction"] > thresholds.max_bright_fraction
    ):
        reasons.append("overexposed")
    if metrics["glare_fraction"] > thresholds.max_glare_fraction:
        reasons.append("possible_glare")

    return {
        "status": "FAIL" if reasons else "PASS",
        "reasons": reasons,
        "metrics": metrics,
        "thresholds": asdict(thresholds),
        "image": {
            "width": int(image.shape[1]),
            "height": int(image.shape[0]),
            "channels": 1 if image.ndim == 2 else int(image.shape[2]),
        },
        "scope": "screening baseline; thresholds require labelled-domain calibration",
    }


def assess_encoded(payload: bytes, thresholds: Thresholds | None = None) -> dict[str, Any]:
    if not payload:
        raise ValueError("image payload is empty")
    image = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("payload is not a decodable image")
    return assess(image, thresholds)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    image = cv2.imread(str(args.image), cv2.IMREAD_COLOR)
    if image is None:
        parser.error(f"could not decode {args.image}")
    rendered = json.dumps(assess(image), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
