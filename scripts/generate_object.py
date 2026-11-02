#!/usr/bin/env python3
"""IIJ object: generates assets/iij.stl and embeds it in README.md.

GitHub renders a fenced stl block as an interactive 3D viewer. The wordmark is a
closed, printable solid. Stems keep the 1:2:3 widths and rise in 1:2:3 heights;
the foot of the second I is the tallest pin. Standard library only.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARK_H = 328
UNIT, GAP, FOOT = 34, 12, 46
BASE, MARGIN = 12, 24
RISE = 26       # height added per stem
CHAMFER = 2.5
ARC_STEPS = 18


def arc(cx, cy, rx, ry, start, end):
    """Quarter-ellipse points, endpoints included, angles in degrees."""
    return [
        (cx + rx * math.cos(math.radians(start + (end - start) * n / ARC_STEPS)),
         cy + ry * math.sin(math.radians(start + (end - start) * n / ARC_STEPS)))
        for n in range(ARC_STEPS + 1)
    ]


def outlines():
    """Return (polygon, height) for each part, counter-clockwise, y up."""
    i1 = 0
    i2 = UNIT + GAP
    j = i2 + 2 * UNIT + GAP
    right = j + 3 * UNIT
    hook = i2 + UNIT + GAP
    floor = FOOT

    in_rx, in_ry = j - hook, 104
    out_rx, out_ry = right - hook, right - hook + 8

    stem_1 = [(i1, 0), (i1 + UNIT, 0), (i1 + UNIT, MARK_H), (i1, MARK_H)]

    cut_rx, cut_ry = in_rx - GAP, in_ry - GAP
    foot_y = floor + GAP
    stem_2 = [(i2, foot_y), *arc(hook, foot_y + cut_ry, cut_rx, cut_ry, -90, 0), (j - GAP, MARK_H), (i2, MARK_H)]

    letter_j = [
        (hook, 0),
        *arc(hook, out_ry, out_rx, out_ry, -90, 0),
        (right, MARK_H),
        (j, MARK_H - 30),
        *arc(hook, floor + in_ry, in_rx, in_ry, 0, -90),
    ]

    pin = [(i2, 0), (i2 + UNIT, 0), (i2 + UNIT, FOOT), (i2, FOOT)]
    return [
        (stem_1, RISE),
        (stem_2, 2 * RISE),
        (letter_j, 3 * RISE),
        (pin, 4 * RISE),
    ]


def area(poly):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1])) / 2


def inset(poly, distance):
    """Offset a counter-clockwise polygon inward, keeping its vertex count."""
    out = []
    count = len(poly)
    for n in range(count):
        ax, ay = poly[n - 1]
        bx, by = poly[n]
        cx, cy = poly[(n + 1) % count]
        l1 = math.hypot(bx - ax, by - ay)
        l2 = math.hypot(cx - bx, cy - by)
        n1 = (-(by - ay) / l1, (bx - ax) / l1)
        n2 = (-(cy - by) / l2, (cx - bx) / l2)
        mx, my = n1[0] + n2[0], n1[1] + n2[1]
        scale = distance / max(0.4, (mx * n1[0] + my * n1[1]))
        out.append((bx + mx * scale, by + my * scale))
    return out


def triangulate(poly):
    """Ear-clip a simple counter-clockwise polygon into index triples."""
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def inside(p, a, b, c):
        return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0

    left = list(range(len(poly)))
    tris = []
    while len(left) > 2:
        for n in range(len(left)):
            i, j, k = left[n - 1], left[n], left[(n + 1) % len(left)]
            a, b, c = poly[i], poly[j], poly[k]
            if cross(a, b, c) <= 1e-9:
                continue
            if any(inside(poly[m], a, b, c) for m in left if m not in (i, j, k)):
                continue
            tris.append((i, j, k))
            left.pop(n)
            break
        else:
            left.pop(0)
    return tris


def prism(poly, z0, z1, chamfer=CHAMFER):
    """Closed extrusion with a chamfered top edge, as triangles."""
    if area(poly) < 0:
        poly = poly[::-1]
    # Drop points that coincide with their neighbour, so edge lengths stay nonzero.
    poly = [p for n, p in enumerate(poly) if math.dist(p, poly[n - 1]) > 1e-6]
    top = inset(poly, chamfer)
    tris = []
    for a, b, c in triangulate(poly):
        tris.append(((*poly[a], z0), (*poly[c], z0), (*poly[b], z0)))
    for a, b, c in triangulate(poly):
        tris.append(((*top[a], z1), (*top[b], z1), (*top[c], z1)))
    shoulder = z1 - chamfer
    for n in range(len(poly)):
        m = (n + 1) % len(poly)
        low_a, low_b = (*poly[n], z0), (*poly[m], z0)
        mid_a, mid_b = (*poly[n], shoulder), (*poly[m], shoulder)
        top_a, top_b = (*top[n], z1), (*top[m], z1)
        tris += [(low_a, low_b, mid_b), (low_a, mid_b, mid_a)]
        tris += [(mid_a, mid_b, top_b), (mid_a, top_b, top_a)]
    return tris


def solid():
    tris = []
    width = 4 * UNIT + 2 * UNIT + 2 * GAP
    plate = [(-MARGIN, -MARGIN), (width + MARGIN, -MARGIN), (width + MARGIN, MARK_H + MARGIN), (-MARGIN, MARK_H + MARGIN)]
    tris += prism(plate, 0, BASE)
    for poly, height in outlines():
        tris += prism(poly, BASE - 1, BASE + height)
    return tris


def normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    size = math.hypot(nx, ny, nz) or 1
    return nx / size, ny / size, nz / size


def num(value):
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def to_stl(tris):
    lines = ["solid iij"]
    for a, b, c in tris:
        lines.append("facet normal " + " ".join(num(v) for v in normal(a, b, c)))
        lines.append("outer loop")
        lines += ["vertex " + " ".join(num(v) for v in p) for p in (a, b, c)]
        lines += ["endloop", "endfacet"]
    lines.append("endsolid iij")
    return "\n".join(lines) + "\n"


README = """# I make things that do things.

```stl
{stl}```

<sub>Drag it.</sub>
"""


def main():
    stl = to_stl(solid())
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "iij.stl").write_text(stl)
    (ROOT / "README.md").write_text(README.format(stl=stl))


if __name__ == "__main__":
    main()
