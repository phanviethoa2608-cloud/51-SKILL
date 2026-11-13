"""Dựng song song theo khúc rồi ghép: python render_all.py <out.mp4> [workers=6]. Âm thanh = bản gốc (-c copy), không đụng."""
import os, subprocess, sys, math, time
BASE = os.path.dirname(os.path.abspath(__file__)); WK = os.path.join(BASE, "..", "work", "chunks"); os.makedirs(WK, exist_ok=True)
V = r"D:\EDIT VIDEO CLAUDE\VIEC-DANG-LAM\topview-ai-film-studio-2-huong-dan-0.mp4"
out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 6
sd = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", V]))
ST = float(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=start_time", "-of", "csv=p=0", V]))
frames = round(sd * 30); per = math.ceil(frames / (N * 3)); jobs = []
for i in range(0, frames, per):
    jobs.append((i / 30, min(frames, i + per) / 30, os.path.join(WK, f"c{i // per:03d}.mp4")))
files = [j[2] for j in jobs]
py = os.path.join(BASE, "..", "venv", "Scripts", "python.exe"); env = dict(os.environ, VONLY="1", PYTHONIOENCODING="utf-8")
run = []; done = 0; t0 = time.time()
while jobs or run:
    while jobs and len(run) < N:
        a, b, f = jobs.pop(0); run.append((subprocess.Popen([py, os.path.join(BASE, "render_tv.py"), "--range", str(a), str(b), f], env=env, stdout=subprocess.DEVNULL), f))
    for r in list(run):
        if r[0].poll() is not None:
            if r[0].returncode: print("LỖI", r[1]); sys.exit(1)
            run.remove(r); done += 1; print(f"{done} khúc xong, {time.time()-t0:.0f}s", flush=True)
    time.sleep(2)
lst = os.path.join(WK, "list.txt"); open(lst, "w").write("\n".join("file '" + f.replace("\\", "/") + "'" for f in files))
import json
EVS = json.load(open(os.path.join(BASE, "..", "work", "events.json"), encoding="utf-8"))
LS = [e["t0"] for e in EVS if e["kind"] == "likesub"]
LSV = r"D:\TAI NGUYEN\YouTube Subscribe and Like button green.mp4"
tmp = os.path.join(WK, "video_only.mp4")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", tmp])
if LS:
    fc = "[1:a]aresample=44100,aformat=channel_layouts=stereo[base];[2:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.3,asplit=%d%s;" % (len(LS), "".join(f"[s{i}]" for i in range(len(LS))))
    fc += "".join(f"[s{i}]adelay={int(t * 1000)}|{int(t * 1000)}[d{i}];" for i, t in enumerate(LS))
    fc += "[base]" + "".join(f"[d{i}]" for i in range(len(LS))) + f"amix=inputs={len(LS) + 1}:normalize=0:duration=first[aout]"
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-itsoffset", f"{ST:.6f}", "-i", tmp, "-i", V, "-i", LSV, "-filter_complex", fc, "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out])
else:
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-itsoffset", f"{ST:.6f}", "-i", tmp, "-i", V, "-map", "0:v", "-map", "1:a", "-c", "copy", "-shortest", "-movflags", "+faststart", out])
print("DONE", out)
