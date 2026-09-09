# OpenHI software-stage sample report

## Decision

**GO for the selected visualization-only stage on the recorded environment.**
The public `visualize_cumulative_weighted.py` entry point accepted the frozen
synthetic NPZ interface, completed with exit code 0, and produced one readable
PNG. **NO-GO as evidence for the full OpenHI acquisition or reconstruction
pipeline.** Those paths require separate data, dependencies, parameters, and
scientific checks that this sample deliberately does not supply.

## What was tested

- Repository: `lachlanchen/OpenHI` at `080ad074a4581f34e3b87e6f23be64321eda5222`.
- Script SHA-256: `a4f4bf94143ce8031ec05d2299df1dfeae547c46196ac8e7fff38bfd07b50251`.
- Input: `4096` synthetic events on a
  `64 × 32` grid over
  `240000` microseconds.
- Command: `MPLBACKEND=Agg python <OPENHI_ROOT>/visualize_cumulative_weighted.py <WORK_DIR>/synthetic-events.npz --sensor_width 64 --sensor_height 32 --step_us 2000 --auto_scale --no_comp --ymin -0.05 --ymax 1.3`.
- Environment: Python 3.10.13, NumPy 2.2.6,
  Matplotlib 3.10.9, backend `Agg`, x86_64.
- Result: `120` time bins, auto-selected negative polarity
  scale `1.510`, one
  `1280 × 701` PNG.

The fixture, environment record, sanitized log, summary, output image, and
hash manifest are included beside this report.

## Failure ledger and boundary

1. The repository does not currently provide a locked root environment, so the
   exact interpreter and library versions had to be recorded.
2. The public checkout does not include the RAW acquisition named by the full
   wrapper, and some acquisition paths require external vendor SDKs. The
   end-to-end wrapper was not claimed or attempted.
3. `--no_comp` was used, so learned compensation parameters and compensated
   timing were not tested.
4. The script creates a timestamped output directory and calls `plt.show()`.
   `MPLBACKEND=Agg` made the run headless; the generated plot was then copied to
   the stable delivery name `weighted-cumulative.png`.
5. The checks establish file/interface execution, not whether a plot is a
   scientifically correct reconstruction of real measurements.

## Scope statement

Project-owned synthetic workflow evidence only: no client data, camera, optics, specimen, acquisition, calibration, compensation, reconstruction accuracy, hardware qualification, or paper-result reproduction, and no customer result.
