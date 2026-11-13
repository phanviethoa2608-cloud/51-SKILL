#!/usr/bin/env python
"""BỘ YOUTUBE DÀI (16:9, 3-60 phút): bỏ khoảng lặng, âm thanh, màu, chuẩn 1080p, zoom thưa, chương, phụ đề, thumbnail, mô tả, QC.
  yt.py silence-cut <in> <out> [--min 0.7 --keep 0.2 --db -38]       cắt khoảng lặng dài (jump cut nhanh; vấp/lặp: dùng edit-video-toan-dien)
  yt.py chapters   <scenes.json> --out chapters.json [--min 60]       gợi ý chương (mốc đổi ý), đặt tên theo từ khoá -> Claude đặt lại
  yt.py thumbs     <video> --out DIR [--n 6] [--text "CHỮ"]           khung đẹp (nét, có mặt, sáng đủ) 1280x720 + chữ to
  yt.py meta       chapters.json --out meta.md [--title "..."]        khung mô tả YouTube: chương (00:00...), từ khoá, nguồn ảnh
  yt.py build      <video> --dir DIR [--style doi-thuong|sang|nhanh] [--chapter-min 60] [--no-silence-cut] [--name "Tên|Chức danh"]
Quy trình khuyến nghị: edit-video-toan-dien (cắt vấp/lặp) -> bo-youtube-dai build. Không đăng lên YouTube thay người dùng.
"""
import argparse, json, os, re, subprocess, sys, unicodedata
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SK = os.environ.get("SKILLS_AI") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = [sys.executable, "-I"]
STYLES = {"doi-thuong": dict(look="natural", zoom=1.10, density=4, skin=0.2), "sang": dict(look="natural", zoom=1.12, density=4, skin=0.3),
          "nhanh": dict(look="bright", zoom=1.2, density=2, skin=0.3)}
CUES = ["tiếp theo", "bây giờ", "phần tiếp", "thứ hai", "thứ nhất", "thứ ba", "cuối cùng", "tóm lại", "bước", "đầu tiên", "chuyển sang", "câu hỏi"]

def run(cmd, **k):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **k)

def step(name, script, args):
    print(f"\n=== {name} ===", flush=True)
    if subprocess.run(PY + [os.path.join(SK, script)] + args, text=True, encoding="utf-8", errors="replace").returncode:
        sys.exit(f"Bước '{name}' lỗi. Dừng.")

def ts(t, force_h=False):
    t = int(round(t)); h, m, s = t // 3600, t // 60 % 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if (h or force_h) else f"{m:02d}:{s:02d}"

# ---------- bỏ khoảng lặng ----------
def cmd_silence(src, out, mn, keep, db):
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).stdout)
    err = run(["ffmpeg", "-hide_banner", "-i", src, "-vn", "-af", f"silencedetect=n={db}dB:d={mn}", "-f", "null", "-"]).stderr
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]; en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    cuts = [(max(0, a) + keep, b - keep) for a, b in zip(st, en) if b - a > mn + 2 * keep - 0.01]  # chừa `keep` giây mỗi đầu để nhịp thở tự nhiên
    keep_iv, pos = [], 0.0
    for a, b in cuts:
        if a - pos > 0.3: keep_iv.append((pos, a))
        pos = b
    if dur - pos > 0.3: keep_iv.append((pos, dur))
    removed = dur - sum(b - a for a, b in keep_iv)
    if not cuts: print("Không có khoảng lặng đủ dài để cắt.");
    fc = "".join(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{i}];" for i, (a, b) in enumerate(keep_iv))
    fc += "".join(f"[v{i}][a{i}]" for i in range(len(keep_iv))) + f"concat=n={len(keep_iv)}:v=1:a=1[V][A]"
    script = out + ".filter.txt"; open(script, "w", encoding="utf-8").write(fc)
    r = run(["ffmpeg", "-v", "error", "-y", "-i", src, "-/filter_complex", script, "-map", "[V]", "-map", "[A]", "-c:v", "libx264", "-crf", "17", "-preset", "fast",
             "-c:a", "aac", "-b:a", "192k", out])
    os.remove(script)
    if r.returncode: sys.exit("ffmpeg lỗi:\n" + r.stderr[-1200:])
    print(f"Cắt {len(cuts)} khoảng lặng, bớt {removed:.1f}s ({removed / dur * 100:.0f}%) -> {out}. Mốc thời gian đã dịch: phân cảnh lại.")

# ---------- chương ----------
def norm(s):
    s = unicodedata.normalize("NFD", s.lower()); return "".join(c for c in s if unicodedata.category(c) != "Mn")

def cmd_chapters(scenes_json, out, mn):
    d = json.load(open(scenes_json, encoding="utf-8-sig")); sc = d["scenes"]; dur = d["info"]["duration"]
    starts = [0.0]
    for i, s in enumerate(sc[1:], 1):
        if s["start"] - starts[-1] < mn: continue
        cue = any(c in norm(s["text"][:60]) for c in map(norm, CUES)); gap = s["start"] - sc[i - 1]["end"] > 1.2
        if cue or gap or s["start"] - starts[-1] > mn * 2: starts.append(s["start"])
    starts = [t for t in starts if dur - t > 10]
    chs = []
    for k, a in enumerate(starts):
        b = starts[k + 1] if k + 1 < len(starts) else dur
        txt = " ".join(s["text"] for s in sc if s["start"] < b and s["end"] > a); words = [w for s in sc if s["start"] < b and s["end"] > a for w in s.get("keywords", [])]
        top = [w for w, _ in sorted({w: words.count(w) for w in words}.items(), key=lambda x: -x[1])[:3]]
        chs.append({"id": k + 1, "start": round(a, 1), "end": round(b, 1), "title": "Mở đầu" if k == 0 else (" ".join(top).capitalize() or f"Phần {k + 1}"), "text": txt[:140]})
    json.dump(chs, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(chs)} chương -> {out}" + ("  ⚠ YouTube cần ≥3 chương, mỗi chương ≥10s: hạ --min" if len(chs) < 3 else ""))
    for c in chs: print(f"  {ts(c['start'])}  {c['title']}   ({c['text'][:50]})")
    print("Tên chương là gợi ý từ từ khoá: hãy đặt lại cho rõ nghĩa (≤5 từ).")

# ---------- thumbnail ----------
def cmd_thumbs(video, out, n, text):
    import cv2, numpy as np
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(out, exist_ok=True)
    cap = cv2.VideoCapture(video); N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cas = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"); cand = []
    for k in range(60):
        i = int(N * (k + 0.5) / 60); cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, fr = cap.read()
        if not ok: continue
        g = cv2.cvtColor(cv2.resize(fr, (640, int(640 * fr.shape[0] / fr.shape[1]))), cv2.COLOR_BGR2GRAY)
        fs = cas.detectMultiScale(g, 1.1, 5, minSize=(60, 60)); face = max((w * h for _, _, w, h in fs), default=0) / g.size
        sharp = cv2.Laplacian(g, cv2.CV_64F).var(); luma = g.mean()
        score = min(sharp, 300) / 300 + (1.5 if 0.03 < face < 0.5 else 0) + (0.5 if 70 < luma < 190 else -0.5)
        cand.append((score, i / fps, fr))
    cap.release(); cand.sort(key=lambda c: -c[0]); chosen = []
    for s, t, fr in cand:
        if all(abs(t - c[1]) > 8 for c in chosen): chosen.append((s, t, fr))
        if len(chosen) >= n: break
    fp = os.path.join(SK, "edit-video-cao-cap", "fonts", "Inter-Black.ttf")
    for k, (s, t, fr) in enumerate(chosen, 1):
        h, w = fr.shape[:2]; tw, th = 1280, 720; r = max(tw / w, th / h)
        im = Image.fromarray(cv2.cvtColor(cv2.resize(fr, (int(w * r) + 1, int(h * r) + 1)), cv2.COLOR_BGR2RGB)); l, tp = (im.width - tw) // 2, (im.height - th) // 2
        im = im.crop((l, tp, l + tw, tp + th))
        if text:
            d = ImageDraw.Draw(im); f = ImageFont.truetype(fp if os.path.exists(fp) else r"C:\Windows\Fonts\arialbd.ttf", 96); lines, cur = [], ""
            for wd in text.split():
                if d.textlength((cur + " " + wd).strip(), font=f) <= 1100 or not cur: cur = (cur + " " + wd).strip()
                else: lines.append(cur); cur = wd
            lines.append(cur); y = 40
            for ln in lines:
                for dx, dy in ((-4, -4), (4, -4), (-4, 4), (4, 4), (0, 6)): d.text((40 + dx, y + dy), ln, font=f, fill=(0, 0, 0))
                d.text((40, y), ln, font=f, fill=(255, 214, 0)); y += 110
        p = os.path.join(out, f"thumb_{k}.jpg"); im.save(p, quality=92); print(f"  thumb_{k}.jpg  (giây {t:.0f}, điểm {s:.2f})")
    print("Chọn bằng mắt: mặt rõ, biểu cảm mạnh, chữ ≤5 từ đọc được khi thu nhỏ (thumbnail hiển thị rất nhỏ). Chữ không che mặt.")

# ---------- mô tả ----------
def cmd_meta(chapters_json, out, title):
    chs = json.load(open(chapters_json, encoding="utf-8-sig")); force_h = chs[-1]["end"] >= 3600
    lines = [f"# {title or '<<TIÊU ĐỀ>>'}", "", "## Mô tả (dán vào YouTube)", "", "<<2–3 câu tóm tắt giá trị video; đặt từ khoá chính trong câu đầu>>", "", "⏱ Mục lục"]
    lines += [f"{ts(c['start'], force_h)} {c['title']}" for c in chs]
    lines += ["", "🔗 Liên kết: <<điền>>", "", "📌 Nguồn hình/nhạc (nếu có): <<xem NGUON_ANH.txt>>", "", "#<<từ khoá 1>> #<<từ khoá 2>> #<<từ khoá 3>>"]
    open(out, "w", encoding="utf-8").write("\n".join(lines)); print("->", out, "(điền các mục <<…>>; chương đầu bắt buộc 00:00)")

# ---------- dựng trọn gói ----------
def cmd_build(video, d, style, chmin, no_sil, name):
    st = STYLES[style]; os.makedirs(d, exist_ok=True); cur = video
    if not no_sil:
        s0 = os.path.join(d, "s0_nosilence.mp4"); cmd_silence(cur, s0, 0.7, 0.2, -38); cur = s0
    sc = os.path.join(d, "scenes.json")
    if not os.path.exists(sc): step("1 Phân cảnh", "video-thu-thap-phan-canh/scripts/ingest.py", [cur, "--out", d, "--max", "25"])
    s1 = os.path.join(d, "s1_audio.mp4"); step("2 Âm thanh", "video-am-thanh/scripts/audio.py", ["master", cur, s1])
    s2 = os.path.join(d, "s2_color.mp4"); step("3 Màu", "video-mau-chat-luong/scripts/grade.py", [s1, s2, "--look", st["look"], "--auto-exposure", "--denoise", "--skin", str(st["skin"])])
    s3 = os.path.join(d, "s3_1080p.mp4"); step("4 Chuẩn 1920x1080", "video-xuat-ban-qc/scripts/export.py", ["fmt", s2, s3, "--ratio", "16:9", "--fit", "blur", "--crf", "17"])
    plan = os.path.join(d, "plan_fx.json"); step("5a Gợi ý zoom", "video-zoom-chuyen-canh/scripts/fx.py", ["auto", sc, plan, "--density", str(st["density"]), "--max", str(st["zoom"])])
    s4 = os.path.join(d, "s4_fx.mp4"); step("5b Zoom thưa", "video-zoom-chuyen-canh/scripts/fx.py", ["apply", s3, plan, s4])
    chj = os.path.join(d, "chapters.json"); cmd_chapters(sc, chj, chmin); chs = json.load(open(chj, encoding="utf-8-sig"))
    dur = json.load(open(sc, encoding="utf-8-sig"))["info"]["duration"]; items = []
    for c in chs[1:]:  # thẻ tên chương 3.5s ở đầu mỗi chương
        items.append({"type": "text", "text": f"PHẦN {c['id']}: {c['title'].upper()}", "t0": c["start"] + 0.3, "t1": min(c["start"] + 3.8, c["end"] - 0.5), "style": "pill", "slot": "top"})
    if name: items.append({"type": "lower", "text": name, "t0": 1.0, "t1": 5.5})
    ij = os.path.join(d, "items.json"); json.dump({"items": items}, open(ij, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    final = os.path.join(d, "final_youtube.mp4"); step("6 Thẻ chương + lower third", "video-minh-hoa-bo-cuc/scripts/overlay.py", ["render", s4, ij, final])
    step("7 Phụ đề SRT", "video-xuat-ban-qc/scripts/export.py", ["srt", os.path.join(d, "words.json"), os.path.join(d, "phude.srt"), "--max-words", "9"])
    cmd_thumbs(final, os.path.join(d, "thumbs"), 6, ""); cmd_meta(chj, os.path.join(d, "mota_youtube.md"), "")
    rc = subprocess.run(PY + [os.path.join(SK, "video-xuat-ban-qc/scripts/qc.py"), final, "--ratio", "16:9", "--snap", os.path.join(d, "qc"), "--json", os.path.join(d, "qc.json")]).returncode
    print(f"\nXong -> {final}\nGồm: phude.srt, mota_youtube.md (điền <<…>>), thumbs/ (chọn + thêm chữ bằng `thumbs --text`), chapters.json (đặt lại tên chương), qc/. Chưa nghe bằng tai.")
    sys.exit(rc)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest="c", required=True)
    p = sp.add_parser("silence-cut"); p.add_argument("src"); p.add_argument("out"); p.add_argument("--min", type=float, default=0.7); p.add_argument("--keep", type=float, default=0.2); p.add_argument("--db", type=float, default=-38)
    p = sp.add_parser("chapters"); p.add_argument("scenes"); p.add_argument("--out", required=True); p.add_argument("--min", type=float, default=60)
    p = sp.add_parser("thumbs"); p.add_argument("video"); p.add_argument("--out", required=True); p.add_argument("--n", type=int, default=6); p.add_argument("--text", default="")
    p = sp.add_parser("meta"); p.add_argument("chapters"); p.add_argument("--out", required=True); p.add_argument("--title", default="")
    p = sp.add_parser("build"); p.add_argument("video"); p.add_argument("--dir", required=True); p.add_argument("--style", default="doi-thuong", choices=STYLES)
    p.add_argument("--chapter-min", type=float, default=60); p.add_argument("--no-silence-cut", action="store_true"); p.add_argument("--name", default="")
    a = ap.parse_args()
    if a.c == "silence-cut": cmd_silence(a.src, a.out, a.min, a.keep, a.db)
    elif a.c == "chapters": cmd_chapters(a.scenes, a.out, a.min)
    elif a.c == "thumbs": cmd_thumbs(a.video, a.out, a.n, a.text)
    elif a.c == "meta": cmd_meta(a.chapters, a.out, a.title)
    else: cmd_build(os.path.abspath(a.video), os.path.abspath(a.dir), a.style, a.chapter_min, a.no_silence_cut, a.name)

if __name__ == "__main__":
    main()
