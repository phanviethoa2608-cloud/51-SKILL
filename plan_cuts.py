"""Auto cut planner (master time).
Rules (from skill): keep LAST take of repeated sentences; only remove (never reorder/edit); compress long silences;
drop ghost segments (ASR hallucinations over silence). Writes cuts.json + cut-plan.md + speech.json (kept segments)."""
import json, os, re, wave, unicodedata
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
tr = json.load(open(os.path.join(BASE, "transcript.words.json"), encoding="utf-8"))
segs_proj = json.load(open(os.path.join(BASE, "segments.json"), encoding="utf-8"))

# ---- audio energy (10 ms frames) ----
w = wave.open(os.path.join(BASE, "master_16k.wav"))
sr = w.getframerate()
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
FR = int(sr * 0.01)
n = len(a) // FR
rms = np.sqrt((a[: n * FR].reshape(n, FR) ** 2).mean(axis=1) + 1e-12)
db = 20 * np.log10(rms + 1e-9)
T = n * 0.01
speech_ref = np.percentile(db, 90)
floor = np.percentile(db, 10)
print(f"audio {T:.1f}s  p90={speech_ref:.1f}dB  p10={floor:.1f}dB")
QUIET = floor + 0.35 * (speech_ref - floor)   # below => quiet frame
print("quiet threshold", round(QUIET, 1))


def seg_db(s, e):
    i, j = int(s * 100), max(int(e * 100), int(s * 100) + 1)
    return float(np.percentile(db[i:j], 75)) if j > i else -99.0


def norm(t):
    t = unicodedata.normalize("NFC", t.lower())
    return re.sub(r"[^\w\s]", " ", t).split()


def jac(a_, b_):
    A, B = set(a_), set(b_)
    return len(A & B) / max(1, len(A | B))


def prefix(a_, b_):
    k = 0
    for x, y in zip(a_, b_):
        if x != y:
            break
        k += 1
    return k


# ---- 1. ghost segments ----
segs = []
for i, s in enumerate(tr):
    d = seg_db(s["start"], s["end"])
    toks = norm(s["text"])
    ghost = d < QUIET + 1.0 or (s["end"] - s["start"]) < 0.15
    segs.append({"i": i, "s": s["start"], "e": s["end"], "text": s["text"], "toks": toks, "db": d, "ghost": ghost})
ghosts = [x for x in segs if x["ghost"]]
print("ghost segments:", len(ghosts), "of", len(segs))

# ---- 2. retakes: MANUAL list only (auto detection removed: it cut unique sentences) ----
remove_ranges = []
man = json.load(open(os.path.join(BASE, "manual_cuts.json"), encoding="utf-8"))
for m in man:
    remove_ranges.append((m[0], m[1], m[2], m[3]))

# ---- 2b. fillers / stutters / voiced non-words (conservative: function words only) ----
FILL = {"ờ", "ừ", "ừm", "ờm", "à", "hừm", "ơ", "ê", "um", "uh", "ừa", "ờa", "ầm", "ưm", "ừmm", "ờmm", "ừ ừ", "hừ", "hm", "hmm", "ớ", "ờơ", "ừơ", "ah", "er", "erm"}
# Người dùng yêu cầu CẮT LUÔN mọi ừm/ờ/à... (xem SKILL.md 2.0b) → các từ này bị cắt tự động, kể cả khi dính liền câu
FUNC = set("các bạn cái ở đây nha ha thì rồi mình sẽ là và của những này đó như được có một để cho với ra vào nó khi mà thế nè đã đang hãy ok ơi ạ nữa lại trong nhưng tuy nên chúng ta tôi".split())
W2 = [(x["w"].strip(), x["s"], x["e"]) for sg in tr for x in sg["words"]]
T2 = [re.sub(r"[^\w]", "", unicodedata.normalize("NFC", t.lower())) for t, _, _ in W2]
auto = 0
for i, (t, s0, e0) in enumerate(W2):
    if T2[i] in FILL:
        remove_ranges.append((s0 - 0.03, e0 + 0.03, "filler", t)); auto += 1
for i in range(len(W2) - 1):
    if T2[i] and T2[i] == T2[i + 1] and T2[i] in FUNC and W2[i + 1][1] - W2[i][2] < 0.5:
        remove_ranges.append((W2[i][1] - 0.02, W2[i + 1][1] - 0.02, "stutter", W2[i][0] + " " + W2[i + 1][0])); auto += 1
for n_ in (2, 3):
    for i in range(len(W2) - 2 * n_):
        a_, b_ = T2[i:i + n_], T2[i + n_:i + 2 * n_]
        if a_ == b_ and all(a_) and all(x in FUNC for x in a_) and W2[i + n_][1] - W2[i + n_ - 1][2] < 0.6:
            remove_ranges.append((W2[i][1] - 0.02, W2[i + n_][1] - 0.02, "stutter", " ".join(x[0] for x in W2[i:i + 2 * n_]))); auto += 1
for i in range(len(W2) - 1):
    g0, g1 = W2[i][2], W2[i + 1][1]
    if float(os.environ.get("VG_MIN", 0.35)) <= g1 - g0 <= 1.6:
        seg = db[int(g0 * 100) + 3:int(g1 * 100) - 3]
        if len(seg) > 5 and float((seg > QUIET + 6).mean()) > 0.6:
            remove_ranges.append((g0 + 0.1, g1 - 0.1, "voiced-gap(ầm ừ?)", f"{W2[i][0]} … {W2[i+1][0]}")); auto += 1
print("auto filler/stutter/voiced-gap candidates:", auto)

# ---- 3. build keep/remove using words ----
words = []
for s in tr:
    for w_ in s["words"]:
        words.append((w_["s"], w_["e"], s["start"]))
cuts = []
for (s0, e0, why, txt) in remove_ranges:
    cuts.append([s0, e0, why, txt])
for g in ghosts:
    cuts.append([g["s"], g["e"], "ghost-asr", g["text"][:100]])

# ---- 4. silence compression (gaps between speech) ----
removed = sorted([(c[0], c[1]) for c in cuts])


def is_removed(t):
    return any(a0 <= t < b0 for a0, b0 in removed)


kept_words = [(s0, e0) for (s0, e0, _) in words if not is_removed((s0 + e0) / 2)]
kept_words.sort()
GAP_KEEP = float(os.environ.get("GAP_KEEP", 1.8))
GAP_MIN = float(os.environ.get("GAP_MIN", 3.5))
LONG = float(os.environ.get("LONG", 8.0))               # long waits
LONG_KEEP = float(os.environ.get("LONG_KEEP", 2.5))
prev_end = 0.0
for (s0, e0) in kept_words:
    gap = s0 - prev_end
    if gap > GAP_MIN:
        keep = LONG_KEEP if gap > LONG else GAP_KEEP
        a0 = prev_end + keep * 0.5
        b0 = s0 - keep * 0.5
        if b0 - a0 > 0.4:
            cuts.append([a0, b0, "silence" if gap <= LONG else "long-wait", f"{gap:.1f}s gap"])
    prev_end = max(prev_end, e0)
# tail after last kept word
if T - prev_end > 3.0:
    cuts.append([prev_end + 1.5, T, "tail", "end silence"])
# head: leading silence
if kept_words and kept_words[0][0] > 1.0:
    cuts.append([0.0, max(0.0, kept_words[0][0] - 0.4), "head", "leading silence"])

# ---- 5. snap to quiet frames, merge ----
def snap(t, lo, hi):
    i0, i1 = max(0, int((t - lo) * 100)), min(n - 1, int((t + hi) * 100))
    seg = db[i0:i1 + 1]
    q = np.where(seg < QUIET)[0]
    if len(q) == 0:
        return t
    # nearest quiet frame to t
    k = q[np.argmin(np.abs((q + i0) * 0.01 - t))]
    return (i0 + k) * 0.01


cuts.sort()
snapped = []
for a0, b0, why, txt in cuts:
    sa, sb = snap(a0, 0.15, 0.15), snap(b0, 0.15, 0.15)
    sa = max(0.0, sa)
    sb = min(T, sb)
    if sb - sa < 0.15:
        continue
    snapped.append([round(sa, 3), round(sb, 3), why, txt])
merged = []
for c in sorted(snapped):
    if merged and c[0] <= merged[-1][1] + 0.05:
        merged[-1][1] = max(merged[-1][1], c[1])
        if c[2] not in merged[-1][2]:
            merged[-1][2] += "+" + c[2]
        merged[-1][3] = (merged[-1][3] + " || " + c[3])[:200]
    else:
        merged.append(c)

# do not cut inside the first 2 seconds (hook) ; ensure frame alignment later in render
cuts_final = [c for c in merged if c[1] - c[0] >= 0.15]
total_cut = sum(c[1] - c[0] for c in cuts_final)
json.dump([[c[0], c[1]] for c in cuts_final], open(os.path.join(BASE, "cuts.json"), "w"))
json.dump(cuts_final, open(os.path.join(BASE, "cuts.detail.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
with open(os.path.join(BASE, "cut-plan.md"), "w", encoding="utf-8") as f:
    f.write(f"# Kế hoạch cắt tự động\n\nTổng: {len(cuts_final)} đoạn bị bỏ, {total_cut:.0f}s ({total_cut/60:.1f} phút) trên {T:.0f}s ({T/60:.1f} phút) → còn {(T-total_cut)/60:.1f} phút.\n\n")
    f.write("Luật: giữ lần nói cuối khi nói lại; chỉ bỏ, không đảo/sửa lời; bỏ 'ảo giác' ASR ở đoạn im lặng; rút gọn khoảng lặng dài.\n\n")
    f.write("| # | master (s) | dài (s) | lý do | nội dung |\n|---|---|---|---|---|\n")
    for i, c in enumerate(cuts_final):
        f.write(f"| {i+1} | {c[0]:.1f}–{c[1]:.1f} | {c[1]-c[0]:.1f} | {c[2]} | {c[3].replace('|', '/')} |\n")
print(len(cuts_final), "cuts", round(total_cut), "s removed of", round(T), "->", round((T - total_cut) / 60, 1), "min")
from collections import Counter
cnt = Counter()
for c in cuts_final:
    for r in c[2].split("+"):
        cnt[r] += c[1] - c[0]
print({k: round(v) for k, v in cnt.items()})
