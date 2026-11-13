"""Thư viện dựng lớp phủ vàng-đen (phụ đề, thẻ minh họa, animation) cho video 1920x1080@30.
Mọi hàm vẽ trả về ảnh RGBA (PIL) theo thời gian cục bộ t (giây) -> được trộn lên khung bởi render_tv.py.
Không đụng vào các đoạn protected (render_tv.py bỏ qua)."""
import math, os, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
GOLD = (255, 215, 0); WHITE = (255, 255, 255); BLACK = (11, 11, 11); GRAY = (184, 178, 160); CARD = (26, 26, 26)
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "edit-video-dai-youtube", "fonts")
ITALIC = [r"C:\Windows\Fonts\CormorantInfant-SemiBoldItalic.ttf", r"C:\Windows\Fonts\georgiaz.ttf"]
_fc = {}
CX = 900   # tâm ngang của nội dung thẻ minh họa (render_tv đặt theo vị trí cam để chữ không bị cam che)


def sans(size, bold="ExtraBold"):
    k = ("s", size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(os.path.join(REPO, f"Montserrat-{bold}.ttf"), size)
    return _fc[k]


def ital(size):
    """(giữ tên cũ) Người dùng muốn MỘT font duy nhất: từ nhấn đổi MÀU vàng, không đổi kiểu chữ."""
    return sans(size, "ExtraBold")


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def out_expo(x): x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)
def in_out(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def out_back(x, s=1.70158): x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def prog(t, t0, d): return clamp((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)


def fade_io(t, dur, fin=0.3, fout=0.25):
    return min(out_cubic(t / fin), out_cubic((dur - t) / fout)) if fin > 0 else 1.0


# ---------- helpers ----------
def new_layer(w=W, h=H): return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def text_w(txt, font): return font.getlength(txt)


def draw_runs(img, cx, cy, runs, alpha=1.0, shadow=True, anchor="mm"):
    """runs = [(text, font, color, alpha_i)] vẽ ngang, căn giữa tại (cx,cy). Trả về bbox."""
    parts = []
    tot = 0
    for r in runs:
        txt, font, col = r[0], r[1], r[2]; a = r[3] if len(r) > 3 else 1.0
        w = text_w(txt, font); parts.append((txt, font, col, a, w)); tot += w
    x = cx - tot / 2
    lay = new_layer(img.width, img.height)
    d = ImageDraw.Draw(lay)
    for txt, font, col, a, w in parts:
        if a > 0.01 and txt.strip():
            d.text((x, cy), txt, font=font, fill=col + (int(255 * a * alpha),), anchor="lm")
        x += w
    if shadow:
        bx = lay.getbbox()
        if bx:
            pad = 24
            c = (max(0, bx[0] - pad), max(0, bx[1] - pad), min(lay.width, bx[2] + pad), min(lay.height, bx[3] + pad))
            reg = lay.crop(c)
            sh = Image.new("RGBA", reg.size, (0, 0, 0, 0))
            sh.putalpha(reg.getchannel("A").point(lambda v: int(v * 0.65)))
            sh = sh.filter(ImageFilter.GaussianBlur(9))
            img.alpha_composite(sh, (c[0], c[1]))
    img.alpha_composite(lay)
    return (cx - tot / 2, cy, tot)


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def glow(layer, box_or_center, radius=40, color=GOLD, a=0.35):
    x, y, rx, ry = box_or_center
    pad = int(radius * 2.5)
    x0, y0 = int(max(0, x - rx - pad)), int(max(0, y - ry - pad)); x1, y1 = int(min(layer.width, x + rx + pad)), int(min(layer.height, y + ry + pad))
    if x1 <= x0 or y1 <= y0: return
    sc = 4
    w, h = max(1, (x1 - x0) // sc), max(1, (y1 - y0) // sc)
    g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse(((x - rx - x0) / sc, (y - ry - y0) / sc, (x + rx - x0) / sc, (y + ry - y0) / sc), fill=color + (int(255 * a),))
    g = g.filter(ImageFilter.GaussianBlur(max(1, radius / sc))).resize((x1 - x0, y1 - y0), Image.BILINEAR)
    layer.alpha_composite(g, (x0, y0))


# ---------- nền cho thẻ toàn màn hình ----------
_grid = None


def grid_bg():
    global _grid
    if _grid is None:
        im = np.zeros((H, W, 3), np.float32); im[:] = (11, 11, 11)
        yy, xx = np.mgrid[0:H, 0:W]
        vig = 1 - 0.55 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
        im *= vig[..., None]
        line = ((xx % 80 == 0) | (yy % 80 == 0)).astype(np.float32) * 0.05
        im += line[..., None] * np.array([255, 215, 0], np.float32)
        _grid = np.clip(im, 0, 255).astype(np.uint8)
    return _grid


def card_background(frame_bgr, t, mode="dim", amt=1.0):
    """Trả về nền (BGR uint8). mode 'dim' = làm tối+mờ khung gốc; 'solid' = nền đen lưới."""
    import cv2
    g = grid_bg()[..., ::-1]
    if mode == "solid":
        bg = g.copy()
    else:
        small = cv2.resize(frame_bgr, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), 3)
        big = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
        bg = (big.astype(np.float32) * 0.22 + g.astype(np.float32) * 0.85).clip(0, 255).astype(np.uint8)
    drift = int(t * 3) % 80
    bg = np.roll(bg, drift, axis=1) if mode == "solid" else bg
    if amt < 1.0:
        bg = (frame_bgr.astype(np.float32) * (1 - amt) + bg.astype(np.float32) * amt).astype(np.uint8)
    return bg


# ---------- icon ----------
def icon(d, kind, cx, cy, s, col=GOLD, a=255):
    c = col + (a,)
    w = max(3, int(s * 0.07))
    if kind == "eye":
        d.ellipse((cx - s, cy - s * 0.55, cx + s, cy + s * 0.55), outline=c, width=w)
        d.ellipse((cx - s * 0.3, cy - s * 0.3, cx + s * 0.3, cy + s * 0.3), outline=c, width=w)
        d.ellipse((cx - s * 0.1, cy - s * 0.1, cx + s * 0.1, cy + s * 0.1), fill=c)
    elif kind == "camera":
        rrect(d, (cx - s, cy - s * 0.6, cx + s * 0.35, cy + s * 0.6), int(s * 0.18), fill=c)
        d.polygon([(cx + s * 0.5, cy - s * 0.2), (cx + s, cy - s * 0.5), (cx + s, cy + s * 0.5), (cx + s * 0.5, cy + s * 0.2)], fill=c)
    elif kind == "doc":
        rrect(d, (cx - s * 0.65, cy - s, cx + s * 0.65, cy + s), int(s * 0.12), fill=(245, 245, 245, a))
        for i in range(3):
            d.line((cx - s * 0.35, cy - s * 0.35 + i * s * 0.35, cx + s * 0.35, cy - s * 0.35 + i * s * 0.35), fill=(40, 40, 40, a), width=w)
    elif kind == "folder":
        rrect(d, (cx - s, cy - s * 0.55, cx + s, cy + s * 0.7), int(s * 0.14), fill=c)
        rrect(d, (cx - s, cy - s * 0.8, cx - s * 0.1, cy - s * 0.4), int(s * 0.1), fill=c)
    elif kind == "gear":
        d.ellipse((cx - s * 0.7, cy - s * 0.7, cx + s * 0.7, cy + s * 0.7), outline=c, width=int(w * 2.2))
        for k in range(8):
            ang = k * math.pi / 4
            d.line((cx + math.cos(ang) * s * 0.7, cy + math.sin(ang) * s * 0.7, cx + math.cos(ang) * s, cy + math.sin(ang) * s), fill=c, width=int(w * 2))
        d.ellipse((cx - s * 0.25, cy - s * 0.25, cx + s * 0.25, cy + s * 0.25), outline=c, width=w)
    elif kind == "play":
        d.polygon([(cx - s * 0.5, cy - s * 0.7), (cx - s * 0.5, cy + s * 0.7), (cx + s * 0.7, cy)], fill=c)
    elif kind == "coin":
        for i in range(3):
            d.ellipse((cx - s * 0.8, cy + s * 0.35 - i * s * 0.3, cx + s * 0.8, cy + s * 0.8 - i * s * 0.3), fill=(255, 200, 0, a), outline=(160, 110, 0, a), width=w // 2 + 1)
    elif kind == "star":
        pts = []
        for k in range(10):
            r = s if k % 2 == 0 else s * 0.42; ang = -math.pi / 2 + k * math.pi / 5
            pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        d.polygon(pts, fill=c)
    elif kind == "bolt":
        d.polygon([(cx + s * 0.1, cy - s), (cx - s * 0.6, cy + s * 0.1), (cx - s * 0.05, cy + s * 0.1), (cx - s * 0.2, cy + s), (cx + s * 0.6, cy - s * 0.15), (cx + s * 0.05, cy - s * 0.15)], fill=c)
    elif kind == "user":
        d.ellipse((cx - s * 0.35, cy - s * 0.9, cx + s * 0.35, cy - s * 0.2), fill=c)
        d.pieslice((cx - s * 0.8, cy, cx + s * 0.8, cy + s * 1.6), 180, 360, fill=c)
    elif kind == "image":
        rrect(d, (cx - s, cy - s * 0.75, cx + s, cy + s * 0.75), int(s * 0.12), outline=c, width=w)
        d.polygon([(cx - s * 0.8, cy + s * 0.6), (cx - s * 0.2, cy - s * 0.1), (cx + s * 0.2, cy + s * 0.3), (cx + s * 0.45, cy + s * 0.05), (cx + s * 0.85, cy + s * 0.6)], fill=c)
        d.ellipse((cx + s * 0.35, cy - s * 0.5, cx + s * 0.6, cy - s * 0.25), fill=c)
    elif kind == "check":
        d.line((cx - s * 0.6, cy, cx - s * 0.15, cy + s * 0.5, cx + s * 0.7, cy - s * 0.5), fill=c, width=w * 2, joint="curve")
    elif kind == "arrow":
        d.line((cx - s, cy, cx + s * 0.6, cy), fill=c, width=w * 2)
        d.polygon([(cx + s * 0.4, cy - s * 0.4), (cx + s, cy), (cx + s * 0.4, cy + s * 0.4)], fill=c)
    elif kind == "claude":
        for k in range(12):
            ang = k * math.pi / 6
            d.line((cx + math.cos(ang) * s * 0.3, cy + math.sin(ang) * s * 0.3, cx + math.cos(ang) * s, cy + math.sin(ang) * s), fill=(217, 119, 87, a), width=int(w * 1.6))


# ---------- phụ đề ----------
STOP = set("và là của cho với các những một này đó thì mà ở trong khi sẽ đã đang được có không cũng như để từ ra vào lên rồi nhé nha ạ ơi thế nào gì ai cái chúng ta tôi mình bạn các hay hoặc nên nếu vì nó này kia đấy ừ ờ".split())


PROPER = set("topview film studio claude youtube tên_thương_hiệu builder seedance gpt-6 astra fable orbit qwen flash canvas style color click edit clip depth extraction core skill ultra chatgpt codex code agent ask ai upscale 3d 4k 2k credit storyboard snapshot enter camera preset prompt model mode workflow ugc".split())


def clean_word(w, first=False):
    w = w.strip().rstrip(",.;:")
    low = w.lower()
    if low in PROPER or any(c.isdigit() for c in w) or (sum(c.isupper() for c in w) >= 2):
        return {"topview": "Topview", "youtube": "YouTube", "claude": "Claude", "chatgpt": "ChatGPT", "ai": "AI", "3d": "3D", "ugc": "UGC", "gpt-6": "GPT-6"}.get(low, w if (w[:1].isupper() or any(c.isdigit() for c in w)) else w.capitalize() if low in ("phan", "đông", "giang", "film", "studio", "builder", "seedance", "astra", "fable", "orbit", "qwen", "flash", "canvas", "ultra", "codex") else w)
    return low


KEYS = [k.split() for k in [
    "kiểm soát", "tiết kiệm", "credit", "chi phí", "không giới hạn", "video nháp", "bản nháp", "chế độ nháp", "thế giới 3d", "film studio", "seedance 2.5",
    "topview ai", "upscale", "nâng cấp", "đạo diễn", "chỉnh sửa", "click to edit", "depth extraction", "core skill", "ultra", "miễn phí", "mô tả", "rẻ",
    "3d builder", "style", "camera", "storyboard", "snapshot", "prompt", "model", "chất lượng", "giảm", "tuyệt vời", "nhiều thời gian", "phim ai", "dựng phim",
    "tên_thương_hiệu", "youtube", "seedance", "không tốn", "một nửa", "365 ngày", "30 ngày", "67 phần trăm", "150 đô", "50 đô", "hơn 200", "đăng ký", "like", "bản nâng cấp", "plugin", "workflow"]]
DANGLING = set("của trong và là thì mà cho với các những một cái để ở từ như sẽ đã đang được của bạn nào hoặc nên vì".split())


def build_phrases(words, max_words=5, max_chars=34, gap=0.55):
    """words=[{w,s,e}] -> phrases [{s,e,words:[{w,s,e,emp}]}] (2-5 từ, ngắt theo khoảng lặng/dấu câu)."""
    ph, cur = [], []
    def flush():
        nonlocal cur
        if cur: ph.append({"s": cur[0]["s"], "e": cur[-1]["e"], "words": cur}); cur = []
    for i, w in enumerate(words):
        raw = w["w"].strip()
        if not raw: continue
        txt = clean_word(raw) + (raw[-1] if raw[-1] in ".!?…," else "")
        if cur and (w["s"] - cur[-1]["e"] > gap or len(cur) >= max_words or len(" ".join(x["w"].strip() for x in cur) + " " + txt) > max_chars):
            carry = []
            if w["s"] - cur[-1]["e"] <= gap and len(cur) > 2 and cur[-1]["w"].lower() in DANGLING: carry = [cur.pop()]
            flush(); cur = carry
        cur.append({"w": txt.rstrip(",.;:"), "s": w["s"], "e": w["e"], "emp": False})
        if re.search(r"[.!?…]$", txt) or (re.search(r"[,;:]$", txt) and len(cur) >= 3):
            flush()
    flush()
    # gộp cụm 1 từ vào cụm kế/trước nếu gần
    out = []
    for p in ph:
        if out and len(p["words"]) == 1 and p["s"] - out[-1]["e"] < 0.4 and len(out[-1]["words"]) < max_words:
            out[-1]["words"] += p["words"]; out[-1]["e"] = p["e"]
        else:
            out.append(p)
    # từ nhấn: cụm từ khóa (nhiều âm tiết) + số + từ mượn
    for p in out:
        toks = [re.sub(r"[^\w.]", "", x["w"].lower()) for x in p["words"]]
        k = 0
        while k < len(toks):
            hit = 0
            for key in KEYS:
                n = len(key)
                if toks[k:k + n] == key: hit = n; break
            if hit:
                for q in range(k, k + hit): p["words"][q]["emp"] = True
                k += hit
            else: k += 1
        for w in p["words"]:   # con số cũng là nội dung quan trọng
            if any(ch.isdigit() for ch in w["w"]): w["emp"] = True
    return out


def parse_marked(text):
    """'Bản **nâng cấp** mới' -> [(từ, nhấn?)]"""
    out = []
    for k, part in enumerate(re.split(r"\*\*", text)):
        for w in part.split():
            out.append((w, k % 2 == 1))
    return out


def sub_layer(text, t, s, e, y=930, size=50, free=(30, 1890), mode="bottom"):
    """Phụ đề: MỘT font (Montserrat Bold), từ quan trọng màu vàng, hiện ĐỦ cả cụm cùng lúc. Dấu câu dính từ trước; xuống dòng cân bằng.
    mode 'bottom': lớp phủ = GRADIENT đen nhẹ phủ 1/3 màn hình phía dưới (như ảnh mẫu của người dùng); mode 'top': dải bo mềm.
    Trả (layer, x, y_top) hoặc None. Lớp phủ nằm DƯỚI mặt/cam: render_tv dán lại cam gốc lên trên. free = vùng trống ngang cạnh cam."""
    if t < s or t > e: return None
    a_in = out_cubic((t - s) / 0.22); a_out = clamp((e - t) / 0.25); a = min(a_in, a_out)
    if a <= 0: return None
    f = sans(size, "Bold")
    toks = parse_marked(text)
    def tw_of(seq):
        w = 0.0
        for k, (tok, emp) in enumerate(seq):
            sp = 0 if (k + 1 >= len(seq) or seq[k + 1][0][0] in ",.;:?!") else text_w(" ", f)
            w += text_w(tok, f) + sp
        return w
    maxw = min(1180, free[1] - free[0] - 140)
    total = tw_of(toks)
    if total <= maxw: lines = [toks]
    else:
        best = None
        for k in range(1, len(toks)):
            if toks[k][0][0] in ",.;:?!": continue
            a_, b_ = tw_of(toks[:k]), tw_of(toks[k:]); sc = max(a_, b_)
            if best is None or sc < best[0]: best = (sc, k)
        k = best[1] if best else len(toks) // 2
        lines = [toks[:k], toks[k:]]
    lh = size * 1.32; th = int(lh * len(lines))
    wl = [tw_of(l) for l in lines]
    cx = (free[0] + free[1]) / 2; lift = (1 - a_in) * 10
    if mode == "bottom":
        gh = 360; gy = H - gh
        lay = new_layer(1920, gh)
        ys = np.linspace(0, 1, gh); al = (ys * ys * (3 - 2 * ys)) * 221 * a        # đen nhẹ, đậm dần xuống đáy
        gradient = np.zeros((gh, 1920, 4), np.uint8); gradient[..., 3] = al[:, None].astype(np.uint8)
        lay = Image.fromarray(gradient, "RGBA")
        yc = (y - gy) - th / 2 + lift
        for li, ln in enumerate(lines):
            runs = []
            for k, (tok, emp) in enumerate(ln):
                sp = "" if (k + 1 >= len(ln) or ln[k + 1][0][0] in ",.;:?!") else " "
                runs.append((tok + sp, f, GOLD if emp else WHITE, 1.0))
            draw_runs(lay, cx, yc + lh * (li + 0.5), runs, alpha=a, shadow=True)
        return lay, 0, gy
    hh = int(th + 56)
    lay = new_layer(1920, hh + 40)
    bw = min(free[1] - free[0], int(max(wl) + 170))
    band = new_layer(1920, hh + 40); bd = ImageDraw.Draw(band)
    rrect(bd, (cx - bw / 2, 20 + lift, cx + bw / 2, 20 + hh + lift), 34, fill=(0, 0, 0, int(142 * a)))
    band = band.filter(ImageFilter.GaussianBlur(5))
    lay.alpha_composite(band)
    for li, ln in enumerate(lines):
        runs = []
        for k, (tok, emp) in enumerate(ln):
            sp = "" if (k + 1 >= len(ln) or ln[k + 1][0][0] in ",.;:?!") else " "
            runs.append((tok + sp, f, GOLD if emp else WHITE, 1.0))
        draw_runs(lay, cx, 20 + 28 + lh * (li + 0.5) + lift, runs, alpha=a, shadow=True)
    return lay, 0, int(y - hh / 2 - 20)


# ---------- các mẫu thẻ toàn màn hình ----------
def _head(d, t, kicker=None, cy=0):
    pass


def card_stat(t, dur, kicker, number, unit, caption, sub=None, icon_kind="eye", count=True, fmt="{:,.0f}", start=0):
    """Thẻ số liệu: icon + KICKER + SỐ lớn (đếm tăng) + chữ serif nghiêng + nhãn phụ."""
    lay = new_layer(); d = ImageDraw.Draw(lay)
    A = fade_io(t, dur)
    pi = out_back(prog(t, 0.05, 0.5)); pk = out_cubic(prog(t, 0.25, 0.4)); pn = out_cubic(prog(t, 0.35, 0.5))
    pc = out_cubic(prog(t, 0.8, 0.45)); ps = out_cubic(prog(t, 1.05, 0.4))
    cx = (CX - 20)
    glow(lay, (cx, 330, 120, 40), 60, GOLD, 0.25 * pi * A)
    icon(d, icon_kind, cx, 300 - (1 - pi) * 30, 60 * max(pi, 0.01), GOLD, int(255 * pi * A))
    draw_runs(lay, cx, 400 - (1 - pk) * 14, [(kicker, sans(34, "SemiBold"), GRAY, pk)], alpha=A, shadow=False)
    val = number
    if count and isinstance(number, (int, float)):
        val = start + (number - start) * out_expo(prog(t, 0.35, 1.3))
        txt = fmt.format(val).replace(",", ".")
    else:
        txt = str(number)
    big = sans(230, "ExtraBold")
    runs = [(txt, big, GOLD, pn)]
    if unit: runs.append(("  " + unit, sans(80, "Bold"), WHITE, pn))
    draw_runs(lay, cx, 540 + (1 - pn) * 24, runs, alpha=A)
    draw_runs(lay, cx, 700 + (1 - pc) * 18, [(caption, ital(98), GOLD, pc)], alpha=A)
    if sub: draw_runs(lay, cx, 810 + (1 - ps) * 12, [(sub, sans(36, "SemiBold"), GRAY, ps)], alpha=A, shadow=False)
    return lay


def card_flow(t, dur, nodes, caption=None, cap_emp=None):
    """nodes=[(label, icon_kind)] nối bằng mũi tên vàng vẽ dần. Caption dưới (sans + serif nghiêng)."""
    lay = new_layer(); d = ImageDraw.Draw(lay); A = fade_io(t, dur)
    n = len(nodes); bw, bh = 330, 280; gapw = 170
    total = n * bw + (n - 1) * gapw; x0 = (CX - total / 2); cy = 430
    for i, (lab, ik) in enumerate(nodes):
        t0 = 0.15 + i * 0.75
        p = out_back(prog(t, t0, 0.5)); a = A * clamp(p)
        x = x0 + i * (bw + gapw); y = cy - (1 - clamp(p)) * -30
        sc = 0.9 + 0.1 * clamp(p)
        bx0, by0 = x + bw * (1 - sc) / 2, y - bh / 2 + bh * (1 - sc) / 2
        glow(lay, (x + bw / 2, y, 150, 90), 50, GOLD, 0.10 * a)
        rrect(d, (bx0, by0, bx0 + bw * sc, by0 + bh * sc), 26, fill=CARD + (int(235 * a),), outline=GOLD + (int(110 * a),), width=2)
        icon(d, ik, x + bw / 2, y - 25, 52 * sc, GOLD, int(255 * a))
        draw_runs(lay, x + bw / 2, y + 85, [(lab, sans(34, "Bold"), WHITE, a)], shadow=False)
        if i < n - 1:
            pa = out_cubic(prog(t, t0 + 0.45, 0.45))
            ax0, ax1 = x + bw + 22, x + bw + gapw - 22
            xe = ax0 + (ax1 - ax0) * pa
            if pa > 0.02:
                d.line((ax0, cy, xe, cy), fill=GOLD + (int(255 * A),), width=8)
                if pa > 0.9: d.polygon([(xe - 4, cy - 20), (xe + 22, cy), (xe - 4, cy + 20)], fill=GOLD + (int(255 * A),))
    if caption:
        pc = out_cubic(prog(t, 0.2 + n * 0.75, 0.5))
        runs = [(caption, sans(68), WHITE, pc)]
        if cap_emp: runs.append((" " + cap_emp, ital(82), GOLD, pc))
        draw_runs(lay, CX, 800 + (1 - pc) * 16, runs, alpha=A)
    return lay


def card_list(t, dur, title, items, caption=None, times=None):
    """Thẻ danh sách đánh số 1-2-3 (badge vàng), hiện lần lượt."""
    lay = new_layer(); d = ImageDraw.Draw(lay); A = fade_io(t, dur)
    pc = out_back(prog(t, 0.05, 0.5))
    bw, bh = 900, 130 + len(items) * 112
    x0, y0 = (CX - bw / 2), 190 + (1 - clamp(pc)) * 30
    rrect(d, (x0, y0, x0 + bw, y0 + bh), 30, fill=CARD + (int(240 * A * clamp(pc)),), outline=GOLD + (int(120 * A * clamp(pc)),), width=2)
    d.text((x0 + 56, y0 + 62), title.upper(), font=sans(30, "Bold"), fill=GRAY + (int(255 * A * clamp(pc)),), anchor="lm")
    for i, it in enumerate(items):
        p = out_back(prog(t, (times[i] if times else 0.5 + i * 0.7), 0.45)); a = A * clamp(p)
        y = y0 + 150 + i * 112 + (1 - clamp(p)) * 24
        d.ellipse((x0 + 56, y - 34, x0 + 124, y + 34), fill=GOLD + (int(255 * a),))
        d.text((x0 + 90, y), str(i + 1), font=sans(40), fill=BLACK + (int(255 * a),), anchor="mm")
        d.text((x0 + 160, y), it, font=sans(52, "Bold"), fill=WHITE + (int(255 * a),), anchor="lm")
    if caption:
        pcap = out_cubic(prog(t, 0.6 + len(items) * 0.7, 0.5))
        draw_runs(lay, CX, y0 + bh + 130, [(caption[0], sans(66), WHITE, pcap)] + ([(" " + caption[1], ital(80), GOLD, pcap)] if len(caption) > 1 else []), alpha=A)
    return lay


def card_steps(t, dur, label, win_title, items, caption=None, cap_emp=None, icon_kind=None, chip=None):
    """Thẻ CÁCH n: nhãn nhỏ + cửa sổ giả (3 chấm) + checklist tick + thanh tiến trình + caption lớn."""
    lay = new_layer(); d = ImageDraw.Draw(lay); A = fade_io(t, dur)
    pl = out_cubic(prog(t, 0.0, 0.4))
    draw_runs(lay, CX, 150, [(label.upper(), sans(34, "Bold"), GRAY, pl)], alpha=A, shadow=False)
    if icon_kind:
        pi = out_back(prog(t, 0.2, 0.5))
        icon(d, icon_kind, CX, 400 - (1 - clamp(pi)) * 20, 110 * max(pi, 0.01), GOLD, int(255 * A * clamp(pi)))
        if chip:
            pcp = out_cubic(prog(t, 0.7, 0.4))
            tw = text_w(chip, sans(36, "Bold")) + 100
            cx = CX
            rrect(d, (cx - tw / 2, 580, cx + tw / 2, 650), 22, fill=CARD + (int(235 * A * pcp),), outline=GOLD + (int(90 * A * pcp),), width=2)
            d.text((cx, 615), chip, font=sans(36, "Bold"), fill=WHITE + (int(255 * A * pcp),), anchor="mm")
    else:
        pw = out_back(prog(t, 0.15, 0.5)); a = A * clamp(pw)
        ww, wh = 900, 120 + len(items) * 70 + 40
        x0, y0 = (CX - ww / 2), 230 + (1 - clamp(pw)) * 24
        rrect(d, (x0, y0, x0 + ww, y0 + wh), 24, fill=CARD + (int(240 * a),), outline=GOLD + (int(100 * a),), width=2)
        for k, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse((x0 + 28 + k * 30, y0 + 24, x0 + 46 + k * 30, y0 + 42), fill=c + (int(255 * a),))
        d.text((x0 + 150, y0 + 33), win_title, font=sans(26, "SemiBold"), fill=GRAY + (int(255 * a),), anchor="lm")
        for i, it in enumerate(items):
            p = out_back(prog(t, 0.7 + i * 0.6, 0.4)); aa = A * clamp(p)
            y = y0 + 110 + i * 70
            icon(d, "check", x0 + 62, y, 20, GOLD, int(255 * aa))
            d.text((x0 + 105 + (1 - clamp(p)) * 18, y), it, font=sans(36, "Bold"), fill=WHITE + (int(255 * aa),), anchor="lm")
        pb = out_cubic(prog(t, 0.7, 0.7 + len(items) * 0.6))
        by = y0 + wh - 36
        rrect(d, (x0 + 40, by, x0 + ww - 40, by + 14), 7, fill=(60, 60, 60, int(255 * a)))
        if pb > 0.01: rrect(d, (x0 + 40, by, x0 + 40 + (ww - 80) * pb, by + 14), 7, fill=GOLD + (int(255 * a),))
    if caption:
        pc = out_cubic(prog(t, 0.9 + len(items) * 0.45, 0.5))
        runs = [(caption, sans(72), WHITE, pc)] + ([(" " + cap_emp, ital(86), GOLD, pc)] if cap_emp else [])
        draw_runs(lay, CX, 840 + (1 - pc) * 18, runs, alpha=A)
    return lay


def card_ref(t, dur, title, channel, badge=None, progress=0.4, kicker=None):
    """Thẻ tham chiếu video/bài: thẻ nổi + thanh tiến trình + badge vàng."""
    lay = new_layer(); d = ImageDraw.Draw(lay); A = fade_io(t, dur)
    p = out_back(prog(t, 0.05, 0.6)); a = A * clamp(p); sc = 0.92 + 0.08 * clamp(p)
    cw, ch = 1000 * sc, 560 * sc; x0, y0 = (CX - cw / 2), (H - ch) / 2 - 40
    glow(lay, (x0 + cw / 2, y0 + ch / 2, cw / 2, ch / 2), 60, GOLD, 0.08 * a)
    rrect(d, (x0, y0, x0 + cw, y0 + ch), 30, fill=CARD + (int(240 * a),), outline=GOLD + (int(110 * a),), width=2)
    rrect(d, (x0 + 4, y0 + 4, x0 + cw - 4, y0 + ch * 0.74), 26, fill=(20, 20, 20, int(255 * a)))
    icon(d, "play", CX, y0 + ch * 0.37, 70, GOLD, int(255 * a))
    pb = out_cubic(prog(t, 0.5, 1.2)) * progress
    by = y0 + ch * 0.74 - 22
    rrect(d, (x0 + 40, by, x0 + cw - 40, by + 10), 5, fill=(70, 70, 70, int(255 * a)))
    rrect(d, (x0 + 40, by, x0 + 40 + (cw - 80) * pb, by + 10), 5, fill=GOLD + (int(255 * a),))
    d.text((x0 + 44, y0 + ch * 0.82), title.upper(), font=sans(30, "Bold"), fill=WHITE + (int(255 * a),), anchor="lm")
    d.text((x0 + 44, y0 + ch * 0.92), channel, font=sans(26, "Medium"), fill=GRAY + (int(255 * a),), anchor="lm")
    if badge:
        pbd = out_back(prog(t, 0.6, 0.5)); tw = text_w(badge, sans(32, "Bold")) + 56
        bx1, by1 = x0 + cw + 24, y0 - 22
        rrect(d, (bx1 - tw, by1 - 30, bx1, by1 + 30), 30, fill=GOLD + (int(255 * A * clamp(pbd)),))
        d.text((bx1 - tw / 2, by1), badge, font=sans(32, "Bold"), fill=BLACK + (int(255 * A * clamp(pbd)),), anchor="mm")
    return lay


def card_caption(t, dur, line1, emp=None, sub=None):
    """Caption khổ lớn giữa màn hình (câu chốt): sans trắng + serif nghiêng vàng."""
    lay = new_layer(); A = fade_io(t, dur)
    p = out_cubic(prog(t, 0.05, 0.5)); p2 = out_cubic(prog(t, 0.3, 0.5))
    runs = [(line1, sans(92), WHITE, p)] + ([(" " + emp, ital(116), GOLD, p2)] if emp else [])
    draw_runs(lay, CX, 500 + (1 - p) * 24, runs, alpha=A)
    if sub:
        ps = out_cubic(prog(t, 0.7, 0.5))
        draw_runs(lay, CX, 640, [(sub, sans(40, "SemiBold"), GRAY, ps)], alpha=A, shadow=False)
    return lay


def card_timeline(t, dur, caption=None, cap_emp=None, title="timeline · đang tự dựng"):
    """Mô phỏng 'AI đang làm': các clip hiện dần theo track + playhead chạy."""
    lay = new_layer(); d = ImageDraw.Draw(lay); A = fade_io(t, dur)
    pw = out_back(prog(t, 0.05, 0.5)); a = A * clamp(pw)
    ww, wh = 1100, 420; x0, y0 = (CX - ww / 2), 220
    rrect(d, (x0, y0, x0 + ww, y0 + wh), 24, fill=CARD + (int(240 * a),), outline=GOLD + (int(100 * a),), width=2)
    for k, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse((x0 + 28 + k * 30, y0 + 24, x0 + 46 + k * 30, y0 + 42), fill=c + (int(255 * a),))
    d.text((x0 + 150, y0 + 33), title, font=sans(26, "SemiBold"), fill=GRAY + (int(255 * a),), anchor="lm")
    rows = [[(0, 160), (170, 90), (270, 220), (500, 130)], [(40, 130), (180, 80), (270, 170)], [(90, 90), (190, 120)]]
    cols = [GOLD, (230, 180, 40), (200, 140, 30)]
    n = 0
    for r, row in enumerate(rows):
        for (cx0, cw) in row:
            p = out_back(prog(t, 0.5 + n * 0.22, 0.35)); n += 1
            if p <= 0.02: continue
            xx = x0 + 50 + cx0 * 1.5; yy = y0 + 100 + r * 90
            rrect(d, (xx, yy, xx + cw * 1.5 * clamp(p), yy + 64), 12, fill=cols[r] + (int(235 * a),))
    ph = x0 + 50 + (ww - 140) * out_cubic(prog(t, 0.6, 2.6))
    d.line((ph, y0 + 80, ph, y0 + wh - 30), fill=WHITE + (int(255 * a),), width=5)
    if caption:
        pc = out_cubic(prog(t, 1.2, 0.5))
        runs = [(caption, sans(72), WHITE, pc)] + ([(" " + cap_emp, ital(86), GOLD, pc)] if cap_emp else [])
        draw_runs(lay, CX, 800 + (1 - pc) * 18, runs, alpha=A)
    return lay


# ---------- CTA & Like/Subscribe ----------
def cta_card(t, dur, text="Link ở phần mô tả", emp="phần mô tả"):
    lay = new_layer(); d = ImageDraw.Draw(lay); A = fade_io(t, dur, 0.35, 0.3)
    p = out_back(prog(t, 0, 0.5)); a = A * clamp(p)
    bounce = 8 * math.sin(t * 6)
    f = sans(46, "Bold"); w = text_w(text, f) + 150
    cx, cy = W // 2, 905 + (1 - clamp(p)) * 40
    rrect(d, (cx - w / 2, cy - 55, cx + w / 2, cy + 55), 55, fill=BLACK + (int(235 * a),), outline=GOLD + (int(255 * a),), width=3)
    d.text((cx - w / 2 + 40, cy), text, font=f, fill=WHITE + (int(255 * a),), anchor="lm")
    ax = cx + w / 2 - 60
    d.polygon([(ax - 18, cy - 12 + bounce), (ax + 18, cy - 12 + bounce), (ax, cy + 18 + bounce)], fill=GOLD + (int(255 * a),))
    return lay


def likesub(t, dur=5.2, corner="tr"):
    """Like -> Đăng ký (đổi trạng thái) -> chuông. Trả (layer nhỏ 560x150, x, y)."""
    lay = new_layer(620, 170); d = ImageDraw.Draw(lay); A = fade_io(t, dur, 0.3, 0.35)
    p = out_back(prog(t, 0, 0.5))
    rrect(d, (6, 10, 614, 160), 40, fill=BLACK + (int(235 * A * clamp(p)),), outline=GOLD + (int(255 * A * clamp(p)),), width=3)
    # like
    liked = t > 1.0; lp = out_back(prog(t, 1.0, 0.35)); s = 1 + 0.25 * math.sin(clamp(lp) * math.pi) if liked else 1
    col = GOLD if liked else WHITE
    d.rounded_rectangle((40, 80, 70 * s, 130), 6, fill=col + (int(255 * A),)) if False else None
    cx, cy = 75, 85
    d.polygon([(cx - 18 * s, cy - 2 * s), (cx - 18 * s, cy + 28 * s), (cx + 12 * s, cy + 28 * s), (cx + 26 * s, cy + 8 * s), (cx + 18 * s, cy - 6 * s), (cx + 4 * s, cy - 6 * s), (cx + 8 * s, cy - 26 * s), (cx - 4 * s, cy - 26 * s)], fill=col + (int(255 * A),))
    d.text((115, 85), "LIKE", font=sans(30, "Bold"), fill=col + (int(255 * A),), anchor="lm")
    # subscribe
    sp = out_back(prog(t, 2.0, 0.35)); subd = t > 2.3
    bx0, bx1 = 235, 520
    rrect(d, (bx0, 52, bx1, 118), 33, fill=((70, 70, 70) if subd else GOLD) + (int(255 * A),))
    d.text(((bx0 + bx1) / 2, 85), "ĐÃ ĐĂNG KÝ" if subd else "ĐĂNG KÝ", font=sans(26, "ExtraBold"), fill=(WHITE if subd else BLACK) + (int(255 * A),), anchor="mm")
    # bell
    bp = prog(t, 3.0, 1.2); ang = math.sin(bp * 18) * 14 * (1 - bp) if bp > 0 else 0
    bx, by = 565, 85
    if t > 3.0:
        bell = new_layer(70, 70); bd = ImageDraw.Draw(bell)
        bd.pieslice((15, 12, 55, 52), 180, 360, fill=GOLD + (255,)); bd.rectangle((15, 32, 55, 48), fill=GOLD + (255,)); bd.ellipse((29, 50, 41, 62), fill=GOLD + (255,))
        bell = bell.rotate(ang, resample=Image.BICUBIC, center=(35, 12))
        a_ = bell.getchannel("A").point(lambda v: int(v * A)); bell.putalpha(a_)
        lay.alpha_composite(bell, (bx - 35, by - 33))
    else:
        d.pieslice((bx - 20, by - 23, bx + 20, by + 17), 180, 360, fill=GRAY + (int(255 * A),)); d.rectangle((bx - 20, by - 3, bx + 20, by + 13), fill=GRAY + (int(255 * A),))
    return lay


def sketch_box(t, dur, box, label=None):
    """Khoanh vùng viền vàng vẽ dần + nền vàng nhạt. box=(x0,y0,x1,y1) tuyệt đối. Trả (layer,x,y) trùm vùng."""
    x0, y0, x1, y1 = [int(v) for v in box]; pad = 12
    lw = int(text_w(label, sans(30, 'Bold'))) + 40 if label else 0
    w, h = max(x1 - x0, lw) + 2 * pad, y1 - y0 + 2 * pad + 70
    bw_ = x1 - x0
    lay = new_layer(w, h); d = ImageDraw.Draw(lay); A = fade_io(t, dur, 0.2, 0.3)
    p = out_cubic(prog(t, 0, 0.6))
    d.rounded_rectangle((pad, pad + 0, pad + bw_, pad + (y1 - y0)), 14, fill=GOLD + (int(40 * A * p),))
    per = [(pad, pad), (pad + bw_, pad), (pad + bw_, pad + (y1 - y0)), (pad, pad + (y1 - y0)), (pad, pad)]
    tot = sum(math.dist(per[i], per[i + 1]) for i in range(4)); run = tot * p; acc = 0
    for i in range(4):
        L = math.dist(per[i], per[i + 1]); seg = clamp((run - acc) / L); acc += L
        if seg > 0:
            ex = per[i][0] + (per[i + 1][0] - per[i][0]) * seg; ey = per[i][1] + (per[i + 1][1] - per[i][1]) * seg
            d.line((per[i][0], per[i][1], ex, ey), fill=GOLD + (int(255 * A),), width=6)
    if label:
        pl = out_cubic(prog(t, 0.5, 0.4)); tw = text_w(label, sans(30, "Bold")) + 40
        rrect(d, (pad, pad + (y1 - y0) + 10, pad + tw, pad + (y1 - y0) + 62), 14, fill=GOLD + (int(255 * A * pl),))
        d.text((pad + 20, pad + (y1 - y0) + 36), label, font=sans(30, "Bold"), fill=BLACK + (int(255 * A * pl),), anchor="lm")
    return lay, x0 - pad, y0 - pad


# ---------- trộn ----------
def blend(frame, lay, x=0, y=0):
    """frame: numpy BGR uint8 (sửa tại chỗ). lay: PIL RGBA."""
    arr = np.asarray(lay)
    h, w = arr.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    sub = arr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = sub[..., 3:4].astype(np.float32) / 255.0
    if a.max() <= 0: return
    dst = frame[y0:y1, x0:x1].astype(np.float32)
    rgb = sub[..., 2::-1].astype(np.float32)
    frame[y0:y1, x0:x1] = (dst * (1 - a) + rgb * a).astype(np.uint8)


def card_compare(t, dur, left, right, caption=None, cap_emp=None):
    """So sánh 2 cột. left/right = (tiêu đề, [dòng...], nhãn_nhấn)  — cột phải viền vàng."""
    lay = new_layer(); d = ImageDraw.Draw(lay); A = fade_io(t, dur)
    cw, ch, gap = 640, 470, 70; x0 = (CX - (2 * cw + gap) / 2); y0 = 200
    for k, (title, lines, tag) in enumerate([left, right]):
        p = out_back(prog(t, 0.1 + k * 0.7, 0.5)); a = A * clamp(p)
        x = x0 + k * (cw + gap); y = y0 + (1 - clamp(p)) * 30
        rrect(d, (x, y, x + cw, y + ch), 28, fill=CARD + (int(240 * a),), outline=(GOLD if k else (90, 90, 90)) + (int(200 * a),), width=3 if k else 2)
        d.text((x + 40, y + 55), title.upper(), font=sans(28, "Bold"), fill=(GOLD if k else GRAY) + (int(255 * a),), anchor="lm")
        for i, ln in enumerate(lines):
            pl = out_cubic(prog(t, 0.35 + k * 0.7 + i * 0.25, 0.4))
            d.text((x + 40 + (1 - pl) * 16, y + 130 + i * 62), ln, font=sans(40, "Bold"), fill=WHITE + (int(255 * a * pl),), anchor="lm")
        if tag:
            pt = out_back(prog(t, 0.9 + k * 0.7, 0.4)); tw = text_w(tag, sans(30, "ExtraBold")) + 50
            rrect(d, (x + 40, y + ch - 90, x + 40 + tw, y + ch - 35), 26, fill=(GOLD if k else (70, 70, 70)) + (int(255 * a * clamp(pt)),))
            d.text((x + 40 + tw / 2, y + ch - 62), tag, font=sans(30, "ExtraBold"), fill=(BLACK if k else WHITE) + (int(255 * a * clamp(pt)),), anchor="mm")
    if caption:
        pc = out_cubic(prog(t, 1.9, 0.5))
        runs = [(caption, sans(68), WHITE, pc)] + ([(" " + cap_emp, ital(82), GOLD, pc)] if cap_emp else [])
        draw_runs(lay, CX, 800 + (1 - pc) * 16, runs, alpha=A)
    return lay


# ---------- Like/Subscribe từ video của người dùng (nền xanh đã key) ----------
_LS = {}
LS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work", "likesub")
LS_CROP = (250, 276, 1056, 480)


def likesub_video(lt, width=560):
    k = int(lt * 30) + 1
    if k < 1 or k > 243: return None
    if (k, width) not in _LS:
        if not os.path.exists(os.path.join(LS_DIR, f"f{k:04d}.png")):  # chưa có video Like+Subscribe riêng -> dùng bản vẽ sẵn
            r = likesub(lt, 8.0); return r[0] if isinstance(r, tuple) else r
        im = Image.open(os.path.join(LS_DIR, f"f{k:04d}.png")).convert("RGBA").crop(LS_CROP)
        h = int(im.height * width / im.width)
        _LS[(k, width)] = im.resize((width, h), Image.LANCZOS)
    im = _LS[(k, width)]
    a = clamp(lt / 0.25) * clamp((8.0 - lt) / 0.3)
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im
