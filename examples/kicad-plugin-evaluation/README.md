# KiCad track-rounding plugin evaluation fixture

This project-owned board is a small, reproducible fixture for evaluating a
KiCad track-geometry plugin. It deliberately contains orthogonal, 45-degree,
short-leg, mixed-width, close-clearance, and two-layer/via cases. The baseline
must be clean before a plugin is applied so new DRC findings can be attributed
to the transformation rather than to the fixture.

The fixture is evidence of a testing method, not a result for any third-party
plugin. No proprietary plugin, buyer board, or customer data is included.

## Test contract

For each supported plugin setting:

1. Start from a fresh copy of the baseline board.
2. Record KiCad, operating-system, and plugin versions.
3. Capture the selected tracks and setting values before execution.
4. Apply the plugin once and save a distinct result file.
5. Capture the same viewport after execution.
6. Run KiCad DRC and compare segment count, width, layer, net, and endpoint
   continuity with the baseline.
7. Record changed geometry, no-op cases, warnings, failures, undo behavior,
   and a minimal reproduction for every anomaly.

| Case | Geometry | Width | Layer | Main question |
|---|---|---:|---|---|
| C1 | four 90-degree corners | 0.25 mm | F.Cu | Are sharp orthogonal turns rounded consistently? |
| C2 | symmetric 45-degree dogleg | 0.25 mm | F.Cu | Are both entry and exit transitions preserved? |
| C3 | mixed 45-degree turns | 0.50 mm | F.Cu | Does radius handling scale with track width? |
| C4 | short 45-degree notch | 1.00 mm | F.Cu | Is an infeasible radius rejected or clamped clearly? |
| C5 | via and layer transition | 0.50 mm | F.Cu/B.Cu | Are vias, nets, and layer boundaries preserved? |
| C6/C7 | neighboring doglegs | 0.25 mm | F.Cu | Does rounding retain the baseline clearance? |

## Reproduce the baseline

Requires KiCad 10 and ImageMagick:

```bash
python examples/kicad-plugin-evaluation/build.py
```

The build regenerates the board, runs native KiCad DRC, exports a top-layout
SVG and PNG, renders a 3D overview, and writes a machine-readable manifest.
The committed baseline reports zero DRC violations and zero unconnected items.

The larger public
[HybridImager V2 board](https://github.com/lachlanchen/HybridImager/tree/master/hardware/v2-als-pt19-32x32)
provides a separate real-project example with 1,033 footprints, 2,144 track
segments, 1,024 vias, Gerbers, STEP, renders, and clean KiCad DRC. The
[digiOBSCURA image-sensor board](https://github.com/lachlanchen/CustomSensor/tree/main/PCB/image_sensor)
provides a real routed board with 45-degree traces.

