from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import Any


def _safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return value[:80] or "card"


def render_editorial_card(root: Path, signal: dict[str, Any], packet: dict[str, Any]) -> Path | None:
    if str(packet.get("image_mode") or "NONE").upper() != "EDITORIAL_CARD":
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:
        raise RuntimeError(f"pillow_unavailable:{exc}") from exc

    title = str(packet.get("image_title") or signal.get("title") or "China Tech")[:90]
    points = [str(x).strip() for x in (packet.get("image_points") or []) if str(x).strip()][:3]
    if len(points) < 2:
        return None

    width, height = 1200, 675
    img = Image.new("RGB", (width, height), (246, 247, 249))
    draw = ImageDraw.Draw(img)
    font_paths = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    font_path = next((p for p in font_paths if Path(p).exists()), None)
    if not font_path:
        raise RuntimeError("no_system_font_found")
    title_font = ImageFont.truetype(font_path, 58)
    point_font = ImageFont.truetype(font_path, 36)
    small_font = ImageFont.truetype(font_path, 25)
    brand_font = ImageFont.truetype(font_path, 28)

    # Editorial card: clean, high-contrast, source-attributed, no copied photography.
    draw.rounded_rectangle((54, 48, 1146, 627), radius=28, fill=(255, 255, 255), outline=(224, 227, 232), width=2)
    draw.text((92, 80), "CHINA TECH", font=brand_font, fill=(45, 55, 72))
    y = 135
    wrapped = textwrap.wrap(title, width=31)[:2]
    for line in wrapped:
        draw.text((92, y), line, font=title_font, fill=(15, 20, 28))
        y += 72
    y += 18
    for point in points:
        draw.ellipse((95, y + 14, 111, y + 30), fill=(46, 93, 255))
        lines = textwrap.wrap(point, width=46)[:2]
        for j, line in enumerate(lines):
            draw.text((132, y + j * 45), line, font=point_font, fill=(34, 39, 48))
        y += max(60, len(lines) * 45 + 20)
    source = str(packet.get("source_url") or signal.get("source_name") or "")
    source_label = signal.get("source_name") or "Source"
    draw.text((92, 574), f"Source: {source_label}", font=small_font, fill=(100, 107, 120))
    draw.text((915, 574), "@KennyChinaTech", font=small_font, fill=(72, 78, 90))

    out_dir = root / "runtime" / "editorial-assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"signal-{signal.get('id')}-{_safe_name(title)}.png"
    img.save(out, format="PNG", optimize=True)
    return out
