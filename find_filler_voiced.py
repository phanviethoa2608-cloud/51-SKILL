"""Dò ầm/ừ/ờ mà Whisper không ghi thành chữ — CHỈ lấy âm có giọng ĐỨNG RIÊNG (an toàn).
Điều kiện: đoạn có giọng (> -44 dB) nằm ngoài mốc mọi từ, dài >= 0.2s, và CẢ HAI phía (trước/sau) đều có >= 0.1s im lặng
(< -50 dB) tách khỏi từ gần nhất. Đoạn dính liền với từ (đuôi từ, tên riêng/từ Whisper bỏ sót, câu chưa xong) -> KHÔNG cắt.
Bản cũ (không kiểm tra im lặng hai phía) từng cắt nhầm đuôi từ và tên model như 'OneBar, Minimax' -> đã bỏ.
usage: python find_filler_voiced.py  (trong thư mục làm việc có transcript.words.json, master_16k.wav, manual_cuts.json)"""
import json, os, wave, numpy as np
MINLEN = float(os.environ.get('FILL_MIN', 0.15))   # độ dài tối thiểu (s)
QSIDE = float(os.environ.get('FILL_QSIDE', 0.05))  # im lặng tối thiểu mỗi phía (s) để coi là đứng riêng
SOLO1 = float(os.environ.get('FILL_ONESIDE', 0.30)) # dính một phía: chỉ ghi ứng viên nếu dài >= giá trị này
t = json.load(open('transcript.words.json', encoding='utf-8'))
W = sorted((w['s'], w['e']) for s in t for w in s['words'])
w = wave.open('master_16k.wav'); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
n = len(a) // 160; db = 20 * np.log10(np.sqrt((a[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9)
cov = np.zeros(n, bool)
for s, e in W: cov[max(0, int((s - .06) * 100)):int((e + .06) * 100) + 1] = True
v = (db > -44) & ~cov
man = [m for m in json.load(open('manual_cuts.json', encoding='utf-8')) if m[2] != 'ầm ừ']
i = 0; added = 0; cands = []
while i < n:
    if v[i]:
        j = i
        while j < n and v[j]: j += 1
        s, e = i / 100, j / 100
        if e - s >= MINLEN:
            pe = max([x[1] for x in W if x[1] <= s + .06], default=0); ns = min([x[0] for x in W if x[0] >= e - .06], default=9999)
            lq = (db[int(pe * 100):i] < -50).sum() / 100 if i > int(pe * 100) else 0
            rq = (db[j:int(ns * 100)] < -50).sum() / 100 if int(ns * 100) > j else 0
            if lq >= QSIDE and rq >= QSIDE:
                man.append([round(s - .02, 2), round(e + .02, 2), 'ầm ừ', 'âm có giọng đứng riêng giữa hai khoảng lặng, không phải lời']); added += 1
            elif e - s >= SOLO1 and (lq >= QSIDE or rq >= QSIDE):
                cands.append([round(s - .02, 2), round(e + .02, 2), 'ầm ừ?', 'dính một phía với từ - phải xác minh (xem SKILL.md 2.0b)'])
        i = j
    else: i += 1
json.dump(man, open('manual_cuts.json', 'w', encoding='utf-8'), ensure_ascii=False)
json.dump(cands, open('filler_candidates.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(len(cands), 'ứng viên dính một phía -> filler_candidates.json (xác minh rồi mới đưa vào manual_cuts.json)')
print(added, 'đoạn ầm ừ đứng riêng đã thêm; tổng', len(man), 'dòng')
