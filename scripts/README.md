# The Living Label

GitHub displays the committed `assets/living-label.svg`. Nothing here runs to view the profile.

```sh
python scripts/generate_label.py                       # version one, static design dataset
python scripts/generate_label.py --empty               # no activity at all
python scripts/generate_label.py --values counts.json  # any JSON list of counts, oldest first
```

`generate_label.py` uses only the Python standard library. Its output is byte-identical for identical
input. `glyphs.json` holds the outlines for Inter Tight SemiBold and IBM Plex Mono Medium (both SIL Open
Font License 1.1). `build_glyphs.py` rebuilds it with fontTools, only if the banner needs a new character.

## How the weave works

`weave(values, x0, y0, x1, y1)` builds a warped mesh of 84 warps and 62 wefts, then decides who passes
over at each crossing from a weave draft.

- `BLOCKS` is the fixed structure: which draft sits where. It never changes, so the identity holds.
- `values` is free to vary. It can be any length, including empty, and is resampled across the cloth.

| Activity drives | Effect |
|---|---|
| Local line density | Warp spacing tightens where values are high |
| Interlacing rhythm | Draft repeat shortens from 9 crossings to 5 |
| Repeated marks | A shorter repeat produces more breaks and dashes |
| Accent position | The three vermilion stitches move to the busiest open column |

Counts are log-scaled against a ceiling of at least 8, so a single contribution stays quiet.

`DESIGN_STUDY` in the script is a hand-written composition, not GitHub data.

## Future: weekly regeneration

Not implemented. When real data is wired in:

1. Fetch daily counts from the GitHub GraphQL API, `user.contributionsCollection.contributionCalendar`.
   It is free. A token with `read:user` is needed, stored as a repository secret. Private contributions
   count only if the profile setting allows them.
2. Write the counts, oldest first, to a JSON list. Treat missing days as `0`.
3. Change the `META_TOP` or `META_FOOT` label to `FIG. 01 / ACTIVITY STUDY`, which is true only from then on.
4. Run on a weekly schedule, and commit only on change. Deterministic output makes this reliable:

```yaml
on:
  schedule:
    - cron: "0 6 * * 1"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  weave:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fetch contribution counts
        env:
          GH_TOKEN: ${{ secrets.CONTRIBUTIONS_TOKEN }}
        run: |
          gh api graphql -F login=ikshithij -f query='
            query($login: String!) { user(login: $login) { contributionsCollection {
              contributionCalendar { weeks { contributionDays { contributionCount } } } } } }' \
            --jq '[.. | .contributionCount? // empty]' > counts.json
      - run: python scripts/generate_label.py --values counts.json
      - name: Commit if changed
        run: |
          git diff --quiet assets/living-label.svg && exit 0
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add assets/living-label.svg
          git commit -m "Reweave label"
          git push
```

If the fetch fails, the step fails and the committed SVG stays in place. The profile never depends on
browser JavaScript or a live service.
