import json, subprocess, numpy as np, cv2, os
BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = "D:/EDIT VIDEO CLAUDE/VIEC-DANG-LAM/camtasia/huong-dan-chay-hermes-agent-vps-hostinger.tscproj"
segs = json.load(open(os.path.join(BASE, "segments.json"), encoding="utf-8"))
tl = json.load(open(os.path.join(BASE, "timeline.json"), encoding="utf-8"))
casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
casc2 = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
SW, SH = 640, 360
out = {}
for s in segs:
    src = PROJ + "/" + s["srcName"]
    cmd = ["ffmpeg", "-v", "error", "-ss", str(s["ms"]), "-t", str(s["dur"]), "-i", src, "-map", "0:v:1",
           "-vf", f"fps=1/2,scale={SW}:{SH},format=gray", "-f", "rawvideo", "-"]
    p = subprocess.run(cmd, capture_output=True)
    n = len(p.stdout) // (SW * SH)
    pts = []
    for k in range(n):
        g = np.frombuffer(p.stdout, np.uint8, SW * SH, k * SW * SH).reshape(SH, SW)
        f = casc.detectMultiScale(g, 1.1, 5, minSize=(60, 60))
        if len(f) == 0:
            f = casc2.detectMultiScale(g, 1.1, 5, minSize=(60, 60))
        if len(f):
            x, y, w, h = max(f, key=lambda r: r[2] * r[3])
            pts.append({"t": k * 2, "cx": float((x + w / 2) * 2), "cy": float((y + h / 2) * 2), "size": float(w * 2)})
    out[s["i"]] = pts
    print(s["i"], len(pts), "/", n, flush=True)
json.dump(out, open(os.path.join(BASE, "face-track.json"), "w"))
print("done")
