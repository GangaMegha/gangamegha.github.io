#!/usr/bin/env python3
"""Normalise a raw logo download into a tile-ready image.

    python3 tools/normalise-logos.py img/logos/ScanCafe_logo.webp scancafe
    python3 tools/normalise-logos.py img/logos/Foo.png foo 1.4   # one-off boost
    python3 tools/normalise-logos.py --measure img/logos/*.png

Raw brand downloads differ wildly in canvas padding, background and lettering
size, so dropping one straight into a tile makes it tower over or shrink
beside its neighbours. This lands every logo on the same 400x160 transparent
canvas with the same LETTER height, so the tiles read as a set.

Why letter height and not total ink or bounding box: a lockup with an emblem
(IIT Madras's seal, Amazon's swoosh) has most of its ink outside the lettering,
so matching total ink shrinks the words to nothing. We label connected
components, drop ones far wider than they are tall (swooshes, rules, underlines),
and take the 90th percentile of the rest as the cap height.
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage

CANVAS = (400, 160)
TARGET_CAP = 37.0      # px of cap height on the 400x160 canvas

# Optical correction. Matching cap height makes most marks agree, but a
# single-line wordmark with no emblem leaves the tile half empty, so it reads
# smaller than a lockup whose seal or swoosh fills the same box. Boost those.
SCALE = {
    "scancafe": 1.6,   # plain wordmark, no emblem
}
WIDE_RATIO = 3.2       # component wider than this x its height is not a letter
ALPHA_ON = 40          # alpha above this counts as ink

def to_rgba(path):
    """Load, and if the image is opaque treat near-white as the background."""
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    if a[..., 3].min() > 250:                      # fully opaque -> key out white
        rgb = a[..., :3]
        alpha = 255.0 - rgb.min(axis=2)            # white -> 0, dark -> high
        keep = alpha > 0
        out = np.zeros_like(a)
        # un-premultiply so colours stay saturated instead of going muddy
        scale = np.where(keep, 255.0 / np.maximum(alpha, 1e-6), 0)[..., None]
        out[..., :3] = np.clip((rgb - 255.0) * scale + 255.0, 0, 255)
        out[..., 3] = alpha
        a = out
    return a

def cap_height(alpha):
    ink = alpha > ALPHA_ON
    if not ink.any():
        return None, 0
    lab, n = ndimage.label(ink)
    hs = []
    for sl in ndimage.find_objects(lab):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if h < 2 or w < 2:
            continue
        if w > WIDE_RATIO * h:        # swoosh, rule, underline: not a letter
            continue
        hs.append(h)
    if not hs:
        return None, n
    return float(np.percentile(hs, 90)), n

def normalise(src, slug, outdir, boost=None):
    a = to_rgba(src)
    cap, ncomp = cap_height(a[..., 3])
    if cap is None:
        raise SystemExit("no letter-like components found in %s" % src)
    boost = SCALE.get(slug, 1.0) if boost is None else boost
    scale = (TARGET_CAP * boost) / cap
    im = Image.fromarray(a.astype(np.uint8), "RGBA")
    # crop to the ink before scaling, so canvas padding in the source is ignored
    bbox = Image.fromarray((a[..., 3] > ALPHA_ON).astype(np.uint8) * 255).getbbox()
    im = im.crop(bbox)
    w, h = im.size
    new = (max(1, round(w * scale)), max(1, round(h * scale)))
    if new[0] > CANVAS[0] - 8 or new[1] > CANVAS[1] - 8:   # never overflow the tile
        fit = min((CANVAS[0] - 8) / new[0], (CANVAS[1] - 8) / new[1])
        new = (max(1, round(new[0] * fit)), max(1, round(new[1] * fit)))
        print("   (clamped to fit the tile; cap height will be under target)")
    im = im.resize(new, Image.LANCZOS)
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.paste(im, ((CANVAS[0] - new[0]) // 2, (CANVAS[1] - new[1]) // 2), im)
    out = os.path.join(outdir, slug + ".png")
    canvas.save(out)
    got, _ = cap_height(np.asarray(canvas).astype(np.float32)[..., 3])
    print("%-28s -> %-16s source cap %.1fpx (%d components), boost %.2fx, result cap %.1fpx"
          % (os.path.basename(src), slug + ".png", cap, ncomp, boost, got or -1))
    return out

def measure(paths):
    for p in paths:
        a = to_rgba(p)
        cap, n = cap_height(a[..., 3])
        print("%-28s %-12s cap %.1fpx  (%d components)"
              % (os.path.basename(p), "%dx%d" % Image.open(p).size, cap or -1, n))

if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--measure":
        measure(args[1:])
    elif len(args) in (2, 3):
        normalise(args[0], args[1], os.path.dirname(args[0]) or ".",
                  float(args[2]) if len(args) == 3 else None)
    else:
        raise SystemExit(__doc__)
