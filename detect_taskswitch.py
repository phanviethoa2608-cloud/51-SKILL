"""Detect the Windows Alt-Tab task switcher (large neutral-gray translucent panel with window thumbnails in the centre).
Works on a RAW 1920x1080 screen stream (default) or on a composed video where the screen sits at x96..1824,y70..1042 (--composed).
usage: python detect_taskswitch.py <video> [--composed] [--stream 0] [--fps 5] [--ss 0] [--t 9999]
prints intervals (seconds, relative to --ss)."""
import subprocess, sys, numpy as np

a = sys.argv
path = a[1]
composed = "--composed" in a
fps = float(a[a.index("--fps") + 1]) if "--fps" in a else 5
ss = float(a[a.index("--ss") + 1]) if "--ss" in a else 0
tt = float(a[a.index("--t") + 1]) if "--t" in a else 1e9
stream = a[a.index("--stream") + 1] if "--stream" in a else "0"
W, H = 480, 270
cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(tt), "-i", path, "-map", f"0:v:{stream}", "-vf", f"fps={fps},scale={W}:{H},format=bgr24", "-f", "rawvideo", "-"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
hits = []
i = 0
while True:
    b = p.stdout.read(W * H * 3)
    if len(b) < W * H * 3:
        break
    img = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.int16)
    if composed:
        img = img[int(70 / 4):int(1042 / 4), int(96 / 4):int(1824 / 4)]
    h, w = img.shape[:2]
    band = img[int(.33 * h):int(.64 * h), int(.12 * w):int(.88 * w)]
    bl, gr, rd = band[:, :, 0], band[:, :, 1], band[:, :, 2]
    g = (bl + gr + rd) / 3
    neutral = (abs(bl - gr) < 10) & (abs(gr - rd) < 10) & (g > 48) & (g < 110)
    frac, rows = float(neutral.mean()), float((neutral.mean(axis=1) > 0.55).mean())
    blue = float(((bl > 200) & (gr > 130) & (gr < 215) & (rd < 120)).mean())   # selected-window accent outline
    hits.append((i / fps, frac >= 0.3 and rows >= 0.25 and blue >= 0.002))
    i += 1
runs, cur = [], None
for t, h_ in hits:
    if h_ and cur is None:
        cur = [t, t]
    elif h_:
        cur[1] = t
    elif cur:
        runs.append(cur)
        cur = None
if cur:
    runs.append(cur)
runs = [(x + ss, y + ss + 1 / fps) for x, y in runs if y - x >= 0.3 or True]
print(len(runs), "task-switcher candidates")
for x, y in runs:
    print(f"{x:9.1f} - {y:9.1f}  ({y-x:.1f}s)")
