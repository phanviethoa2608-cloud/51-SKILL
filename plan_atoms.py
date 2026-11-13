"""Intersect track-1 (camera+mic) clips with track-0 (screen) clips -> atoms with explicit sources.
master time = cumulative time of track-1 clips (gap in project removed)."""
import json, os
BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = "D:/EDIT VIDEO CLAUDE/VIEC-DANG-LAM/camtasia/huong-dan-chay-hermes-agent-vps-hostinger.tscproj"
tl = json.load(open(os.path.join(BASE, "timeline.json"), encoding="utf-8"))
segs = json.load(open(os.path.join(BASE, "segments.json"), encoding="utf-8"))
bin_ = {int(k): v for k, v in tl["bin"].items()}
FPS = 30


def fr(x):
    return round(x * FPS) / FPS


# screen sources on project timeline: list of (start,end,file,ms_at_start)
scr = []
raw = json.load(open(os.path.join(BASE, "timeline_groups.json"), encoding="utf-8")) if os.path.exists(os.path.join(BASE, "timeline_groups.json")) else {}
for c in tl["t0"]:
    if c["type"] == "UnifiedMedia" and c["vt"] == "ScreenVMFile":
        scr.append((c["start"], c["start"] + c["dur"], bin_[c["src"]], c["ms"] or 0))
    elif c["type"] == "VMFile":
        scr.append((c["start"], c["start"] + c["dur"], bin_[c["src"]], c["ms"] or 0))
    elif c["type"] == "Group":
        g = raw.get(f'{c["start"]:.2f}')
        if g:
            scr.append((c["start"], c["start"] + c["dur"], g["file"], g["ms"]))
scr.sort()

atoms = []
for s in segs:
    a0, a1 = s["projStart"], s["projStart"] + s["dur"]
    cuts = [a0, a1]
    for (ss, se, f, ms) in scr:
        if se > a0 + 1e-6 and ss < a1 - 1e-6:
            cuts += [max(ss, a0), min(se, a1)]
    cuts = sorted(set(round(x, 3) for x in cuts))
    for x0, x1 in zip(cuts[:-1], cuts[1:]):
        if x1 - x0 < 1e-3:
            continue
        mid = (x0 + x1) / 2
        sc = next(((f, ms + (x0 - ss)) for (ss, se, f, ms) in scr if ss <= mid < se), None)
        atoms.append({
            "mStart": round(s["masterStart"] + (x0 - a0), 3), "dur": round(x1 - x0, 3), "clip": s["i"],
            "cam": {"file": s["srcName"], "ms": round(s["ms"] + (x0 - a0), 3)},
            "screen": None if sc is None else {"file": sc[0], "ms": round(sc[1], 3)},
        })
json.dump(atoms, open(os.path.join(BASE, "atoms.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(atoms), "atoms;", sum(a["dur"] for a in atoms), "s;", sum(1 for a in atoms if a["screen"] is None), "cam-only atoms,",
      round(sum(a["dur"] for a in atoms if a["screen"] is None), 1), "s")
