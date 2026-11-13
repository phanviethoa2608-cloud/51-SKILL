"""Dựng khung (MẪU CHUẨN 2, chủ kênh chốt 2026-10-20) — chạy TRƯỚC ed_overlay:
  · căn nhân vật vào GIỮA khung khi họ đã đứng yên (lúc đang đi vào khung thì không bám theo);
    người đứng lệch → zoom nền vừa đủ (≤ 1.12) để có chỗ dời khung.
  · TỰ ZOOM vào ý quan trọng (đọc từ plan.json), KHÔNG lạm dụng: ~2 lần / 15s — câu chốt (serif_pair) +0.22 vào nhanh,
    câu kết cuối video +0.08 đẩy chậm. Ép tay bằng --zoom hoặc plan "zoom".
Cùng một phép crop cho video và mask → reframe.mp4 + mask_reframe.mp4 (plan "mask": "mask_reframe.mp4",
check/snap/render chạy trên reframe.mp4).

python reframe.py <video> --mask <work>/mask.mp4 -o <work> --plan <work>/plan.json      ← MẶC ĐỊNH (tự căn giữa + tự zoom)
python reframe.py <video> --mask <work>/mask.mp4 -o <work> --zoom "3.72-6.3:0.22,12.3-15.1:0.08:slow"   ← ép tay
  --zoom "a-b:k"  : từ giây a tới b phóng thêm k (0.22 = +22%), vào 0.38s, ra 0.45s (b ≥ cuối video → giữ tới hết)
  --zoom "a-b:k:slow" : đẩy chậm (vào trong ~1.1s) — hợp câu kết
  --no-center     : chỉ zoom, không dời khung
Lưu ý: câu có cụm serif ở NGỰC thì zoom ≤ +0.08 (mặt to → ngực hết chỗ, engine tự thu chữ còn ×0.7).
"""
import argparse
import subprocess
from pathlib import Path

import cv2
import numpy as np


def ss(a, b, t):
    x = min(max((t - a) / max(b - a, 1e-6), 0.0), 1.0)
    return x * x * (3 - 2 * x)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip().split(",")
    n, d = out[2].split("/")
    return int(out[0]), int(out[1]), float(n) / float(d)


def has_audio(path):
    return bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
                                path], capture_output=True, text=True).stdout.strip())


def scene_cuts(path, thr=0.3):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vf", f"select='gt(scene,{thr})',showinfo", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [float(x.split("pts_time:")[1].split()[0]) for x in err.splitlines() if "pts_time:" in x]


def read(path, W, H, gray):
    pix = "gray" if gray else "bgr24"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", pix, "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape((-1, H, W) if gray else (-1, H, W, 3))


ZOOM_FAST, ZOOM_END = 0.22, 0.08     # câu chốt: +22% vào nhanh · câu kết (cụm serif ở ngực): +8% đẩy chậm


def auto_zoom(plan_path, dur):
    """MẶC ĐỊNH (chủ kênh 2026-10-20): tự zoom vào ý quan trọng, ~2 lần / 15s, không lạm dụng.
    Ứng viên theo thứ tự ưu tiên: moment ghi "zoom": true/số → cụm serif_pair (câu chốt) → cụm cuối video (câu kết).
    Cụm kết thúc video = đẩy chậm, nhẹ (+0.08, cụm ngực còn chỗ); còn lại = vào nhanh +0.22, giữ tới cụm sau.
    Plan "zoom": false → tắt; "zoom": [["a-b:k"], ...] hoặc chuỗi như --zoom → dùng đúng danh sách đó."""
    import json
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8-sig"))
    z = plan.get("zoom", True)
    if z is False:
        return []
    if isinstance(z, (str, list)):
        items = z.split(",") if isinstance(z, str) else z
        res = []
        for it in items:
            p = it.split(":")
            t0, t1 = (float(v) for v in p[0].split("-"))
            res.append((t0, t1, float(p[1]), len(p) > 2 and p[2] == "slow"))
        return res
    ms = sorted([m for m in plan.get("moments", []) if m.get("type", "text") not in ("flash", "image") and "start" in m],
                key=lambda m: float(m["start"]))
    limit = max(1, round(dur / 15 * 2))
    cand = []
    for i, m in enumerate(ms):
        if m.get("zoom") is False:
            continue
        s = float(m["start"])
        e = float(ms[i + 1]["start"]) if i + 1 < len(ms) else dur          # giữ tới cụm sau (engine cũng giữ chữ tới đó)
        last = i + 1 == len(ms) and dur - s < 4.0
        prio = 0 if m.get("zoom") not in (None, False) else (1 if m.get("style") == "serif_pair" else (2 if last else 9))
        if prio == 9:
            continue
        k = float(m["zoom"]) if isinstance(m.get("zoom"), (int, float)) and m["zoom"] is not True else (ZOOM_END if last else ZOOM_FAST)
        cand.append((prio, s, (s - 0.12, dur if last else e, k, last)))
    cand.sort(key=lambda c: (c[0], c[1]))
    picked, used = [], []
    for _, s, p in cand:
        if len(picked) >= limit or any(abs(s - u) < 4.0 for u in used):     # 2 cú zoom cách nhau ≥ 4s
            continue
        picked.append(p)
        used.append(s)
    return sorted(picked)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--mask", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--zoom", default="")
    ap.add_argument("--plan", help="plan.json — không có --zoom thì TỰ CHỌN chỗ zoom từ plan (mặc định của skill)")
    ap.add_argument("--no-center", action="store_true")
    ap.add_argument("--max-base", type=float, default=1.12)
    a = ap.parse_args()
    out = Path(a.out)
    W, H, fps = probe(a.video)
    masks = read(a.mask, W, H, True)
    n = len(masks)
    T = np.arange(n) / fps
    dur = n / fps

    # đầu người: tâm ngang + đỉnh đầu (15% chiều cao từ đỉnh)
    cx, top = np.full(n, np.nan), np.full(n, np.nan)
    for i, m in enumerate(masks):
        ys, xs = np.nonzero(m > 128)
        if len(ys) > 0.01 * W * H:
            t0 = ys.min()
            sel = ys < t0 + int(0.15 * H)
            cx[i], top[i] = xs[sel].mean() / W, t0 / H

    cuts = [0.0] + [c for c in scene_cuts(a.video) if 0.3 < c < dur - 0.3] + [dur]
    shots = [(int(round(cuts[k] * fps)), min(n, int(round(cuts[k + 1] * fps)))) for k in range(len(cuts) - 1)]
    sm = np.full(n, 0.5)
    base = np.ones(n)
    ay = np.full(n, 0.40)
    k = max(1, int(0.8 * fps))
    for lo, hi in shots:
        seg = cx[lo:hi].copy()
        if np.all(np.isnan(seg)):
            continue
        seg[np.isnan(seg)] = np.nanmedian(seg)
        pad = np.pad(seg, (k, k), mode="edge")
        sm[lo:hi] = np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
        # lúc ĐỨNG YÊN: từ khung đầu tiên mà 0.5s sau đó tâm đầu lệch < 3%
        win = max(1, int(0.5 * fps))
        onset = next((i for i in range(len(seg) - win) if np.ptp(seg[i:i + win]) < 0.03), None)
        if onset is None or a.no_center:
            continue
        rest = seg[onset:]
        off = abs(float(np.median(rest)) - 0.5)
        zb = min(a.max_base, 1 / max(1 - 2 * off, 1e-3)) if off > 0.02 else 1.0
        t_on = T[lo + onset]
        for i in range(lo, hi):
            base[i] = 1 + (zb - 1) * ss(t_on - 0.2, t_on + 0.6, T[i])
        tp = top[lo:hi]
        if not np.all(np.isnan(tp)):
            ay[lo:hi] = float(np.nanmedian(tp[onset:])) + 0.09   # ~giữa mặt

    punches = []
    for item in filter(None, a.zoom.split(",")):
        parts = item.split(":")
        t0, t1 = (float(v) for v in parts[0].split("-"))
        punches.append((t0, t1, float(parts[1]), len(parts) > 2 and parts[2] == "slow"))
    if not punches and a.plan:
        punches = auto_zoom(a.plan, dur)
    for t0, t1, kk, slow in punches:
        print(f"Zoom {t0:.2f}–{t1:.2f}s +{kk:.2f}{' (đẩy chậm)' if slow else ''}")

    def zoom(i):
        t, z = T[i], 1.0
        for t0, t1, kk, slow in punches:
            r = ss(t0, t0 + (1.1 if slow else 0.38), t) * (1 if t1 >= dur - 0.05 else 1 - ss(t1 - 0.15, t1 + 0.3, t))
            z += kk * r
        return base[i] + (z - 1)          # cộng (không nhân) để tổng zoom không vọt

    def matrix(i):
        z = zoom(i)
        cw, ch = W / z, H / z
        cxp = sm[i] if not a.no_center else 0.5
        x0 = min(max(cxp * W - cw / 2, 0), W - cw)
        y0 = min(max(ay[i] * H - ay[i] * ch, 0), H - ch)
        return np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])

    def write(frames, path, gray):
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray" if gray else "bgr24", "-s", f"{W}x{H}",
               "-r", f"{fps}", "-i", "-"]
        if not gray and has_audio(a.video):
            cmd += ["-i", a.video, "-map", "0:v", "-map", "1:a", "-c:a", "copy"]
        cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "16" if gray else "12", "-pix_fmt", "yuv420p", str(path)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i, f in enumerate(frames):
            p.stdin.write(cv2.warpAffine(f, matrix(min(i, n - 1)), (W, H),
                                         flags=cv2.INTER_LINEAR if gray else cv2.INTER_LANCZOS4,
                                         borderMode=cv2.BORDER_REPLICATE).tobytes())
        p.stdin.close()
        p.wait()

    write(masks, out / "mask_reframe.mp4", True)
    write(read(a.video, W, H, False), out / "reframe.mp4", False)
    print(f"Cắt cảnh: {', '.join(f'{c:.2f}s' for c in cuts[1:-1]) or 'không'}")
    for t in np.arange(0.5, dur, max(1.0, dur / 12)):
        i = int(t * fps)
        print(f"  {t:5.1f}s  zoom {zoom(i):.2f}  tâm đầu {sm[i]:.2f}")
    print(f"Xong → {out / 'reframe.mp4'} + {out / 'mask_reframe.mp4'}")


if __name__ == "__main__":
    main()
