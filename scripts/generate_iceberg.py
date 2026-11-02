#!/usr/bin/env python3
"""Generates assets/iceberg.svg: an iceberg floating at its true proportion.

The waterline is solved so that 10% of the shape sits above it, then CSS rocks it
gently. Standard library only, deterministic. The playable version is index.html.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

W, H = 1200, 400
WATER = 104
SKY, SEA, BERG = "#0E1418", "#163240", "#EDF2F0"
SHAPE = [
    (440, 34), (486, 12), (538, 40), (594, 2), (648, 30), (702, 18), (774, 52), (856, 84),
    (936, 150), (884, 228), (790, 262), (742, 342), (650, 382), (560, 336), (466, 356),
    (372, 288), (290, 226), (316, 140), (372, 88),
]
ABOVE = 0.10


def shoelace(poly):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2


def above_line(poly, line):
    kept = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if a[1] <= line:
            kept.append(a)
        if (a[1] <= line) != (b[1] <= line):
            t = (line - a[1]) / (b[1] - a[1])
            kept.append((a[0] + (b[0] - a[0]) * t, line))
    return kept


def solve_line():
    low, high = min(y for _, y in SHAPE), max(y for _, y in SHAPE)
    total = shoelace(SHAPE)
    for _ in range(50):
        mid = (low + high) / 2
        if shoelace(above_line(SHAPE, mid)) / total < ABOVE:
            low = mid
        else:
            high = mid
    return low


def compose():
    shift = WATER - solve_line()
    points = " ".join(f"{x},{y + shift:.1f}" for x, y in SHAPE)
    style = (
        "@media (prefers-reduced-motion:no-preference){"
        "@keyframes r{0%,100%{transform:rotate(-2.2deg) translateY(-3px)}"
        "50%{transform:rotate(2.2deg) translateY(4px)}}"
        ".b{transform-box:fill-box;transform-origin:50% 45%;animation:r 9s ease-in-out infinite}"
        "}"
    )
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">',
        '<title id="t">An iceberg floating with one tenth of it above the water.</title>',
        f"<style>{style}</style>",
        f'<rect width="{W}" height="{H}" fill="{SKY}"/>',
        f'<rect y="{WATER}" width="{W}" height="{H - WATER}" fill="{SEA}"/>',
        f'<polygon class="b" fill="{BERG}" points="{points}"/>',
        f'<rect y="{WATER}" width="{W}" height="{H - WATER}" fill="{SEA}" opacity=".62"/>',
        "</svg>",
    ]) + "\n"


def main():
    (ROOT / "assets" / "iceberg.svg").write_text(compose())


if __name__ == "__main__":
    main()
