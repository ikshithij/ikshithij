#!/usr/bin/env python3
"""Rev ∞ board: generates assets/board.svg.

An illustration of a black circuit board. A light comes on behind it and the
text glows through clearances in the inner copper. CSS only, standard library
only, deterministic. Outlines come from scripts/glyphs.json (Inter Tight Medium,
SIL Open Font License 1.1).
"""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT = json.loads((ROOT / "scripts" / "glyphs.json").read_text())

W, H = 1200, 400
ROOM, BOARD, EDGE, LIGHT, SILK = "#070706", "#121210", "#23231F", "#FFD9A0", "#CFCBBE"
INSET = 26
LINES = ["This profile is the public tip", "of a fairly private iceberg."]
SIZE, LEADING, LEFT, FIRST = 66, 84, 92, 172
CYCLE = 11


def fmt(value):
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def text_path(text, x, y, size, tracking=-8):
    scale = size / FONT["upm"]
    parts = []
    for char in text:
        glyph = FONT["glyphs"][char]
        for op, *args in glyph["d"]:
            coords = [fmt(x + v * scale if n % 2 == 0 else y - v * scale) for n, v in enumerate(args)]
            parts.append(op + " ".join(coords))
        x += glyph["adv"] * scale + tracking * size / 1000
    return "".join(parts), x


def infinity(x, y, size):
    """Draw the lemniscate as a stroke, sat on the same baseline as the text."""
    a, mid = size * 0.46, y - size * 0.3
    points = []
    for n in range(49):
        t = math.tau * n / 48
        d = 1 + math.sin(t) ** 2
        points.append((x + a + a * math.cos(t) / d, mid + a * 1.15 * math.sin(t) * math.cos(t) / d))
    return "M" + "L".join(f"{fmt(px)} {fmt(py)}" for px, py in points) + "Z"


def vias():
    """Pinpricks of stitching vias along the board edge, where light also escapes."""
    rng = random.Random(9)
    marks = []
    for x in range(64, W - 60, 24):
        for y in (50, H - 50):
            if rng.random() < 0.62:
                marks.append(f"M{x} {y}h0")
    for y in range(74, H - 60, 24):
        for x in (50, W - 50):
            if rng.random() < 0.62:
                marks.append(f"M{x} {y}h0")
    return "".join(marks)


def compose():
    words = "".join(text_path(line, LEFT, FIRST + n * LEADING, SIZE)[0] for n, line in enumerate(LINES))
    mark, end = text_path("Rev ", W - 150, H - 58, 22, 0)
    style = (
        "@media (prefers-reduced-motion:no-preference){"
        "@keyframes b{0%,18%{opacity:0}40%,72%{opacity:1}94%,100%{opacity:0}}"
        f".l{{animation:b {CYCLE}s ease-in-out infinite}}"
        "}"
    )
    holes = "".join(
        f'<circle cx="{x}" cy="{y}" r="9" fill="{ROOM}"/>'
        for x in (INSET + 26, W - INSET - 26)
        for y in (INSET + 26, H - INSET - 26)
    )
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">',
        '<title id="t">Illustration of a black circuit board. Light behind it reveals: This profile is the public tip of a fairly private iceberg.</title>',
        f"<style>{style}</style>",
        '<defs><filter id="g" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="11"/></filter></defs>',
        f'<rect width="{W}" height="{H}" fill="{ROOM}"/>',
        f'<rect x="{INSET}" y="{INSET}" width="{W - 2 * INSET}" height="{H - 2 * INSET}" rx="8" fill="{BOARD}" stroke="{EDGE}"/>',
        holes,
        f'<path fill="{SILK}" d="{mark}"/>',
        f'<path fill="none" stroke="{SILK}" stroke-width="2.2" d="{infinity(end, H - 58, 22)}"/>',
        '<g class="l">',
        f'<path fill="#E8912D" opacity=".28" filter="url(#g)" d="{words}"/>',
        f'<path fill="{LIGHT}" d="{words}"/>',
        f'<path fill="none" stroke="{LIGHT}" stroke-width="2.4" stroke-linecap="round" d="{vias()}"/>',
        "</g>",
        "</svg>",
    ]) + "\n"


def main():
    (ROOT / "assets" / "board.svg").write_text(compose())


if __name__ == "__main__":
    main()
