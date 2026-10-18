# -*- coding: utf-8 -*-
"""Speaker timeline for a Zoom meeting captured as window JPEGs (HHMMSS.jpg).

  python zoom_speakers.py <win_dir> <transcript_segments.json> <audio_start HH:MM:SS> <out.txt>

Finds the green active-speaker border in the tile strip of each frame, OCRs the
name with macOS Vision (ocr_tiles.swift), and writes the transcript with a
<<speaker>> marker at every change. Names ending in "?" were inferred from the
nearest earlier run, not seen in a frame.
"""
import glob, json, os, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def tiles(win_dir, out_dir, step=2):
    for f in sorted(glob.glob(win_dir + "/*.jpg"))[::step]:
        im = Image.open(f).convert("RGB"); w, h = im.size
        top = int(h * .04); strip = np.asarray(im.crop((0, top, w, int(h * .22)))).astype(int)
        g = (strip[:, :, 1] > 150) & (strip[:, :, 1] - strip[:, :, 0] > 60) & (strip[:, :, 2] < 160)
        cc = g.sum(0)
        if cc.max() < 30:                      # no vertical green edge = no active tile
            continue
        cols = np.where(cc > cc.max() * 0.7)[0]    # relative: works at any window size
        if len(cols) < 2 or not w * .04 < cols.max() - cols.min() < w * .3:
            continue
        x0, x1 = cols.min(), cols.max()
        rows = np.where(g[:, x0:x1].sum(1) > (x1 - x0) * 0.5)[0]
        y0, y1 = (rows.min(), rows.max()) if len(rows) >= 2 else (0, strip.shape[0] - 1)
        im.crop((x0, top + y0, x1, top + y1)).save(os.path.join(out_dir, os.path.basename(f)))


def main(win_dir, seg_json, start, out):
    tmp = tempfile.mkdtemp()
    tiles(win_dir, tmp)
    ocr = subprocess.run(["swift", os.path.join(HERE, "ocr_tiles.swift"), tmp],
                         capture_output=True, text=True).stdout
    h, m, s = map(int, start.split(":")); t0 = h * 3600 + m * 60 + s
    runs = []
    for l in ocr.splitlines():
        f, _, name = l.strip().partition(" ")
        name = re.sub(r"@.*", "", name.split(" | ")[-1]).replace("...", "").strip()
        t = int(f[:2]) * 3600 + int(f[2:4]) * 60 + int(f[4:6]) - t0
        if not name or t < -5:
            continue
        if runs and runs[-1][2] == name and t - runs[-1][1] <= 15:
            runs[-1][1] = t
        else:
            runs.append([t, t, name])

    def who(t):
        prev = None
        for a, b, n in runs:
            if a - 4 <= t <= b + 4:
                return n
            if b < t:
                prev = n
        return (prev or "?") + "?"

    parts, cur = [], None
    for sg in json.load(open(seg_json)):
        n = who((sg["start"] + sg["end"]) / 2)
        if n != cur:
            parts.append(f"\n[{int(sg['start'])//60}:{int(sg['start'])%60:02d}] <<{n}>>"); cur = n
        parts.append(sg["text"].strip())
    open(out, "w").write(" ".join(parts))
    print(" -> ".join(dict.fromkeys(n for a, b, n in runs if b - a >= 6)))


if __name__ == "__main__":
    main(*sys.argv[1:5])
