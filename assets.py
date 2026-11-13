"""Static assets for the auto-edit style: background, masks, cam ring, overlay sprite renderers (Pillow)."""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np

W, H = 1920, 1080
BASE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(BASE, "assets")
os.makedirs(A, exist_ok=True)
_REPO_FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
FD = (_REPO_FONTS if os.path.exists(os.path.join(_REPO_FONTS, "Montserrat-ExtraBold.ttf")) else "C:/Windows/Fonts") + "/"
YELLOW = (246, 227, 72)
WHITE = (255, 255, 255)
NAVY = (23, 30, 55)

# screen window geometry (matches the sample style)
SX, SY, SW, SH = 96, 70, 1728, 972
CAM_D = 270          # outer ring diameter
CAM_CX, CAM_CY = 1752, 150
RING = 10


def font(size, weight="ExtraBold"):
    return ImageFont.truetype(FD + f"Montserrat-{weight}.ttf", size)


def rounded_mask(w, h, r):
    m = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], r * 2, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def circle_mask(d):
    m = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255)
    return m.resize((d, d), Image.LANCZOS)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient_ring(d, width, top, bottom, ang=90):
    """Circular ring with vertical-ish gradient and soft shadow; returns RGBA (d+pad)."""
    pad = 24
    S = d + pad * 2
    g = Image.new("RGB", (S, S))
    px = g.load()
    for y in range(S):
        c = lerp(top, bottom, y / (S - 1))
        for x in range(S):
            px[x, y] = c
    outer = Image.new("L", (S, S), 0)
    outer.paste(circle_mask(d), (pad, pad))
    inner = Image.new("L", (S, S), 0)
    inner.paste(circle_mask(d - 2 * width), (pad + width, pad + width))
    ring_a = ImageChops.subtract(outer, inner)
    # shadow
    sh = Image.new("L", (S, S), 0)
    sh.paste(outer.point(lambda v: int(v * 0.55)), (0, 6))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    black = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    out = Image.composite(black, out, sh)
    # shadow only outside of inner hole region is fine (cam covers hole)
    out.paste(g.convert("RGBA"), (0, 0), ring_a)
    return out, pad


def build_static():
    # background: dark navy gradient with subtle vignette
    bg = Image.new("RGB", (W, H))
    arr = np.zeros((H, W, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    t = (yy / H) * 0.6 + (xx / W) * 0.4
    c0 = np.array([14, 18, 36], dtype=np.float32)
    c1 = np.array([34, 24, 66], dtype=np.float32)
    arr = c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    arr *= (1.0 - 0.35 * np.clip(d - 0.4, 0, 1))[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(os.path.join(A, "bg.png"))

    # screen mask (rounded) + shadow plate (drawn into a bg-sized RGBA)
    rounded_mask(SW, SH, 28).save(os.path.join(A, "mask_screen.png"))
    pl = Image.new("L", (W, H), 0)
    pl.paste(rounded_mask(SW, SH, 28).point(lambda v: int(v * 0.6)), (SX, SY + 10))
    pl = pl.filter(ImageFilter.GaussianBlur(18))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 255)), shadow, pl)
    shadow.save(os.path.join(A, "screen_shadow.png"))

    # cam: ring (tim) + circle mask for the cam image
    inner_d = CAM_D - 2 * RING
    circle_mask(inner_d).save(os.path.join(A, "mask_cam.png"))
    ring, pad = gradient_ring(CAM_D, RING, (180, 138, 253), (110, 168, 254))
    ring.save(os.path.join(A, "ring.png"))
    with open(os.path.join(A, "ring.txt"), "w") as f:
        f.write(f"{pad}")
    # ring for black title cards (green-blue)
    ring2, _ = gradient_ring(CAM_D, RING, (120, 230, 190), (90, 170, 250))
    ring2.save(os.path.join(A, "ring_green.png"))


# ---------- text sprites ----------
def text_width(parts, f):
    return sum(f.getlength(t) for t, _ in parts)


def draw_parts(d, xy, parts, f, stroke=0):
    x, y = xy
    for t, col in parts:
        d.text((x, y), t, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0, 255) if stroke else None)
        x += f.getlength(t)


def parse_markup(s, base=WHITE):
    """'text **key** more' -> [(text,col)...] with **..** in yellow."""
    out, cur, hi = [], "", False
    i = 0
    while i < len(s):
        if s[i:i + 2] == "**":
            if cur:
                out.append((cur, YELLOW if hi else base))
            cur, hi = "", not hi
            i += 2
        else:
            cur += s[i]
            i += 1
    if cur:
        out.append((cur, YELLOW if hi else base))
    return out


def pill(markup, size=34, path=None, yellow_bg=False, icon=None):
    f = font(size, "ExtraBold" if not yellow_bg else "ExtraBold")
    parts = parse_markup(markup, (20, 20, 20) if yellow_bg else WHITE)
    if yellow_bg:
        parts = [(t, (20, 20, 20)) for t, _ in parts]
    tw = int(text_width(parts, f))
    padx, pady = 22, 12
    ih = int(size * 1.25)
    iw = (ih + 12) if icon else 0
    w, h = tw + padx * 2 + iw, ih + pady * 2
    sc = 2
    img = Image.new("RGBA", (w * sc, h * sc), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fill = YELLOW + (235,) if yellow_bg else (18, 20, 28, 190)
    d.rounded_rectangle([0, 0, w * sc - 1, h * sc - 1], 14 * sc, fill=fill)
    img = img.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    asc = f.getmetrics()[0]
    draw_parts(d, (padx + iw, pady + (ih - asc) // 2 - 4), parts, f)
    if icon:
        d.rounded_rectangle([padx - 4, pady + 2, padx - 4 + ih - 4, pady + ih - 2], 8, fill=icon)
    if path:
        img.save(path)
    return img


def lower_third(lines, size=56, path=None):
    """lines: list of markup strings; centered, big, with stroke/shadow. RGBA 1920 x h"""
    f = font(size, "ExtraBold")
    lh = int(size * 1.22)
    h = lh * len(lines) + 40
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    ds, d = ImageDraw.Draw(sh), ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        parts = parse_markup(ln.upper())
        tw = text_width(parts, f)
        x = (W - tw) / 2
        y = 16 + i * lh
        draw_parts(ds, (x + 3, y + 5), [(t, (0, 0, 0, 200)) for t, _ in parts], f)
        draw_parts(d, (x, y), parts, f, stroke=0)
    sh = sh.filter(ImageFilter.GaussianBlur(5))
    out = Image.alpha_composite(sh, img)
    if path:
        out.save(path)
    return out


def bottom_gradient(path, h=330, a=0.78):
    arr = np.zeros((h, W, 4), dtype=np.uint8)
    t = np.linspace(0, 1, h) ** 1.6
    arr[..., 3] = (t * 255 * a).astype(np.uint8)[:, None]
    Image.fromarray(arr, "RGBA").save(path)


def tag_topleft(markup, path, size=34):
    f = font(size, "ExtraBold")
    parts = parse_markup(markup)
    tw = int(text_width(parts, f))
    w, h = tw + 44, int(size * 1.25) + 18
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, 5, h - 1], 3, fill=YELLOW)
    draw_parts(d, (22, 4), parts, f)
    img.save(path)


def progress_bar(labels, active, path, size=30):
    f = font(size, "ExtraBold")
    items = []
    gap = 16
    for i, lab in enumerate(labels):
        on = (i == active)
        tw = int(f.getlength(lab))
        num_w = size + 22
        w = num_w + tw + 26 + 14
        items.append((w, lab, on, i + 1))
    total = sum(w for w, *_ in items) + gap * (len(items) - 1)
    h = size + 30
    img = Image.new("RGBA", (total, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 0
    for w, lab, on, n in items:
        bg = YELLOW + (255,) if on else NAVY + (225,)
        fg = (15, 15, 15) if on else (190, 198, 220)
        d.rounded_rectangle([x, 0, x + w - 1, h - 1], 14, fill=bg)
        nb = size + 6
        d.rounded_rectangle([x + 10, 10, x + 10 + nb, 10 + nb], 9, fill=(15, 15, 15) if on else (45, 55, 90))
        d.text((x + 10 + nb / 2, 10 + nb / 2), str(n), font=f, fill=YELLOW if on else (200, 205, 225), anchor="mm")
        d.text((x + 10 + nb + 12, h / 2), lab, font=f, fill=fg, anchor="lm")
        x += w + gap
    img.save(path)
    return img.size


def chapter_card(num, total, kicker, title_markup, path, grid=None):
    img = Image.new("RGBA", (W, H), (5, 5, 10, 255))
    if grid:
        g = Image.open(grid).convert("RGB").resize((W, H))
        g = Image.eval(g, lambda v: int(v * 0.18))
        img.paste(g, (0, 0))
    d = ImageDraw.Draw(img)
    fk = font(32, "ExtraBold")
    ft = font(96, "ExtraBold")
    # number chips
    chip = 64
    gap = 18
    tw = total * chip + (total - 1) * gap
    x0 = (W - tw) // 2
    for i in range(total):
        on = (i + 1 == num)
        x = x0 + i * (chip + gap)
        d.rounded_rectangle([x, 330, x + chip, 330 + chip], 14, fill=YELLOW if on else NAVY)
        d.text((x + chip / 2, 330 + chip / 2), str(i + 1), font=font(34, "ExtraBold"), fill=(15, 15, 15) if on else (190, 198, 220), anchor="mm")
    # kicker
    kt = " ".join(kicker.upper())
    d.text((W / 2, 440), kt, font=fk, fill=YELLOW, anchor="mm")
    d.rectangle([W / 2 - 160, 478, W / 2 + 160, 481], fill=YELLOW)
    parts = parse_markup(title_markup)
    # auto-shrink to fit
    size = 96
    while True:
        ft = font(size, "ExtraBold")
        tw = text_width(parts, ft)
        if tw < W - 240 or size < 48:
            break
        size -= 4
    draw_parts(d, ((W - tw) / 2, 540), parts, ft)
    img.save(path)


if __name__ == "__main__":
    build_static()
    print("static assets ok")
