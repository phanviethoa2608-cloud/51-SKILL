"""Corrected-ish SRT on the FINAL timeline (kept speech only). ASR errors fixed via dictionary (not perfect)."""
import json, os, re
BASE = os.path.dirname(os.path.abspath(__file__))
units = json.load(open(os.path.join(BASE, "units.json"), encoding="utf-8"))
tr = json.load(open(os.path.join(BASE, "transcript.words.json"), encoding="utf-8"))
FIX = [
    (r"\bHermit Agent\b", "Hermes Agent"), (r"\bHermitAgent\b", "Hermes Agent"), (r"\bHermit\b", "Hermes"), (r"\bHermes eigen\b", "Hermes Agent"),
    (r"\bHerman Agent\b", "Hermes Agent"), (r"\bHerman\b", "Hermes"), (r"\bHomeAgent\b", "Hermes Agent"), (r"\bHelmet Agent\b", "Hermes Agent"),
    (r"\bHome Edition\b", "Hermes Agent"), (r"\bHome Advertising\b", "Hermes Agent"), (r"\bVBS\b", "VPS"), (r"\bOpen Router\b", "OpenRouter"),
    (r"mạng giảm giá", "mã giảm giá"), (r"mại giảm giá", "mã giảm giá"), (r"[Hh]òn tiền", "hoàn tiền"), (r"[Hh]ồn tiền", "hoàn tiền"),
    (r"mô đồ", "model"), (r"\bCloud Cowork\b", "Claude Cowork"), (r"\bCloud Core Work\b", "Claude Cowork"), (r"\bClaw\b", "Claude"),
    (r"\bDipsit\b|\bDipshift\b|\bDeepSeed\b", "DeepSeek"), (r"\bChassability\b", "ChatGPT"), (r"\bClawCode\b", "Claude Code"),
    (r"\bAPI Key\b", "API key"), (r"phòng mô tả", "phần mô tả"), (r"\bGetway\b|\bghét quay\b", "gateway"), (r"công hợp", "app"),
]


def fix(t):
    for a, b in FIX:
        t = re.sub(a, b, t)
    return t


def ts(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def to_final(m):
    for u in units:
        if u["m0"] - 1e-6 <= m < u["m1"] - 1e-6:
            return u["f0"] + (m - u["m0"])
    return None


out, n = [], 0
for s in tr:
    a, b = to_final(s["start"] + 0.01), to_final(max(s["start"] + 0.2, s["end"] - 0.05))
    if a is None or b is None or b - a < 0.3:
        continue
    n += 1
    out.append(f"{n}\n{ts(a)} --> {ts(b)}\n{fix(s['text'])}\n")
open(os.path.join(BASE, "phu-de.srt"), "w", encoding="utf-8").write("\n".join(out))
print(n, "subtitle lines")
