#!/usr/bin/env python3
"""Extract the glyph outlines the board needs into scripts/glyphs.json.

Only needed when the text gains a new character. Requires fontTools and Inter
Tight Medium, licensed under the SIL Open Font License 1.1:

    python scripts/build_glyphs.py InterTight-Medium.woff
"""
import json
import sys
from pathlib import Path

from fontTools.pens.basePen import decomposeQuadraticSegment
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

CHARS = "This profile the pubc tp of a fairly vate ceberg.Rv"


def outline(font, name):
    """Return a glyph as flat [op, *coords] lists using only M, L, Q and Z."""
    pen = DecomposingRecordingPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    out, last = [], None
    for op, args in pen.value:
        if op == "moveTo":
            last = args[0]
            out.append(["M", *last])
        elif op == "lineTo":
            last = args[0]
            out.append(["L", *last])
        elif op == "qCurveTo":
            for ctrl, end in decomposeQuadraticSegment(args):
                out.append(["Q", *ctrl, *end])
                last = end
        elif op == "closePath":
            out.append(["Z"])
    return out


def extract(path, chars):
    font = TTFont(path)
    cmap = font.getBestCmap()
    glyphs = {}
    for char in chars:
        name = cmap[ord(char)]
        glyphs[char] = {"adv": font["hmtx"][name][0], "d": outline(font, name)}
    return {
        "name": font["name"].getDebugName(4),
        "upm": font["head"].unitsPerEm,
        "cap": font["OS/2"].sCapHeight,
        "glyphs": glyphs,
    }


def main():
    data = {"licence": "SIL Open Font License 1.1", **extract(sys.argv[1], sorted(set(CHARS)))}
    target = Path(__file__).with_name("glyphs.json")
    target.write_text(json.dumps(data, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
