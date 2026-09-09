# Edge image-quality baseline report

## Result

The small CPU baseline classified the five project-owned fixtures as expected: one reference passed, while blur, underexposure, overexposure, and a large low-saturation highlight each produced an explicit reason code. On this workstation the 640×400 reference took a median of **2.8428 ms** across 250 measured iterations; this is a local benchmark, not a deployment promise.

## What is inspectable

- deterministic synthetic fixtures and their individual JSON results;
- Laplacian detail, mean luminance, dark/bright clipping, and possible-glare measurements;
- explicit thresholds, reason codes, input validation, and a raw-image FastAPI boundary;
- a CPU-only Docker recipe and hashes for every source and output in this packet.

## Boundary

This is engineering-process evidence, not a customer result, medical-device validation, diagnostic software, or proof of accuracy on clinical images. The fixed thresholds are illustrative. A real milestone must calibrate them on rights-cleared, representative labelled data and keep a held-out evaluation set. Incorrect-view detection is intentionally absent until the buyer defines views and supplies representative examples; pretending that one generic heuristic solves it would be misleading.
