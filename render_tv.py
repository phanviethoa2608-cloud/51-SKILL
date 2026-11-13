"""Dựng bản hoàn thiện: đọc video xuất từ Camtasia (base) + transcript + events.json + protected.json + privacy.json
-> thêm phụ đề, thẻ minh họa, CTA, Like/Sub, làm mờ riêng tư. Đoạn PROTECTED đi qua nguyên vẹn (không vẽ gì).
usage: python render_tv.py out.mp4                       (cả video)
       python render_tv.py --stills 30,120,300 outdir     (xuất ảnh kiểm tra tại các mốc giây)
       python render_tv.py --range 100 130 out.mp4         (chỉ dựng đoạn thử)"""
import json, os, subprocess, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tvlib as L

BASE = os.path.dirname(os.path.abspath(__file__)); WK = os.path.join(BASE, "..", "work")
V = r"D:\EDIT VIDEO CLAUDE\VIEC-DANG-LAM\topview-ai-film-studio-2-huong-dan-0.mp4"
W, H, FPS = 1920, 1080, 30
PROT = [(a, b) for a, b, *_ in json.load(open(os.path.join(BASE, "..", "protected.json"), encoding="utf-8"))]
EV = json.load(open(os.path.join(WK, "events.json"), encoding="utf-8"))
PRIV = json.load(open(os.path.join(WK, "privacy.json"), encoding="utf-8")) if os.path.exists(os.path.join(WK, "privacy.json")) else []
words = json.load(open(os.path.join(WK, "words_fixed.json"), encoding="utf-8"))  # transcript đã rà tay (fix_transcript.py)
SUBS = json.load(open(os.path.join(WK, "subs.json"), encoding="utf-8"))   # phụ đề chọn lọc viết tay (subs_tv.py)
CARD_FN = {"stat": L.card_stat, "flow": L.card_flow, "list": L.card_list, "steps": L.card_steps, "ref": L.card_ref, "caption": L.card_caption,
           "timeline": L.card_timeline, "compare": L.card_compare}


def protected(t): return any(a - 0.001 <= t <= b + 0.001 for a, b in PROT)


def cam_rect(t):
    """Ô cam trong video nền, tính từ thông số Camtasia (scale/translation/crop của track cam): 4 giai đoạn."""
    if t < 100.7: x0, x1, y0, y1 = 14, 363, 645, 1066
    elif t < 129.8: x0, x1, y0, y1 = 1557, 1906, 640, 1061
    elif t < 791.0: x0, x1, y0, y1 = 1568, 1900, 640, 1061
    else: x0, x1, y0, y1 = 1526, 1900, 586, 1062
    return x0 - 3, y0 - 3, min(1920, x1 + 3), min(1080, y1 + 3)


CUR = json.load(open(os.path.join(WK, "cursor_track.json")))
CUR_T = [c[0] for c in CUR]
ZOOMS = [e for e in EV if e["kind"] == "zoom"]
import bisect


def smoother(x):
    x = min(1.0, max(0.0, x)); return x * x * x * (x * (x * 6 - 15) + 10)


def plan_zoom(z):
    """Chọn tâm CỐ ĐỊNH + mức zoom sao cho con trỏ (và vùng cần xem) luôn nằm trong khung; không theo con trỏ liên tục (tránh hoa mắt)."""
    i0 = bisect.bisect_left(CUR_T, z["t0"]); i1 = bisect.bisect_right(CUR_T, z["t0"] + z["dur"])
    pts = [(c[1], c[2]) for c in CUR[i0:i1] if c[1] < 1900 and c[2] < 1070]
    for bx in z.get("include", []): pts += [(bx[0], bx[1]), (bx[2], bx[3])]
    if not pts: z["zz"] = 0; return
    xs = np.array([p[0] for p in pts], float); ys = np.array([p[1] for p in pts], float)
    x0, x1 = (np.percentile(xs, 3), np.percentile(xs, 97)) if len(pts) > 20 else (xs.min(), xs.max())
    y0, y1 = (np.percentile(ys, 3), np.percentile(ys, 97)) if len(pts) > 20 else (ys.min(), ys.max())
    for bx in z.get("include", []): x0, y0, x1, y1 = min(x0, bx[0]), min(y0, bx[1]), max(x1, bx[2]), max(y1, bx[3])
    bw, bh = x1 - x0 + 200, y1 - y0 + 160
    zmax = min(0.94 * W / bw, 0.94 * H / bh)
    ze = min(z["z"], zmax)
    z["zz"] = ze if ze >= 1.12 else 0   # không vừa khung -> bỏ zoom thay vì cắt mất con trỏ
    z["c"] = ((x0 + x1) / 2, (y0 + y1) / 2)


for _z in ZOOMS: plan_zoom(_z)


def active_zoom(t):
    for z in ZOOMS:
        if z.get("zz") and z["t0"] <= t < z["t0"] + z["dur"]: return z
    return None


def zoom_amount(t):
    z = active_zoom(t)
    if not z: return 1.0
    lt = t - z["t0"]; a = min(smoother(lt / z.get("fi", 1.0)), smoother((z["dur"] - lt) / z.get("fo", 1.0)))
    return 1 + (z["zz"] - 1) * a


def zoom_center(t, z):
    return z["c"]


def apply_zoom(frame, t):
    z = zoom_amount(t)
    if z <= 1.001: return
    zz = active_zoom(t); orig = frame.copy(); cx, cy = zoom_center(t, zz)
    cw, ch = W / z, H / z
    x0 = min(max(cx - cw / 2, 0), W - cw); y0 = min(max(cy - ch / 2, 0), H - ch)
    M = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    frame[:] = cv2.warpAffine(remove_cam(orig, t), M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    paste_cam(frame, orig, t)


def remove_cam(img, t):
    """Xoá ô cam khỏi khung (inpaint độ phân giải thấp) để khi zoom không bị cam phóng to chồng lên cam gốc."""
    x0, y0, x1, y1 = cam_rect(t); pad = 24
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    reg = img[Y0:Y1, X0:X1]; sc = 4
    small = cv2.resize(reg, ((X1 - X0) // sc, (Y1 - Y0) // sc), interpolation=cv2.INTER_AREA)
    mk = np.zeros(small.shape[:2], np.uint8); mk[(y0 - Y0) // sc:(y1 - Y0) // sc + 1, (x0 - X0) // sc:(x1 - X0) // sc + 1] = 255
    inp = cv2.inpaint(small, mk, 4, cv2.INPAINT_TELEA)
    up = cv2.resize(inp, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_CUBIC)
    out = img.copy(); m = np.zeros((Y1 - Y0, X1 - X0), np.uint8); m[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = 255
    m = cv2.GaussianBlur(m, (0, 0), 3).astype(np.float32)[..., None] / 255
    out[Y0:Y1, X0:X1] = (up * m + reg * (1 - m)).astype(np.uint8)
    return out


TRANS = [e for e in EV if e["kind"] == "trans"]; _PREV = {}


def apply_trans(frame, t):
    for e in TRANS:
        if e["t0"] <= t < e["t0"] + e["dur"]:
            if e["t0"] not in _PREV: _PREV[e["t0"]] = grab(e["t0"] - 1 / FPS)
            p = smoother((t - e["t0"]) / e["dur"]); prev = _PREV[e["t0"]]
            sc = 1.0 + 0.045 * p
            M = np.float32([[sc, 0, W * (1 - sc) / 2], [0, sc, H * (1 - sc) / 2]])
            pv = cv2.warpAffine(prev, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            frame[:] = (pv.astype(np.float32) * (1 - p) + frame.astype(np.float32) * p).astype(np.uint8)
            return


def paste_cam(frame, orig, t):
    """Dán lại ô cam gốc NGUYÊN VẸN (mặt nạ bo góc đúng kích thước cam, không cắt viền) lên trên mọi lớp phủ."""
    x0, y0, x1, y1 = cam_rect(t); x0 += 3; y0 += 3; x1 -= 3; y1 -= 3
    w, h = x1 - x0, y1 - y0
    k = np.zeros((h, w), np.uint8); r = 20
    cv2.rectangle(k, (r, 0), (w - r - 1, h - 1), 255, -1); cv2.rectangle(k, (0, r), (w - 1, h - r - 1), 255, -1)
    for cx_, cy_ in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)): cv2.circle(k, (cx_, cy_), r, 255, -1)
    k = cv2.GaussianBlur(k, (0, 0), 1.0).astype(np.float32)[..., None] / 255
    frame[y0:y1, x0:x1] = (orig[y0:y1, x0:x1] * k + frame[y0:y1, x0:x1] * (1 - k)).astype(np.uint8)


def mosaic(frame, x0, y0, x1, y1):
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0: return
    roi = frame[y0:y1, x0:x1]
    sm = cv2.resize(roi, (max(2, (x1 - x0) // 14), max(2, (y1 - y0) // 14)), interpolation=cv2.INTER_AREA)
    mz = cv2.resize(sm, (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST)
    frame[y0:y1, x0:x1] = cv2.GaussianBlur(mz, (0, 0), 6)


TB_RANGES = [(150.2, 169.4)]   # taskbar Windows lộ trong video nền (dò bằng so khớp biểu tượng Start) -> che bằng dải phản chiếu mờ


def hide_taskbar(frame, t):
    if not any(a <= t <= b for a, b in TB_RANGES): return
    y0 = 1016
    keep = np.zeros((H - y0, W), bool)
    cx0, cy0, cx1, cy1 = cam_rect(t)
    keep[:max(0, cy1 - 4 - y0), cx0 + 4:cx1 - 4] = True     # không đụng ô cam (trừ mép dưới cam)
    sub = frame[y0:H]; sub[~keep] = (14, 14, 14)   # dải đen thay cho taskbar (như viền khung)


def composite(frame, t):
    """frame BGR (sửa tại chỗ). Trả về frame."""
    if protected(t): return frame
    orig = None
    hide_taskbar(frame, t)
    apply_trans(frame, t)
    hide_taskbar(frame, t)
    if not any(e["kind"] == "card" and e["t0"] <= t < e["t0"] + e["dur"] for e in EV):
        for e in EV:   # SKETCH vẽ trên khung gốc TRƯỚC zoom -> luôn bám đúng nút khi zoom (lỗi cũ: sketch lệch vị trí lúc đang zoom)
            if e["kind"] == "sketch" and e["t0"] <= t < e["t0"] + e["dur"]:
                lay, x, y = L.sketch_box(t - e["t0"], e["dur"], e["box"], e.get("label")); L.blend(frame, lay, x, y)
    apply_zoom(frame, t)
    # riêng tư
    for a, b, box in PRIV:
        if a <= t <= b: mosaic(frame, *box)
    card = next((e for e in EV if e["kind"] == "card" and e["t0"] <= t < e["t0"] + e["dur"]), None)
    if card:
        orig = frame.copy()
        bg = L.card_background(frame, t, card.get("bg", "dim"), L.fade_io(t - card["t0"], card["dur"], 0.3, 0.25))
        frame[:] = bg
        _cx0, _cy0, _cx1, _cy1 = cam_rect(t)
        L.CX = W // 2   # thẻ minh họa TOÀN MÀN HÌNH: căn GIỮA màn hình và đè lên cả talking head (yêu cầu người dùng)
        lay = CARD_FN[card["tpl"]](t - card["t0"], card["dur"], **card["args"])
        L.blend(frame, lay)
        # (không dán lại cam: thẻ toàn màn hình đè lên cả talking head)
    for e in EV:
        if e["kind"] in ("cta", "likesub") and e["t0"] <= t < e["t0"] + e["dur"]:
            lt = t - e["t0"]
            if e["kind"] == "cta": L.blend(frame, L.cta_card(lt, e["dur"], **e.get("args", {})))
            elif e["kind"] == "likesub":
                x, y = {"tr": (1320, 36), "tl": (40, 36)}[e["corner"]]
                im = L.likesub_video(lt)
                if im is not None: L.blend(frame, im, x, y)
    if not card:
        sb = next((x for x in SUBS if x["s"] <= t <= x["e"]), None)
        if sb:
            zz = active_zoom(t); sy = 930
            if zz and zoom_amount(t) > 1.02 and zz.get("c") and zz["c"][1] > 640: sy = 140  # zoom vùng dưới: đưa phụ đề lên trên
            _cx0, _cy0, _cx1, _cy1 = cam_rect(t)
            free = (_cx1 + 30, 1890) if _cx1 < 960 else (30, _cx0 - 30)   # vùng trống cạnh cam: chữ không bị cam che
            r = L.sub_layer(sb["text"], t, sb["s"], sb["e"], y=sy, free=free, mode=("top" if sy < 500 else "bottom"))
            if r:
                pre = frame.copy()
                L.blend(frame, r[0], r[1], r[2])
                paste_cam(frame, pre, t)    # lớp phủ nằm DƯỚI mặt/cam: dán lại cam gốc lên trên
    return frame


def grab(t):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", V, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(H, W, 3).copy()


def main():
    a = sys.argv[1:]
    if a and a[0] == "--stills":
        os.makedirs(a[2], exist_ok=True)
        for t in [float(x) for x in a[1].split(",")]:
            cv2.imwrite(os.path.join(a[2], f"s{t:07.2f}.png"), composite(grab(t), t))
        return
    # Khung nguồn k có pts = start_time + k/FPS (start_time của base = 1 khung). Chia theo CHỈ SỐ khung để không trùng/mất khung.
    st = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=start_time", "-of", "csv=p=0", V]))
    sd = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", V]))
    nframes = round(sd * FPS)
    i0, i1, out = 0, nframes, a[0]
    if a and a[0] == "--range": i0, i1, out = round(float(a[1]) * FPS), min(nframes, round(float(a[2]) * FPS)), a[3]
    count = i1 - i0
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{i0 / FPS + 0.01:.4f}", "-i", V, "-fps_mode", "passthrough", "-frames:v", str(count), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    enc = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-pix_fmt", "yuv420p", "-g", "30", "-bf", "0", "-movflags", "+faststart", out]
    ep = subprocess.Popen(enc, stdin=subprocess.PIPE)
    n = 0; nb = W * H * 3
    while n < count:
        buf = dec.stdout.read(nb)
        if len(buf) < nb: break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        t = (i0 + n + 1) / FPS   # pts của khung nguồn k = (k+1)/30 (start_time base = 1 khung); đã đo: -ss = k/30+0.01 cho đúng khung k (so với giải mã passthrough)
        ep.stdin.write(composite(fr, t).tobytes()); n += 1
        if n % 300 == 0: print(f"{t:.0f}s", flush=True)
    ep.stdin.close(); ep.wait(); dec.kill(); print("DONE", n, "of", count, "frames")


if __name__ == "__main__":
    main()
