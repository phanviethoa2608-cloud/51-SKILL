import os, sys, json, glob, time, site
base = os.path.dirname(os.path.abspath(__file__))
# make CUDA DLLs from pip packages discoverable
for sp in site.getsitepackages():
    for d in glob.glob(os.path.join(sp, "nvidia", "*", "bin")):
        os.add_dll_directory(d)
        os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]
from faster_whisper import WhisperModel

model_name = sys.argv[1] if len(sys.argv) > 1 else "large-v3"
t0 = time.time()
model = WhisperModel(model_name, device="cuda", compute_type="int8_float16")
print("model loaded", round(time.time() - t0, 1), flush=True)
prompt = "Hướng dẫn Topview AI Film Studio 2. Tên Thương Hiệu. 3D Builder, Seedance, Dreamina, ChatGPT, Claude, Topview, prompt, storyboard, video AI."
segs, info = model.transcribe(
    os.path.join(base, "..", "work", "audio_16k.wav"),
    language="vi", word_timestamps=True, vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=300),
    beam_size=5, initial_prompt=prompt, condition_on_previous_text=False,
)
out = []
for s in segs:
    out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(),
                "words": [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2), "p": round(w.probability, 2)} for w in (s.words or [])]})
    if len(out) % 20 == 0:
        print(f"{s.end:.0f}/{info.duration:.0f}s  {time.time()-t0:.0f}s elapsed", flush=True)
        json.dump(out, open(os.path.join(base, "..", "work", "transcript.words.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump(out, open(os.path.join(base, "..", "work", "transcript.words.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("DONE", round(time.time() - t0), "s", len(out), "segments", flush=True)
