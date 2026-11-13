"""QA: find 'dead' frames = the screen window region is (almost) uniform AND dark (p95-p5<=12 and p95<60; robust to cam circle/logo overlays) (black / empty slide background).
usage: python scan_blank.py video.mp4 [fps=10] [min_dur=0.2]
Region = screen window (x96..1824, y70..1042) of the 1920x1080 layout; for cam-only frames use whole frame."""
import subprocess, sys, numpy as np

path = sys.argv[1]
fps = float(sys.argv[2]) if len(sys.argv) > 2 else 10
mind = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
W, H = 480, 270
cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={W}:{H},format=gray", "-f", "rawvideo", "-"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
x0, x1, y0, y1 = int(96 / 4), int(1824 / 4), int(70 / 4), int(1042 / 4)
i = 0
flags = []
while True:
    b = p.stdout.read(W * H)
    if len(b) < W * H:
        break
    g = np.frombuffer(b, np.uint8).reshape(H, W)[y0:y1, x0:x1]
    p5, p95 = np.percentile(g, 5), np.percentile(g, 95)
    m, s = float(g.mean()), float(p95 - p5)
    flags.append((i / fps, m, s, (p95 - p5 <= 12 and p95 < 60)))
    i += 1
runs, cur = [], None
for t, m, s, bad in flags:
    if bad and cur is None:
        cur = [t, t, m]
    elif bad:
        cur[1] = t
    elif cur is not None:
        runs.append(cur)
        cur = None
if cur:
    runs.append(cur)
runs = [(a, b + 1 / fps, m) for a, b, m in runs if b + 1 / fps - a >= mind]
print(len(runs), "dead-frame runs >=", mind, "s; total", round(sum(b - a for a, b, _ in runs), 1), "s")
for a, b, m in runs:
    print(f"{a:8.1f} - {b:8.1f}  ({b-a:.1f}s) mean_luma={m:.0f}")
