#!/usr/bin/env python3
"""Render a rights-safe, typography-only Bilingual Lecture Pack short."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


WIDTH = 1080
HEIGHT = 1920
FPS = 30
FONT_REGULAR = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
FONT_BOLD = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")

INK = "#F7F4EC"
MUTED = "#B8C0D4"
VIOLET = "#8B5CF6"
CYAN = "#49D3C4"
PANEL = "#171A2B"
BACKGROUND = "#0C0E18"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", required=True, type=Path)
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def load_example(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entry = next(
        item for item in payload["entries"]
        if item["start"] == "00:00:05.000"
    )
    return {
        "timestamp": "00:05.000 → 00:06.720",
        "ja": entry["tracks"]["ja"]["text"],
        "en": entry["tracks"]["en"]["text"],
        "zh": entry["tracks"]["zh"]["text"],
    }


def require_tools() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required")
    for font in (FONT_REGULAR, FONT_BOLD):
        if not font.is_file():
            raise SystemExit(f"required font is missing: {font}")


def wrap(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if len(words) == 1 and any(ord(char) > 127 for char in text):
        words = list(text)
        separator = ""
    else:
        separator = " "
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else current + separator + word
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def centered_lines(draw, lines: list[str], font, y: int, fill: str, spacing: int) -> int:
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += (box[3] - box[1]) + spacing
    return y


def base_slide(Image, ImageDraw, ImageFont, index: int):
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    brand = ImageFont.truetype(str(FONT_BOLD), 34)
    small = ImageFont.truetype(str(FONT_REGULAR), 28)
    draw.rounded_rectangle((72, 72, 520, 172), radius=48, fill=PANEL)
    draw.text((112, 101), "LAZYINGART", font=brand, fill=INK)
    draw.text((112, 218), "Bilingual Lecture Pack", font=small, fill=VIOLET)
    for dot in range(5):
        x = 414 + dot * 64
        color = VIOLET if dot == index else "#30364D"
        draw.ellipse((x, 1770, x + 18, 1788), fill=color)
    draw.text(
        (WIDTH // 2, 1830),
        "project-made workflow proof",
        font=small,
        fill=MUTED,
        anchor="mm",
    )
    return image, draw


def render_slides(workdir: Path, example: dict[str, str]) -> list[Path]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise SystemExit("Pillow is required: python -m pip install Pillow") from exc

    workdir.mkdir(parents=True, exist_ok=True)
    bold = ImageFont.truetype(str(FONT_BOLD), 86)
    heading = ImageFont.truetype(str(FONT_BOLD), 66)
    body = ImageFont.truetype(str(FONT_REGULAR), 44)
    mono = ImageFont.truetype(str(FONT_BOLD), 48)
    small = ImageFont.truetype(str(FONT_REGULAR), 34)
    paths: list[Path] = []

    image, draw = base_slide(Image, ImageDraw, ImageFont, 0)
    centered_lines(draw, ["A lecture becomes", "reusable when every line", "is tied to time."], bold, 550, INK, 38)
    draw.text((WIDTH // 2, 1050), "transcript · subtitles · pocket PDF", font=body, fill=CYAN, anchor="mm")
    paths.append(workdir / "01-hook.png")
    image.save(paths[-1])

    image, draw = base_slide(Image, ImageDraw, ImageFont, 1)
    draw.text((96, 310), example["timestamp"], font=mono, fill=CYAN)
    y = 450
    for label, key in (("日本語", "ja"), ("English", "en"), ("中文", "zh")):
        draw.rounded_rectangle((72, y, 1008, y + 330), radius=34, fill=PANEL)
        draw.text((112, y + 46), label, font=small, fill=VIOLET)
        lines = wrap(draw, example[key], body, 820)
        centered_lines(draw, lines, body, y + 122, INK, 18)
        y += 372
    paths.append(workdir / "02-alignment.png")
    image.save(paths[-1])

    image, draw = base_slide(Image, ImageDraw, ImageFont, 2)
    centered_lines(draw, ["Search a word.", "Jump to the exact second."], heading, 470, INK, 38)
    draw.rounded_rectangle((112, 910, 968, 1122), radius=38, fill=PANEL)
    draw.text((160, 960), "microenvironment", font=body, fill=INK)
    draw.text((748, 960), "→ 00:05.000", font=small, fill=CYAN)
    draw.text((WIDTH // 2, 1280), "Every result stays connected to its timed source line.", font=small, fill=MUTED, anchor="mm")
    paths.append(workdir / "03-search.png")
    image.save(paths[-1])

    image, draw = base_slide(Image, ImageDraw, ImageFont, 3)
    centered_lines(draw, ["One source.", "Four useful outputs."], heading, 300, INK, 20)
    items = [
        "Corrected timestamped transcript",
        "English + target-language SRT",
        "Editable bilingual source + A5 PDF",
        "Source and rights manifest",
    ]
    y = 620
    for item in items:
        draw.ellipse((104, y + 9, 132, y + 37), fill=CYAN)
        draw.text((172, y), item, font=body, fill=INK)
        y += 190
    paths.append(workdir / "04-deliverables.png")
    image.save(paths[-1])

    image, draw = base_slide(Image, ImageDraw, ImageFont, 4)
    centered_lines(draw, ["One rights-cleared", "English lecture"], heading, 400, INK, 38)
    draw.text((WIDTH // 2, 790), "up to 20 minutes", font=body, fill=MUTED, anchor="mm")
    draw.text((WIDTH // 2, 990), "USD 250", font=bold, fill=CYAN, anchor="mm")
    draw.rounded_rectangle((96, 1210, 984, 1358), radius=52, fill=VIOLET)
    draw.text((WIDTH // 2, 1284), "lazying.art/lecture-pack", font=body, fill="#FFFFFF", anchor="mm")
    draw.text((WIDTH // 2, 1470), "See the working proof before the fit check.", font=small, fill=MUTED, anchor="mm")
    paths.append(workdir / "05-offer.png")
    image.save(paths[-1])
    return paths


def render_video(slides: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-y"]
    for slide in slides:
        command.extend(["-loop", "1", "-t", "5.5", "-i", str(slide)])
    command.extend(["-f", "lavfi", "-t", "25", "-i", "anullsrc=r=48000:cl=stereo"])
    filters = []
    for index in range(5):
        filters.append(f"[{index}:v]fps={FPS},format=yuv420p[v{index}]")
    filters.extend([
        "[v0][v1]xfade=transition=fade:duration=0.5:offset=4.5[x1]",
        "[x1][v2]xfade=transition=fade:duration=0.5:offset=9.0[x2]",
        "[x2][v3]xfade=transition=fade:duration=0.5:offset=13.5[x3]",
        "[x3][v4]xfade=transition=fade:duration=0.5:offset=18.0[vout]",
    ])
    command.extend([
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "5:a",
        "-t", "23", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", str(output),
    ])
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    require_tools()
    example = load_example(args.transcript)
    slides = render_slides(args.workdir, example)
    render_video(slides, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
