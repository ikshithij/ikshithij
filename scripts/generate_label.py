#!/usr/bin/env python3
"""IIJ / The Living Label: generates assets/living-label.svg.

Standard library only. Output is fully deterministic: the same values always
produce byte-identical SVG, so a scheduled job commits only on real change.

    python scripts/generate_label.py
    python scripts/generate_label.py --values weekly_counts.json
    python scripts/generate_label.py --empty

All type is converted to outlines because an SVG shown through <img> cannot load
fonts. Outlines come from scripts/glyphs.json: Inter Tight SemiBold and IBM Plex
Mono Medium, both SIL Open Font License 1.1.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLYPHS = json.loads((ROOT / "scripts" / "glyphs.json").read_text())

W, H = 1200, 400
PORCELAIN, CHARCOAL, GRAPHITE, VERMILION = "#F5F2EA", "#222220", "#676761", "#C9473B"

# Layout grid. Wordmark and text share the top and bottom lines.
TOP, BOTTOM = 36, 364
MARK_X = 36
TEXT_X = 304
WEAVE_X = 716

# Static artwork input for version one. This is a composition, not a record of
# activity: nothing here is real GitHub data and the banner does not claim it is.
DESIGN_STUDY = [
    0, 0, 1, 3, 1, 0, 0, 2, 6, 9, 7, 3, 1, 0, 0, 0, 1, 2, 2, 5, 12, 14, 9, 4, 2, 1,
    0, 0, 3, 7, 5, 2, 0, 0, 1, 4, 10, 16, 11, 5, 2, 1, 1, 0, 0, 2, 4, 3, 1, 0, 0, 1,
]

HEADLINE = ["I MAKE", "THINGS", "THAT DO", "THINGS."]
SUPPORT = "ELECTRONICS / SOFTWARE / PHYSICAL OBJECTS"
META_TOP = "IIJ / PERSONAL ARCHIVE"
META_FOOT = "EDITION 001 — 2026"

# Optical kerning for the headline, in thousandths of the type size.
KERN = {"AK": -8, "MA": -6, "AT": -60, "TH": -8, "TS": -8, "DO": -8, "HA": -6, "KE": -10}


def fmt(value, places=1):
    text = f"{value:.{places}f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


# --- Type ---------------------------------------------------------------------

def text_width(text, face, size, tracking=0):
    font = GLYPHS[face]
    scale = size / font["upm"]
    width = sum(font["glyphs"][c]["adv"] * scale + tracking * size / 1000 for c in text)
    kerns = sum(KERN.get(a + b, 0) * size / 1000 for a, b in zip(text, text[1:]))
    return width + kerns - tracking * size / 1000


def text_path(text, x, y, face, size, tracking=0, places=2):
    """Return outlined text as path data, with x at the left edge and y the baseline."""
    font = GLYPHS[face]
    scale = size / font["upm"]
    parts = []
    for index, char in enumerate(text):
        glyph = font["glyphs"][char]
        for op, *args in glyph["d"]:
            coords = [
                fmt(x + v * scale if n % 2 == 0 else y - v * scale, places)
                for n, v in enumerate(args)
            ]
            parts.append(op + " ".join(coords))
        x += glyph["adv"] * scale + tracking * size / 1000
        x += KERN.get(text[index:index + 2], 0) * size / 1000
    return "".join(parts)


def path(d, fill=CHARCOAL):
    return f'<path fill="{fill}" d="{d}"/>'


# --- Wordmark -----------------------------------------------------------------

def wordmark(x, top, bottom, unit=34, gap=12, foot=46):
    """Draw IIJ as stems of 1, 2 and 3 units.

    The first I runs the full height. The hook of the J tucks under the right half
    of the second I, whose stem is finished by the vermilion tag on its left.
    """
    i1, i2 = x, x + unit + gap
    j = i2 + 2 * unit + gap
    right = j + 3 * unit
    floor = bottom - foot
    hook_end = i2 + unit + gap

    centre_x = hook_end
    inner_rx, inner_ry = j - centre_x, 104
    outer_r = right - centre_x
    outer_ry = outer_r + 8

    shoulder = top + 30
    j_path = (
        f"M{j} {shoulder}L{right} {top}V{bottom - outer_ry}"
        f"A{outer_r} {outer_ry} 0 0 1 {centre_x} {bottom}"
        f"H{hook_end}V{floor}H{centre_x}"
        f"A{inner_rx} {inner_ry} 0 0 0 {j} {floor - inner_ry}Z"
    )

    cut_rx, cut_ry = inner_rx - gap, inner_ry - gap
    i2_right = j - gap
    i2_foot = floor - gap
    i2_path = (
        f"M{i2} {top}H{i2_right}V{i2_foot - cut_ry}"
        f"A{cut_rx} {cut_ry} 0 0 1 {centre_x} {i2_foot}H{i2}Z"
    )
    i1_path = f"M{i1} {top}H{i1 + unit}V{bottom}H{i1}Z"
    tag = f"M{i2} {floor}H{i2 + unit}V{bottom}H{i2}Z"
    return path(i1_path + i2_path + j_path) + path(tag, VERMILION)


# --- Weave --------------------------------------------------------------------

def resample(values, count):
    """Stretch any number of values, including none, onto count points."""
    if not values:
        return [0.0] * count
    if len(values) == 1:
        return [float(values[0])] * count
    out = []
    for n in range(count):
        at = n / (count - 1) * (len(values) - 1)
        low = int(at)
        high = min(low + 1, len(values) - 1)
        out.append(values[low] + (values[high] - values[low]) * (at - low))
    return out


def activity_field(values, count):
    """Map raw counts to a smoothed 0-1 curve.

    The ceiling never falls below 8, so one lone contribution stays quiet instead
    of being normalised up into a peak.
    """
    clean = [max(0.0, float(v or 0)) for v in values]
    ceiling = max(8.0, sorted(clean)[int(len(clean) * 0.95)] if clean else 8.0)
    raw = [min(1.0, math.log1p(v) / math.log1p(ceiling)) for v in resample(clean, count)]
    radius = max(1, count // 28)
    smooth = []
    for n in range(count):
        span = raw[max(0, n - radius): n + radius + 1]
        smooth.append(sum(span) / len(span))
    return smooth


def positions(count, start, end, density):
    """Place threads so that a higher density packs them closer together."""
    gaps = [1 / (0.42 + d) for d in density]
    total = sum(gaps[:-1])
    placed, at = [], start
    for gap in gaps:
        placed.append(at)
        at += gap / total * (end - start)
    return placed


# Fixed structure of the cloth: (u0, u1, v0, v1, kind, thread weight). This skeleton
# carries the identity, so the composition stays recognisable whatever the data does.
BLOCKS = [
    (0.00, 0.10, 0.00, 1.00, "warp_up", 1.2),
    (0.10, 0.34, 0.00, 0.58, "warp_face", 1.6),
    (0.34, 0.70, 0.00, 0.24, "weft_down", 1.3),
    (0.70, 1.00, 0.00, 0.40, "weft_face", 1.5),
    (0.34, 0.58, 0.24, 0.58, "open", 1.1),
    (0.58, 1.00, 0.24, 0.40, "herringbone", 1.3),
    (0.58, 1.00, 0.40, 0.74, "diamond", 1.3),
    (0.10, 0.58, 0.58, 0.84, "weft_face", 1.6),
    (0.10, 0.58, 0.84, 1.00, "weft_up", 1.3),
    (0.58, 0.82, 0.74, 1.00, "warp_face", 1.5),
    (0.82, 1.00, 0.74, 1.00, "warp_down", 1.2),
]
FACE_CENTRE = (0.79, 0.57)
# In these drafts the crossing thread is left out, so a break reads as clean negative
# space. Interlacing marks appear only in the face blocks and the open window.
WEFT_ONLY = {"weft_up", "weft_down", "herringbone", "diamond"}
WARP_ONLY = {"warp_up", "warp_down"}


def block_at(u, v):
    for block in BLOCKS:
        if block[0] <= u < block[1] and block[2] <= v < block[3]:
            return block[4], block[5]
    return "warp_up", 1.2


def weft_on_top(i, j, kind, repeat, centre):
    """Decide who passes over at one crossing, from weave drafts that read at a distance."""
    if kind == "weft_face":
        return (i + 2 * j) % (repeat * 3) != 0
    if kind == "warp_face":
        return (2 * i + j) % (repeat * 3) == 0
    if kind == "weft_up":
        return (i + j) % repeat >= 2
    if kind == "weft_down":
        return (i - j) % repeat >= 2
    if kind == "warp_up":
        return (i + j) % repeat < 2
    if kind == "warp_down":
        return (i - j) % repeat < 2
    if kind == "herringbone":
        return (i + abs(j % (2 * repeat) - repeat)) % repeat >= 2
    if kind == "diamond":
        return (abs(i - centre[0]) + abs(j - centre[1])) % repeat >= 2
    return True


def polyline(points, places=1):
    head = f"M{fmt(points[0][0], places)} {fmt(points[0][1], places)}"
    return head + "".join(f"L{fmt(x, places)} {fmt(y, places)}" for x, y in points[1:])


def thin(points):
    """Keep long floats gently curved without storing every crossing."""
    step = max(1, (len(points) - 1) // 4)
    return points[:-1:step] + points[-1:] if len(points) > 1 else points


def bands(count, peaks):
    """Identity density: gaussian bands of tightly packed thread."""
    return [
        sum(amp * math.exp(-(((n / count) - at) / width) ** 2) for at, width, amp in peaks)
        for n in range(count)
    ]


def weave(values, x0, y0, x1, y1, fringe=None, warps=84, wefts=62):
    """Draw the cloth from any list of counts, including an empty one.

    values    contribution counts, oldest first, at any time resolution
    x0..y1    the woven area; threads bleed past the top, bottom and right edges
    fringe    optional fn(y, j) giving how far left a loose weft may run

    Mapping from activity:
      local line density  warp spacing tightens where a value is high
      interlacing rhythm  the draft repeat shortens from 9 to 5 crossings
      repeated marks      a shorter repeat means more breaks, so more dashes
      accents             vermilion floats settle on the highest values
    """
    field = activity_field(values, warps)
    warp_density = [b + 0.9 * a for b, a in zip(bands(warps, [(0.2, 0.09, 0.72), (0.72, 0.05, 0.5)]), field)]
    weft_density = bands(wefts, [(0.32, 0.08, 0.8), (0.72, 0.1, 1.0)])
    warp_x = positions(warps, x0, x1 + 8, warp_density)
    weft_y = positions(wefts, y0 - 8, y1 + 8, weft_density)

    def vertex(i, j):
        u, v = i / (warps - 1), j / (wefts - 1)
        dx = 6.0 * math.sin(math.tau * (v * 0.8 + 0.1))
        dy = 7.0 * math.sin(math.tau * (u * 0.75 + 0.05)) * math.sin(math.pi * v)
        return warp_x[i] + dx, weft_y[j] + dy

    centre = (round(FACE_CENTRE[0] * warps), round(FACE_CENTRE[1] * wefts))
    kind = [[block_at(i / warps, j / wefts) for j in range(wefts)] for i in range(warps)]
    repeat = [9 - round(a * 4) for a in field]
    top = [[weft_on_top(i, j, kind[i][j][0], repeat[i], centre) for j in range(wefts)] for i in range(warps)]

    weft_lane = lambda i, j: top[i][j] and kind[i][j][0] != "open" and kind[i][j][0] not in WARP_ONLY
    warp_lane = lambda i, j: kind[i][j][0] not in WEFT_ONLY and (not top[i][j] or kind[i][j][0] == "open")
    strokes = {}

    def add(colour, weight, points):
        strokes.setdefault((colour, weight), []).append(polyline(thin(points)))

    for j in range(wefts):
        i = 0
        while i < warps:
            if not weft_lane(i, j):
                i += 1
                continue
            start = i
            while i < warps and weft_lane(i, j):
                i += 1
            run = [vertex(n, j) for n in range(start, i)]
            if len(run) == 1:
                x, y = run[0]
                run = [(x - 1.8, y), (x + 1.8, y)]
            add(CHARCOAL, kind[start][j][1], run)

    for i in range(warps):
        j = 0
        while j < wefts:
            if not warp_lane(i, j):
                j += 1
                continue
            start = j
            while j < wefts and warp_lane(i, j):
                j += 1
            run = [vertex(i, n) for n in range(start, j)]
            if len(run) == 1:
                x, y = run[0]
                run = [(x, y - 1.8), (x, y + 1.8)]
            add(CHARCOAL, kind[i][start][1], run)

    if fringe:
        for j in range(wefts):
            left = vertex(0, j)
            reach = fringe(left[1], j)
            if reach is not None and reach < left[0]:
                add(CHARCOAL, 1.1, [(reach, left[1]), left])

    # Accents land on the busiest open column, or on a fixed thread when idle.
    open_columns = [i for i in range(warps) if 0.34 <= i / warps < 0.58]
    stitches = ((0.31, 11), (0.36, 4), (0.41, 7))
    usable = open_columns[:-max(length for _, length in stitches) - 1]
    busiest = max(usable, key=lambda i: (round(field[i], 2), -abs(i - usable[len(usable) // 3])))
    for row, length in stitches:
        j = round(row * wefts)
        add(VERMILION, 2.2, [vertex(n, j) for n in range(busiest, busiest + length)])

    return "".join(
        f'<path fill="none" stroke="{colour}" stroke-width="{weight}" d="{"".join(parts)}"/>'
        for (colour, weight), parts in sorted(strokes.items())
    )


# --- Composition --------------------------------------------------------------

def compose(values):
    mark = wordmark(MARK_X, TOP, BOTTOM)
    out = [mark]

    size, leading = 64, 60
    first_baseline = 112
    head = []
    rag = []
    for index, line in enumerate(HEADLINE):
        baseline = first_baseline + index * leading
        cap = size * GLYPHS["display"]["cap"] / GLYPHS["display"]["upm"]
        stop = line.endswith(".")
        words = line[:-1] if stop else line
        head.append(text_path(words, TEXT_X, baseline, "display", size, -14))
        right = TEXT_X + text_width(words, "display", size, -14)
        if stop:
            side = 0.14 * size
            head_stop = f"M{fmt(right + 5)} {baseline}h{fmt(side)}v-{fmt(side)}h-{fmt(side)}Z"
            right += 5 + side
            out.append(path(head_stop, VERMILION))
        rag.append((baseline - cap - 6, baseline + 6, right))
    out.append(path("".join(head)))

    def fringe(y, j):
        for top, bottom, right in rag:
            if top <= y <= bottom:
                return right + 16 + (j * 5 % 7) * 11
        return None

    out.append(weave(values, WEAVE_X, 0, W, H, fringe))

    small = 14.5
    meta = text_path(META_TOP, TEXT_X, TOP + 10.5, "mono", small, 40)
    meta += text_path(META_FOOT, TEXT_X, BOTTOM, "mono", small, 40)
    out.append(path(meta, GRAPHITE))
    out.append(path(text_path(SUPPORT, TEXT_X, BOTTOM - 21, "mono", small, 20)))
    out.append(f'<path stroke="{CHARCOAL}" stroke-width="1" d="M{TEXT_X} {BOTTOM - 44}H{WEAVE_X - 28}"/>')

    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
        '<title id="t">IIJ: The Living Label</title>',
        '<desc id="d">Wordmark IIJ, the statement I make things that do things, and an abstract woven line pattern.</desc>',
        "<!-- Outlines: Inter Tight, IBM Plex Mono. SIL Open Font License 1.1. -->",
        f'<rect width="{W}" height="{H}" fill="{PORCELAIN}"/>',
        *out,
        "</svg>",
    ]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--values", type=Path, help="JSON list of counts, oldest first")
    parser.add_argument("--empty", action="store_true", help="render with no activity at all")
    parser.add_argument("--out", type=Path, default=ROOT / "assets" / "living-label.svg")
    args = parser.parse_args()

    values = DESIGN_STUDY
    if args.empty:
        values = []
    elif args.values:
        values = json.loads(args.values.read_text())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(compose(values))


if __name__ == "__main__":
    main()
