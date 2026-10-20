# -*- coding: utf-8 -*-
"""Pick the shared-screen pictures out of a meeting recording.

Meeting recordings (Zoom / Meet / Webex, captured as a full desktop or as the
meeting window) are mostly faces, avatars and app chrome; the useful pictures
are the moments someone shares a screen. slides.detect() is tuned for
conference decks and misses most of them, and deduping whole frames lets the
chrome dominate, so different screens look "the same".

This module:
  1. finds the shared-content rectangle in each frame (not dark UI, not
     desktop wallpaper, large, and full of text edges -> not a camera feed),
  2. crops to it,
  3. dedupes on the crop itself, against everything kept so far.

  python screenshare.py frames <dir_of_jpgs> <outdir>   # e.g. window captures
  python screenshare.py video  <video> <outdir> [--every 5]
Writes <outdir>/kept/ss_NNN.jpg (+ .txt with the source time) and sheet_NN.jpg.
"""
import glob, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image
import cv2

MIN_AREA = 0.10      # content box must cover >= 10% of the frame
MIN_EDGES = 0.012    # fraction of edge pixels: rejects blank screens and plain avatar tiles (faces are caught by SKIN)
SKIN = 0.08         # skin-tone fraction above this = camera feed (faces), not a screen
DIFF = 6.0           # mean abs grey difference (0-255) on a 96x54 thumbnail = "new picture"


def content_box(img):
    """(x0, y0, x1, y1) of the shared content, or None."""
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    grey = (r * 30 + g * 59 + b * 11) // 100
    sat = np.max(a, axis=2) - np.min(a, axis=2)
    # Zoom/Meet chrome and black bars are dark AND neutral grey; dark-themed slides
    # (navy, purple) are dark but coloured, so they stay content
    dark_ui = (grey < 42) & (sat < 20)
    wallpaper = (b - np.maximum(r, g) > 45) & (b > 110)   # Windows blue desktop
    mask = (~(dark_ui | wallpaper)).astype(np.uint8)
    h, w = mask.shape
    k = max(3, w // 160)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n < 2:
        return None
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, bw, bh = stats[i, :4]
    if bw * bh < MIN_AREA * w * h or bw < 0.25 * w:
        return None
    crop = grey[y:y + bh, x:x + bw].astype(np.uint8)
    edges = cv2.Canny(crop, 60, 160)
    if edges.mean() / 255 < MIN_EDGES:                    # avatar / blank
        return None
    small = cv2.resize(a[y:y + bh, x:x + bw].astype(np.uint8), (320, 180))
    ycc = cv2.cvtColor(small, cv2.COLOR_RGB2YCrCb).astype(np.int16)
    skin = ((ycc[..., 1] >= 138) & (ycc[..., 1] <= 173) & (ycc[..., 2] >= 77) &
            (ycc[..., 2] <= 127) & (ycc[..., 0] > 60)).mean()
    if skin > SKIN:                                       # camera feed: people, not a shared screen
        return None
    return int(x), int(y), int(x + bw), int(y + bh)


def _thumb(img):
    return np.asarray(img.convert("L").resize((96, 54))).astype(np.float32)


def pick(items, outdir):
    """items: iterable of (label, PIL.Image). Keeps distinct shared-screen crops."""
    kept_dir = os.path.join(outdir, "kept")
    os.makedirs(kept_dir, exist_ok=True)
    thumbs, out, seen = [], [], 0
    for label, img in items:
        seen += 1
        box = content_box(img)
        if not box:
            continue
        crop = img.crop(box)
        t = _thumb(crop)
        if any(np.abs(t - p).mean() < DIFF for p in thumbs):
            continue
        thumbs.append(t)
        p = os.path.join(kept_dir, f"ss_{len(out) + 1:03d}.jpg")
        crop.convert("RGB").save(p, quality=92)
        open(p[:-4] + ".txt", "w").write(str(label))
        out.append(p)
    return seen, out


def from_frames(src, outdir):
    files = sorted(glob.glob(os.path.join(src, "*.jpg")) + glob.glob(os.path.join(src, "*.png")))
    return pick(((os.path.basename(f), Image.open(f)) for f in files), outdir)


def from_video(video, outdir, every=5):
    tmp = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-vf", f"fps=1/{every}",
                    "-q:v", "3", os.path.join(tmp, "f_%05d.jpg")], check=True)
    files = sorted(glob.glob(os.path.join(tmp, "*.jpg")))
    def gen():
        for i, f in enumerate(files):
            s = i * every
            yield f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}", Image.open(f)
    res = pick(gen(), outdir)
    for f in files:
        os.remove(f)
    return res


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import slides
    mode, src, outdir = sys.argv[1:4]
    every = int(sys.argv[sys.argv.index("--every") + 1]) if "--every" in sys.argv else 5
    seen, kept = from_frames(src, outdir) if mode == "frames" else from_video(src, outdir, every)
    sheets = slides.sheets(kept, outdir, per=30, cols=5) if kept else []
    print(json.dumps({"seen": seen, "kept": len(kept), "sheets": sheets}))
