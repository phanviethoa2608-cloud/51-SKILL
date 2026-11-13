"""CHẾ ĐỘ VIDEO THÔ: áp dụng danh sách cắt (cuts.json = [[bắt đầu, kết thúc, ...], ...] giây) lên MỘT file video bất kỳ -> video đã cắt (.mp4),
chính xác từng khung hình, nối liền, KHÔNG sắp xếp lại. protected.json (tùy chọn) = [[bắt đầu, kết thúc, ghi chú], ...] đoạn demo/B-roll có sẵn: KHÔNG được cắt.
usage: python cut_video.py <video> <cuts.json> <out.mp4> [protected.json]
Mọi đoạn cắt chạm vùng bảo vệ bị thu nhỏ/bỏ. Xuất H.264 (libx264 crf 16) + AAC 256k, giữ nguyên độ phân giải & fps. Không bao giờ ghi đè file gốc."""
import json, os, subprocess, sys, tempfile
src, cuts_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
prot_p = sys.argv[4] if len(sys.argv) > 4 else None
if os.path.abspath(src) == os.path.abspath(out): sys.exit("từ chối ghi đè file gốc")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
fr = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", src]).decode().strip()
n, d = (fr.split("/") + ["1"])[:2]; fps = float(n) / float(d)
has_audio = bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", src], capture_output=True).stdout.strip())
snap = lambda t: round(t * fps) / fps
cuts = sorted([snap(max(0, c[0])), snap(min(dur, c[1]))] for c in json.load(open(cuts_p, encoding="utf-8")) if c[1] > c[0])
if prot_p:
    prot = [[snap(p[0]), snap(p[1])] for p in json.load(open(prot_p, encoding="utf-8"))]; res = []; shrunk = 0
    for c in cuts:
        parts = [c]
        for pa, pb in prot:
            parts = [x for (a, b) in parts for x in ([[a, b]] if (b <= pa or a >= pb) else [[a, min(b, pa)], [max(a, pb), b]]) if x[1] > x[0]]
        if parts != [c]: shrunk += 1
        res += parts
    cuts = sorted(res); print(f"protected: {len(prot)} vùng; {shrunk} đoạn cắt bị thu nhỏ/bỏ để không chạm demo/B-roll")
merged = []
for c in cuts:
    if merged and c[0] <= merged[-1][1] + 1e-6: merged[-1][1] = max(merged[-1][1], c[1])
    else: merged.append(list(c))
keep, cur = [], 0.0
for a, b in merged:
    if a - cur >= 1 / fps: keep.append((cur, a))
    cur = max(cur, b)
if dur - cur >= 1 / fps: keep.append((cur, dur))
if not keep: sys.exit("không còn đoạn nào để giữ")
lines = []
for i, (a, b) in enumerate(keep):
    lines.append(f"[0:v]trim=start={a:.5f}:end={b:.5f},setpts=PTS-STARTPTS[v{i}]")
    if has_audio: lines.append(f"[0:a:0]atrim=start={a:.5f}:end={b:.5f},asetpts=PTS-STARTPTS[a{i}]")
cat = "".join(f"[v{i}]" + (f"[a{i}]" if has_audio else "") for i in range(len(keep)))
lines.append(f"{cat}concat=n={len(keep)}:v=1:a={1 if has_audio else 0}[v]" + ("[a]" if has_audio else ""))
fd, fs = tempfile.mkstemp(suffix=".txt"); os.write(fd, ";\n".join(lines).encode()); os.close(fd)
help_ = subprocess.run(["ffmpeg", "-hide_banner", "-h", "full"], capture_output=True, text=True).stdout
FC = "-filter_complex_script" if "-filter_complex_script" in help_ else "-/filter_complex"   # ffmpeg cũ / mới (>=7)
cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, FC, fs, "-map", "[v]"] + (["-map", "[a]", "-c:a", "aac", "-b:a", "256k"] if has_audio else []) + \
      ["-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
subprocess.check_call(cmd); os.remove(fs)
newdur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out]))
print(f"OK: {dur:.1f}s -> {newdur:.1f}s (bỏ {dur-newdur:.1f}s, {len(keep)} đoạn giữ, {len(merged)} đoạn cắt) -> {out}")
