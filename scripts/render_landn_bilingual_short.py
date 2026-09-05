#!/usr/bin/env python3
"""Render a first-party L-and-N bilingual vertical portfolio short."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


WIDTH = 1080
HEIGHT = 1920
FPS = 30
FONT_REGULAR = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
FONT_BOLD = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

NAVY = "#06245A"
NAVY_DARK = "#031A43"
CREAM = "#F7F5EE"
INK = "#072557"
MUTED = "#6E7F99"
CORAL = "#FF6D5F"
TEAL = "#12B8AA"
WHITE = "#FFFFFF"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", required=True, type=Path)
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def require_inputs(app_root: Path) -> dict[str, Path]:
    paths = {
        "icon": app_root / "assets" / "icon.png",
        "practice": app_root / "docs" / "images" / "pwa-practice.png",
        "mouth_l": app_root / "docs" / "images" / "pwa-mouth-model.png",
        "mouth_n": app_root / "docs" / "images" / "pwa-mouth-model-n.png",
        "score": app_root / "docs" / "images" / "android-score-current.png",
        "light_audio": app_root / "public" / "audio" / "models" / "en-light.mp3",
        "night_audio": app_root / "public" / "audio" / "models" / "en-night.mp3",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise SystemExit(f"required L-and-N input is missing: {', '.join(missing)}")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required")
    for font in (FONT_REGULAR, FONT_BOLD):
        if not font.is_file():
            raise SystemExit(f"required font is missing: {font}")
    return paths


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_width(draw, text: str, font) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def center(draw, text: str, y: int, font, fill: str) -> None:
    draw.text((WIDTH // 2, y), text, font=font, fill=fill, anchor="mm")


def cover(Image, source: Path, size: tuple[int, int], radius: int):
    from PIL import ImageOps

    image = Image.open(source).convert("RGB")
    fitted = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)
    mask = Image.new("L", size, 0)
    from PIL import ImageDraw

    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *size), radius=radius, fill=255)
    fitted.putalpha(mask)
    return fitted


def contain(Image, source: Path, size: tuple[int, int], radius: int):
    from PIL import ImageOps

    image = Image.open(source).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, CREAM)
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    mask = Image.new("L", size, 0)
    from PIL import ImageDraw

    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *size), radius=radius, fill=255)
    canvas.putalpha(mask)
    return canvas


def base_slide(Image, ImageDraw, ImageFont, icon_path: Path, index: int):
    image = Image.new("RGB", (WIDTH, HEIGHT), CREAM)
    draw = ImageDraw.Draw(image)
    draw.ellipse((-260, -180, 520, 600), fill="#FFE6DE")
    draw.ellipse((700, -130, 1260, 430), fill="#DDF8F4")
    draw.rounded_rectangle((48, 44, 1032, 184), radius=58, fill=WHITE)
    icon = Image.open(icon_path).convert("RGB").resize((96, 96), Image.Resampling.LANCZOS)
    mask = Image.new("L", icon.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 96, 96), radius=22, fill=255)
    image.paste(icon, (78, 66), mask)
    brand = ImageFont.truetype(str(FONT_BOLD), 46)
    label = ImageFont.truetype(str(FONT_REGULAR), 30)
    draw.text((198, 82), "L-and-N", font=brand, fill=INK)
    draw.text((198, 137), "by LazyingArt", font=label, fill=MUTED)
    for dot in range(5):
        x = 390 + dot * 68
        color = CORAL if dot == index else "#D4D9E0"
        draw.ellipse((x, 1810, x + 20, 1830), fill=color)
    draw.text(
        (WIDTH // 2, 1870),
        "first-party app and audio",
        font=label,
        fill=MUTED,
        anchor="mm",
    )
    return image, draw


def render_slides(workdir: Path, inputs: dict[str, Path]) -> list[Path]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Pillow is required: python -m pip install Pillow") from exc

    workdir.mkdir(parents=True, exist_ok=True)
    hero = ImageFont.truetype(str(FONT_BOLD), 116)
    heading = ImageFont.truetype(str(FONT_BOLD), 64)
    chinese = ImageFont.truetype(str(FONT_BOLD), 47)
    body = ImageFont.truetype(str(FONT_REGULAR), 39)
    small = ImageFont.truetype(str(FONT_REGULAR), 31)
    paths: list[Path] = []

    image, draw = base_slide(Image, ImageDraw, ImageFont, inputs["icon"], 0)
    draw.text((255, 410), "L", font=hero, fill=CORAL, anchor="mm")
    draw.text((540, 410), "or", font=body, fill=MUTED, anchor="mm")
    draw.text((825, 410), "N", font=hero, fill=TEAL, anchor="mm")
    center(draw, "Hear the difference.", 670, heading, INK)
    center(draw, "L 和 N，總是聽起來很像嗎？", 790, chinese, INK)
    draw.rounded_rectangle((132, 980, 948, 1120), radius=62, fill=NAVY)
    center(draw, "20 English words · 普通話 · 廣東話", 1050, body, WHITE)
    center(draw, "A focused four-minute drill", 1280, body, MUTED)
    path = workdir / "01-hook.png"
    image.save(path)
    paths.append(path)

    image, draw = base_slide(Image, ImageDraw, ImageFont, inputs["icon"], 1)
    center(draw, "Listen before you record.", 285, heading, INK)
    center(draw, "先聽，再錄。", 380, chinese, TEAL)
    screen = contain(Image, inputs["practice"], (610, 1100), 44)
    image.paste(screen, (235, 470), screen)
    draw.rounded_rectangle((275, 1600, 805, 1710), radius=46, fill=NAVY)
    center(draw, "light   ↔   night", 1655, heading, WHITE)
    path = workdir / "02-listen.png"
    image.save(path)
    paths.append(path)

    image, draw = base_slide(Image, ImageDraw, ImageFont, inputs["icon"], 2)
    center(draw, "Same place. Different pathway.", 280, heading, INK)
    center(draw, "舌位相近，氣流不同。", 380, chinese, TEAL)
    mouth_l = cover(Image, inputs["mouth_l"], (440, 1040), 44)
    mouth_n = cover(Image, inputs["mouth_n"], (440, 1040), 44)
    image.paste(mouth_l, (70, 505), mouth_l)
    image.paste(mouth_n, (570, 505), mouth_n)
    draw.rounded_rectangle((160, 1490, 420, 1590), radius=42, fill=CORAL)
    draw.rounded_rectangle((660, 1490, 920, 1590), radius=42, fill=TEAL)
    draw.text((290, 1540), "L · side airflow", font=small, fill=WHITE, anchor="mm")
    draw.text((790, 1540), "N · nasal airflow", font=small, fill=WHITE, anchor="mm")
    path = workdir / "03-mouth.png"
    image.save(path)
    paths.append(path)

    image, draw = base_slide(Image, ImageDraw, ImageFont, inputs["icon"], 3)
    center(draw, "See the evidence.", 285, heading, INK)
    center(draw, "不只給分數，也說明依據。", 380, chinese, TEAL)
    score = cover(Image, inputs["score"], (610, 1110), 48)
    image.paste(score, (235, 475), score)
    for x, text in ((220, "signal"), (540, "contrast"), (860, "confidence")):
        draw.ellipse((x - 10, 1640, x + 10, 1660), fill=CORAL if x == 220 else TEAL)
        draw.text((x, 1700), text, font=small, fill=INK, anchor="mm")
    path = workdir / "04-score.png"
    image.save(path)
    paths.append(path)

    image, draw = base_slide(Image, ImageDraw, ImageFont, inputs["icon"], 4)
    icon = Image.open(inputs["icon"]).convert("RGB").resize((260, 260), Image.Resampling.LANCZOS)
    icon_mask = Image.new("L", icon.size, 0)
    ImageDraw.Draw(icon_mask).rounded_rectangle((0, 0, 260, 260), radius=62, fill=255)
    image.paste(icon, (410, 330), icon_mask)
    center(draw, "A four-minute sound drill.", 760, heading, INK)
    center(draw, "四分鐘，專心練一組聲音。", 875, chinese, INK)
    draw.rounded_rectangle((120, 1060, 960, 1218), radius=62, fill=NAVY)
    center(draw, "Free in your browser · 免費網頁練習", 1138, body, WHITE)
    center(draw, "l-and-n.lazying.art", 1360, heading, TEAL)
    center(draw, "English · 普通話 · 廣東話", 1500, body, MUTED)
    path = workdir / "05-cta.png"
    image.save(path)
    paths.append(path)
    return paths


def render_video(slides: list[Path], inputs: dict[str, Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-y"]
    for slide in slides:
        command.extend(["-loop", "1", "-t", "4.7", "-i", str(slide)])
    command.extend(["-f", "lavfi", "-t", "20", "-i", "anullsrc=r=48000:cl=stereo"])
    command.extend(["-i", str(inputs["light_audio"]), "-i", str(inputs["night_audio"])])
    filters = [f"[{index}:v]fps={FPS},format=yuv420p[v{index}]" for index in range(5)]
    filters.extend(
        [
            "[v0][v1]xfade=transition=fade:duration=0.55:offset=3.8[x1]",
            "[x1][v2]xfade=transition=fade:duration=0.55:offset=7.6[x2]",
            "[x2][v3]xfade=transition=fade:duration=0.55:offset=11.4[x3]",
            "[x3][v4]xfade=transition=fade:duration=0.55:offset=15.2[vout]",
            "[6:a]atrim=0:2.55,volume=1.1,pan=stereo|c0=c0|c1=c0,adelay=4100|4100[light]",
            "[7:a]atrim=0:2.85,volume=1.1,pan=stereo|c0=c0|c1=c0,adelay=6900|6900[night]",
            "[5:a][light][night]amix=inputs=3:duration=first:dropout_transition=0[aout]",
        ]
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-t",
            "19.35",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    subprocess.run(command, check=True)


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate:format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    args = parse_args()
    inputs = require_inputs(args.app_root.resolve())
    slides = render_slides(args.workdir.resolve(), inputs)
    render_video(slides, inputs, args.output.resolve())
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(args.output.resolve()),
                "sha256": sha256(args.output.resolve()),
                "probe": probe(args.output.resolve()),
                "inputs": {name: sha256(path) for name, path in inputs.items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
