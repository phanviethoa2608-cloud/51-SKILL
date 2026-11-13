"""Làm đẹp hình (chủ kênh chốt 2026-10-20) — CHỈ KHI NGƯỜI DÙNG YÊU CẦU làm đẹp video. Chạy SAU reframe.py, TRƯỚC ed_overlay (chữ không bị đổi màu):
  · làm mịn da: bilateral chỉ trên vùng DA NGƯỜI (mask người ∧ dò màu da YCrCb, viền mềm), giữ lại một phần vân da;
  · nâng sáng tự động theo độ sáng trung bình, tương phản mềm (đường cong S nhẹ), 
    da TRẮNG không vàng (Lab: sáng thêm, bớt b*), màu trung tính hơi mát, nét nhẹ, tối góc nhẹ → look sang trọng cho video quay bằng camera thường.
python grade.py <work>/reframe.mp4 --mask <work>/mask_reframe.mp4 -o <work>/reframe_grade.mp4 [--skin 0.6] [--look sang]
Sau đó check/render chạy trên reframe_grade.mp4 (cùng khung với mask_reframe.mp4).
"""
import argparse
import subprocess

import cv2
import numpy as np


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True).stdout.strip().split(",")
    n, d = out[2].split("/")
    return int(out[0]), int(out[1]), float(n) / float(d)


def frames(path, W, H, gray):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H}", "-f", "rawvideo",
                          "-pix_fmt", "gray" if gray else "bgr24", "-"], stdout=subprocess.PIPE)
    n = W * H * (1 if gray else 3)
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape((H, W) if gray else (H, W, 3))


def skin_mask(img, person):
    ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    sk = cv2.inRange(ycc, (40, 135, 80), (245, 175, 128))
    sk = cv2.bitwise_and(sk, (person > 110).astype(np.uint8) * 255)
    sk = cv2.morphologyEx(sk, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(sk, (0, 0), 4).astype(np.float32)[..., None] / 255.0


def smooth_skin(img, a, strength):
    base = cv2.bilateralFilter(img, 0, 28, 6)
    base = cv2.bilateralFilter(base, 0, 22, 4)
    detail = img.astype(np.float32) - cv2.GaussianBlur(img, (0, 0), 1.2).astype(np.float32)
    sm = base.astype(np.float32) + 0.35 * detail                # giữ lại vân da mịn, không bết như sáp
    k = a * strength
    return np.clip(img * (1 - k) + sm * k, 0, 255).astype(np.uint8)


def whiten_skin(img, a, white):
    """Da TRẮNG, KHÔNG VÀNG (chủ kênh 2026-10-20): trên vùng da — sáng thêm (L), bớt vàng (b*), bớt đỏ nhẹ (a*)."""
    if white <= 0:
        return img
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    k = a[..., 0] * white
    lab[..., 0] = lab[..., 0] + 14 * k * (1 - lab[..., 0] / 300)          # sáng thêm, vùng đã sáng thì thêm ít
    lab[..., 2] = 128 + (lab[..., 2] - 128) * (1 - 0.45 * k) - 2 * k      # vàng → trung tính
    lab[..., 1] = 128 + (lab[..., 1] - 128) * (1 - 0.15 * k)              # bớt đỏ nhẹ, vẫn hồng hào
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--mask", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--skin", type=float, default=0.6, help="độ mịn da 0–1")
    ap.add_argument("--white", type=float, default=0.6, help="làm trắng da, bớt vàng 0–1 (0 = tắt) — 0.6 cân bằng (chủ kênh chốt; 1.0 trắng quá)")
    ap.add_argument("--target", type=float, default=0.47, help="độ sáng trung bình mục tiêu (0–1)")
    a = ap.parse_args()
    W, H, fps = probe(a.video)

    # đo độ sáng trung bình (mẫu ~20 khung) → mức nâng sáng
    lum = [f.mean() / 255 for i, f in enumerate(frames(a.video, W, H, True)) if i % 15 == 0]
    mean = float(np.median(lum))
    gamma = float(np.clip(np.log(a.target) / np.log(max(mean, 0.05)), 0.80, 1.0))   # <1 = sáng hơn; không làm tối
    lift = 1 / gamma
    print(f"Độ sáng TB {mean:.2f} → gamma {lift:.2f}, mịn da {a.skin}")

    vf = ",".join([
        f"eq=gamma={lift:.3f}:contrast=1.05:saturation=1.03",              # tươi rất nhẹ — bão hòa cao làm da vàng
        "curves=master='0/0.025 0.25/0.235 0.5/0.52 0.75/0.79 1/0.985'",     # S mềm, đen không bết, trắng không cháy
        "colorbalance=rs=-0.01:bs=0.012:rh=-0.005:bh=0.01",               # TRUNG TÍNH hơi mát — KHÔNG làm ấm (da bị vàng)
        "unsharp=5:5:0.35:5:5:0",
        "vignette=angle=PI/6:mode=forward",
    ])
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{fps}",
                            "-i", "-", "-i", a.video, "-map", "0:v", "-map", "1:a?", "-c:a", "copy", "-vf", vf,
                            "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    for img, m in zip(frames(a.video, W, H, False), frames(a.mask, W, H, True)):
        am = skin_mask(img, m)
        enc.stdin.write(whiten_skin(smooth_skin(img, am, a.skin), am, a.white).tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"Xong → {a.out}")


if __name__ == "__main__":
    main()
