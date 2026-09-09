# OpenHI software-stage reproducibility proof

This project-owned sample runs one public OpenHI visualization stage against a
small deterministic event fixture. It records the exact repository revision,
script hash, environment, command, log, output image, checks, and scope
boundary.

## Build

Use a clean OpenHI checkout at the revision named in `artifacts/summary.json`:

```bash
python examples/openhi-reproducibility/build.py --openhi-root /path/to/OpenHI
python examples/openhi-reproducibility/build.py --openhi-root /path/to/OpenHI --check
python -m unittest tests.test_openhi_reproducibility_proof
```

The selected stage is `visualize_cumulative_weighted.py` with `--no_comp` and
the non-interactive Matplotlib `Agg` backend. It requires NumPy and Matplotlib;
it does not use a GPU, network access, camera SDK, raw acquisition file, or
learned compensation parameters.

## Boundary

This is workflow evidence, not a customer result or scientific validation. The
fixture is synthetic and does not represent a camera, optical system, specimen,
or measured spectrum. A successful plot verifies only the selected script's
public NPZ interface and execution path in the recorded environment. It does
not demonstrate acquisition, segmentation, compensation, calibration,
reconstruction accuracy, hardware compatibility, or paper-result reproduction.
