# Board

`assets/board.svg` is an illustration, to be replaced by a photograph of the real board.

```sh
python scripts/generate_board.py
```

`generate_board.py` uses only the Python standard library and always writes identical output.
`glyphs.json` holds Inter Tight Medium outlines (SIL Open Font License 1.1). `build_glyphs.py`
rebuilds it with fontTools, only if the text gains a new character.
