#!/usr/bin/env python3
"""Build a small project-owned KiCad plugin-evaluation fixture."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import uuid
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
BOARD = ROOT / "track-rounding-fixture.kicad_pcb"
PROJECT = ROOT / "track-rounding-fixture.kicad_pro"
DRC = ARTIFACTS / "drc.json"
SVG = ARTIFACTS / "track-rounding-fixture-top.svg"
PNG = ARTIFACTS / "track-rounding-fixture-top.png"
RENDER = ARTIFACTS / "track-rounding-fixture-3d.png"
MANIFEST = ARTIFACTS / "fixture-manifest.json"


CASES = [
    {
        "id": "C1",
        "net": "ORTHOGONAL_025",
        "width_mm": 0.25,
        "segments": [
            ("F.Cu", (27, 31), (39, 31)),
            ("F.Cu", (39, 31), (39, 36)),
            ("F.Cu", (39, 36), (58, 36)),
            ("F.Cu", (58, 36), (58, 31)),
            ("F.Cu", (58, 31), (73, 31)),
        ],
    },
    {
        "id": "C2",
        "net": "DOGLEG_045_025",
        "width_mm": 0.25,
        "segments": [
            ("F.Cu", (27, 44), (39, 44)),
            ("F.Cu", (39, 44), (46, 51)),
            ("F.Cu", (46, 51), (55, 51)),
            ("F.Cu", (55, 51), (62, 44)),
            ("F.Cu", (62, 44), (73, 44)),
        ],
    },
    {
        "id": "C3",
        "net": "MIXED_045_050",
        "width_mm": 0.50,
        "segments": [
            ("F.Cu", (27, 57), (38, 57)),
            ("F.Cu", (38, 57), (44, 63)),
            ("F.Cu", (44, 63), (50, 57)),
            ("F.Cu", (50, 57), (59, 57)),
            ("F.Cu", (59, 57), (64, 62)),
            ("F.Cu", (64, 62), (73, 62)),
        ],
    },
    {
        "id": "C4",
        "net": "SHORT_NOTCH_100",
        "width_mm": 1.00,
        "segments": [
            ("F.Cu", (27, 72), (41, 72)),
            ("F.Cu", (41, 72), (43, 74)),
            ("F.Cu", (43, 74), (45, 72)),
            ("F.Cu", (45, 72), (73, 72)),
        ],
    },
    {
        "id": "C5",
        "net": "VIA_TRANSITION_050",
        "width_mm": 0.50,
        "segments": [
            ("F.Cu", (27, 84), (39, 84)),
            ("F.Cu", (39, 84), (45, 90)),
            ("B.Cu", (45, 90), (52, 83)),
            ("B.Cu", (52, 83), (73, 83)),
        ],
        "via": (45, 90),
        "end_layer": "B.Cu",
    },
    {
        "id": "C6",
        "net": "CLEARANCE_A_025",
        "width_mm": 0.25,
        "segments": [
            ("F.Cu", (27, 96), (41, 96)),
            ("F.Cu", (41, 96), (47, 90)),
            ("F.Cu", (47, 90), (55, 90)),
            ("F.Cu", (55, 90), (61, 96)),
            ("F.Cu", (61, 96), (73, 96)),
        ],
    },
    {
        "id": "C7",
        "net": "CLEARANCE_B_025",
        "width_mm": 0.25,
        "segments": [
            ("F.Cu", (27, 100), (41, 100)),
            ("F.Cu", (41, 100), (47, 94)),
            ("F.Cu", (47, 94), (55, 94)),
            ("F.Cu", (55, 94), (61, 100)),
            ("F.Cu", (61, 100), (73, 100)),
        ],
    },
]


def stable_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"lazyingart:kicad-plugin-fixture:{name}"))


def pad(ref: str, net_id: int, net_name: str, point: tuple[float, float], layer: str) -> str:
    side = "F" if layer == "F.Cu" else "B"
    justify = " (justify mirror)" if side == "B" else ""
    return f"""
\t(footprint "TestPad_2mm"
\t\t(layer "{layer}")
\t\t(uuid "{stable_uuid(ref)}")
\t\t(at {point[0]:g} {point[1]:g})
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 -2 0)
\t\t\t(layer "{side}.SilkS")
\t\t\t(hide yes)
\t\t\t(uuid "{stable_uuid(ref + ':reference')}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)){justify})
\t\t)
\t\t(property "Value" "{net_name}"
\t\t\t(at 0 2 0)
\t\t\t(layer "{side}.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{stable_uuid(ref + ':value')}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)){justify})
\t\t)
\t\t(attr smd exclude_from_pos_files)
\t\t(fp_circle (center 0 0) (end 1.2 0) (stroke (width 0.12) (type solid)) (fill none) (layer "{side}.SilkS") (uuid "{stable_uuid(ref + ':silk')}"))
\t\t(fp_circle (center 0 0) (end 1.45 0) (stroke (width 0.05) (type solid)) (fill none) (layer "{side}.CrtYd") (uuid "{stable_uuid(ref + ':courtyard')}"))
\t\t(pad "1" smd circle (at 0 0) (size 2 2) (layers "{layer}" "{side}.Mask") (net {net_id} "{net_name}") (pinfunction "TEST") (pintype "passive") (uuid "{stable_uuid(ref + ':pad')}"))
\t)"""


def line(layer: str, start: tuple[float, float], end: tuple[float, float], name: str) -> str:
    return (
        f'\t(gr_line (start {start[0]:g} {start[1]:g}) '
        f'(end {end[0]:g} {end[1]:g}) (stroke (width 0.15) (type solid)) '
        f'(layer "{layer}") (uuid "{stable_uuid(name)}"))'
    )


def board_text() -> str:
    nets = ['\t(net 0 "")']
    footprints: list[str] = []
    copper: list[str] = []
    labels: list[str] = []

    for net_id, case in enumerate(CASES, start=1):
        nets.append(f'\t(net {net_id} "{case["net"]}")')
        first_layer, first, _ = case["segments"][0]
        _, _, last = case["segments"][-1]
        last_layer = case.get("end_layer", case["segments"][-1][0])
        footprints.append(pad(f'TP{net_id}A', net_id, case["net"], first, first_layer))
        footprints.append(pad(f'TP{net_id}B', net_id, case["net"], last, last_layer))
        for index, (layer, start, end) in enumerate(case["segments"], start=1):
            copper.append(
                f'\t(segment (start {start[0]:g} {start[1]:g}) '
                f'(end {end[0]:g} {end[1]:g}) (width {case["width_mm"]:g}) '
                f'(layer "{layer}") (net {net_id}) '
                f'(uuid "{stable_uuid(case["id"] + f":segment:{index}")}"))'
            )
        if case.get("via"):
            x, y = case["via"]
            copper.append(
                f'\t(via (at {x:g} {y:g}) (size 1) (drill 0.5) '
                f'(layers "F.Cu" "B.Cu") (net {net_id}) '
                f'(uuid "{stable_uuid(case["id"] + ":via")}"))'
            )
        label_x = 50
        label_y = first[1] - 3
        if case["id"] == "C6":
            label_x, label_y = 35, 88
        elif case["id"] == "C7":
            label_x, label_y = 64, 103
        labels.append(
            f'\t(gr_text "{case["id"]}  {case["net"]}" '
            f'(at {label_x:g} {label_y:g} 0) (layer "F.SilkS") '
            f'(uuid "{stable_uuid(case["id"] + ":label")}") '
            f'(effects (font (size 0.8 0.8) (thickness 0.12))))'
        )

    drawings = [
        line("Edge.Cuts", (20, 12), (80, 12), "edge:top"),
        line("Edge.Cuts", (80, 12), (80, 106), "edge:right"),
        line("Edge.Cuts", (80, 106), (20, 106), "edge:bottom"),
        line("Edge.Cuts", (20, 106), (20, 12), "edge:left"),
        f'\t(gr_text "KiCad track-rounding test fixture" (at 50 16.5 0) '
        f'(layer "F.SilkS") (uuid "{stable_uuid("title")}") '
        f'(effects (font (size 1.25 1.25) (thickness 0.18))))',
        *labels,
    ]

    return f"""(kicad_pcb
\t(version 20240108)
\t(generator "lazypromotion-kicad-plugin-fixture")
\t(generator_version "1.0")
\t(general (thickness 1.6) (legacy_teardrops no))
\t(paper "A4")
\t(title_block
\t\t(title "KiCad Track-Rounding Plugin Evaluation Fixture")
\t\t(date "2026-09-12")
\t\t(rev "1.0")
\t\t(company "LazyingArt LLC")
\t)
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(31 "B.Cu" signal)
\t\t(32 "B.Adhes" user "B.Adhesive")
\t\t(33 "F.Adhes" user "F.Adhesive")
\t\t(34 "B.Paste" user)
\t\t(35 "F.Paste" user)
\t\t(36 "B.SilkS" user "B.Silkscreen")
\t\t(37 "F.SilkS" user "F.Silkscreen")
\t\t(38 "B.Mask" user)
\t\t(39 "F.Mask" user)
\t\t(40 "Dwgs.User" user "User.Drawings")
\t\t(41 "Cmts.User" user "User.Comments")
\t\t(42 "Eco1.User" user "User.Eco1")
\t\t(43 "Eco2.User" user "User.Eco2")
\t\t(44 "Edge.Cuts" user)
\t\t(45 "Margin" user)
\t\t(46 "B.CrtYd" user "B.Courtyard")
\t\t(47 "F.CrtYd" user "F.Courtyard")
\t\t(48 "B.Fab" user)
\t\t(49 "F.Fab" user)
\t\t(50 "User.1" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0.05)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00010fc_ffffffff)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(outputformat 1)
\t\t\t(outputdirectory "artifacts/")
\t\t)
\t)
{chr(10).join(nets)}
{chr(10).join(footprints)}
{chr(10).join(drawings)}
{chr(10).join(copper)}
)"""


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def angle_bucket(start: tuple[float, float], end: tuple[float, float]) -> str:
    angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) % 180
    rounded = round(angle, 1)
    if rounded == 180:
        rounded = 0.0
    return f"{rounded:g}"


def main() -> int:
    for command in ("kicad-cli", "xvfb-run", "convert"):
        if not shutil.which(command):
            raise SystemExit(f"missing required command: {command}")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    BOARD.write_text(board_text() + "\n", encoding="utf-8")
    PROJECT.write_text("{}\n", encoding="utf-8")

    run(["kicad-cli", "pcb", "upgrade", str(BOARD)])
    run(
        [
            "kicad-cli",
            "pcb",
            "drc",
            "--format",
            "json",
            "--severity-all",
            "--exit-code-violations",
            "-o",
            str(DRC),
            str(BOARD),
        ]
    )
    run(
        [
            "kicad-cli",
            "pcb",
            "export",
            "svg",
            "--mode-single",
            "--layers",
            "F.Cu,B.Cu,F.SilkS,Edge.Cuts",
            "--page-size-mode",
            "2",
            "--exclude-drawing-sheet",
            "-o",
            str(SVG),
            str(BOARD),
        ]
    )
    raster_svg = ARTIFACTS / ".track-rounding-fixture-raster.svg"
    raster_svg.write_text(
        re.sub(
            r'<text\b[^>]*\bopacity="0"[^>]*>.*?</text>',
            "",
            SVG.read_text(encoding="utf-8"),
            flags=re.DOTALL,
        ),
        encoding="utf-8",
    )
    try:
        run(
            [
                "convert",
                "-density",
                "220",
                str(raster_svg),
                "-background",
                "white",
                "-alpha",
                "remove",
                "-resize",
                "1800x1800",
                str(PNG),
            ]
        )
    finally:
        raster_svg.unlink(missing_ok=True)
    run(
        [
            "xvfb-run",
            "-a",
            "kicad-cli",
            "pcb",
            "render",
            "--output",
            str(RENDER),
            "--width",
            "1800",
            "--height",
            "1200",
            "--background",
            "opaque",
            "--quality",
            "high",
            "--floor",
            "--perspective",
            "--rotate",
            "315,0,25",
            "--zoom",
            "1.2",
            str(BOARD),
        ]
    )

    drc = json.loads(DRC.read_text(encoding="utf-8"))
    angles = Counter()
    layers = Counter()
    widths = Counter()
    segment_count = 0
    for case in CASES:
        for layer, start, end in case["segments"]:
            segment_count += 1
            angles[angle_bucket(start, end)] += 1
            layers[layer] += 1
            widths[f'{case["width_mm"]:g}'] += 1
    manifest = {
        "version": 1,
        "fixture": BOARD.name,
        "kicad_version": subprocess.run(
            ["kicad-cli", "version"], text=True, capture_output=True, check=True
        ).stdout.strip(),
        "scope": "Project-owned baseline for evaluating track-geometry plugins; no third-party plugin result.",
        "cases": [
            {
                "id": case["id"],
                "net": case["net"],
                "width_mm": case["width_mm"],
                "layers": sorted({segment[0] for segment in case["segments"]}),
                "segment_count": len(case["segments"]),
                "via_count": int(bool(case.get("via"))),
            }
            for case in CASES
        ],
        "geometry": {
            "segment_count": segment_count,
            "via_count": sum(int(bool(case.get("via"))) for case in CASES),
            "angle_counts_degrees": dict(sorted(angles.items(), key=lambda item: float(item[0]))),
            "layer_segment_counts": dict(sorted(layers.items())),
            "width_segment_counts_mm": dict(sorted(widths.items(), key=lambda item: float(item[0]))),
        },
        "drc": {
            "violations": len(drc.get("violations") or []),
            "unconnected_items": len(drc.get("unconnected_items") or []),
        },
        "artifacts": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in (BOARD, DRC, SVG, PNG, RENDER)
        },
        "boundaries": [
            "The baseline does not include or evaluate a third-party plugin.",
            "A plugin result requires separate before/after files, screenshots, DRC, and settings evidence.",
            "Physical fabrication and electrical fitness are outside this software test fixture.",
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST), "drc": manifest["drc"], "geometry": manifest["geometry"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
