# Organisation logos

Drop official logo files here, then run:

    python3 tools/set-logos.py

That swaps the lettered placeholder tiles on the home page AND the experience
page for the images. A slug with no file keeps its letter tile, which is why
ScanCafe currently shows an S.
Re-run it any time you add or remove a file. Run it with `--revert` to go
back to letters.

Expected filenames (any one extension: .svg preferred, else .png / .webp / .jpg):

| file             | used for                                   |
|------------------|--------------------------------------------|
| `amazon.*`       | Amazon Security                            |
| `microsoft.*`    | Microsoft, Windows and Microsoft, Bing Ads |
| `purdue.*`       | Purdue University, Makin Lab               |
| `iitmadras.*`    | IIT Madras (Education)                     |
| `scancafe.*`     | ScanCafe (Experience page only)            |

Official brand assets:
- Amazon   https://developer.amazon.com/en-US/alexa/branding
- Microsoft https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks
- Purdue   https://marcom.purdue.edu/our-brand/

Notes:
- Square or near-square crops sit best in the 2.75rem tile.
- Tiles keep a light plate in both light and dark themes, so a dark logo is fine
  and a logo with a transparent background is ideal.
- Each company's brand guidelines formally ask permission for third-party use.
  Personal CV sites do this routinely, but it is your call.

## Normalising a new logo

Raw downloads differ in padding, background and lettering size, so one dropped
straight in will tower over or shrink beside its neighbours. Run:

    python3 tools/normalise-logos.py img/logos/<Raw_File>.<ext> <slug>
    python3 tools/set-logos.py

That writes `img/logos/<slug>.png` at 400x160, transparent, with its letters
matched to the others (cap height 37px), then swaps it into the pages. Check any
time with:

    python3 tools/normalise-logos.py --measure img/logos/*.png

Keep the raw download beside it; the normalised file is derived and can be
regenerated.
