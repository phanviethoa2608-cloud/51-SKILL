> **CẬP NHẬT 15/10/2026 (ghi đè mọi chỗ bên dưới nói về serif nghiêng / phụ đề toàn video / thẻ số liệu cho giá):** MỘT font Montserrat, từ quan trọng đổi màu vàng; phụ đề chọn lọc viết tay; thẻ toàn màn hình đè talking head và căn giữa; không dùng thẻ số liệu cho thứ đã có trên màn hình. Nguồn chuẩn: `SKILL.md` mục 4.11–4.12 và `references/checklist-kiem-tra-video.md`.

# Phong cách MOTION mẫu — bắt chước video "Giới thiệu hệ thống tự động edit video" (vàng-đen)

Nguồn: 5 khung hình người dùng gửi từ video mẫu (YouTube, 12:07). Bản này **giữ cấu trúc/chuyển động của video mẫu, đổi màu sang thương hiệu VÀNG–ĐEN** của Tên Thương Hiệu (video mẫu dùng xanh navy + xanh lam; KHÔNG dùng xanh).

## 0. Bảng màu (thay xanh → vàng)
| Vai trò | Video mẫu | Của mình |
|---|---|---|
| Nền cảnh toàn màn hình | navy `#0A1030` + lưới mờ | đen `#0B0B0B`→`#141414`, lưới/đường kẻ vàng rất mờ (alpha 4–6%), vignette tối ở góc |
| Nhấn chính (icon, số, chữ nghiêng, mũi tên, viền sáng) | xanh lam `#5BC8F0` | vàng `#FFD700` (glow `#FFD70055`) |
| Chữ chính | trắng | trắng `#FFFFFF` |
| Chữ phụ / nhãn nhỏ in hoa | xanh xám | xám ấm `#B8B2A0` |
| Thẻ/khung | navy bán trong suốt, viền sáng 1px | `#1A1A1A` alpha 85%, viền vàng alpha 25%, bo 24–28px |
| Thanh tiến trình / điểm nhấn thứ hai | đỏ/cam | cam-vàng `#F6A800` (chỉ khi cần tương phản) |

Logo bên thứ ba (Claude cam, v.v.) giữ nguyên màu gốc.

## 1. Phụ đề (khung 1) — CHỌN LỌC viết tay, MỘT font duy nhất (từ quan trọng màu vàng, KHÔNG serif nghiêng), 50px, lớp phủ gradient đen nhẹ 1/3 màn hình phía dưới, DƯỚI cam (cập nhật 15/10/2026 — ghi đè các mục cũ về font nghiêng bên dưới)
- **Burn-in** vào video (không chỉ xuất `.srt`). Vẫn xuất `.srt` kèm theo.
- Vị trí: **giữa-dưới**, cách mép dưới ~12% chiều cao; 1 dòng (tối đa 2), **2–5 từ mỗi cụm**, chữ **hiện theo từng từ/cụm đúng lúc nói** (word-timestamp từ Whisper).
- Font **kết hợp 2 kiểu trong cùng 1 dòng**:
  - Chữ thường: **Montserrat ExtraBold/Bold**, **trắng**, chữ thường (không in hoa), cỡ ~72–80px trên khung 1080p.
  - **Từ khóa/nhấn mạnh (1–2 từ mỗi cụm): chữ serif NGHIÊNG** — **Cormorant Infant SemiBold Italic** (có sẵn trong Windows, có dấu tiếng Việt, rất gần mẫu; dự phòng Georgia Italic; Playfair Display Italic cũng được nếu đã có), **vàng `#FFD700`**, cùng cỡ hoặc to hơn ~5%.
  - Ví dụ như khung mẫu: "tạo ra một" (sans trắng đậm) + "*hệ thống*" (serif nghiêng vàng).
- Bóng đổ mềm (blur ~12px, đen 60%) để đọc được trên mọi nền; không viền cứng, không nền hộp.
- Hiệu ứng: cụm mới **fade + trượt lên 12px, 0,15s**; cụm cũ biến mất trước khi cụm kế hiện; không để phụ đề treo quá ý (tắt ≤0,3s sau từ cuối).
- Chọn từ nhấn: danh từ/khái niệm chính, con số, tên công cụ, từ đối lập ("không", "tự động")… tối đa ~1/3 số từ.
- **Tránh đè**: không vẽ đè khung talking head dưới-phải (giới hạn chiều rộng phụ đề ≤ 1300px, căn giữa); khi có thẻ toàn màn hình đã có caption lớn riêng (khung 5) → nâng phụ đề lên hoặc ẩn.
- Vì phụ đề chiếm giữa-dưới: **pill/lower-third (mục 4.4) dời lên cao hơn** (≈ 18–22% từ đáy) hoặc bỏ; không chồng với phụ đề.

## 2. Cảnh minh họa TOÀN MÀN HÌNH (khung 2, 3, 4, 5)
Dùng cho **đoạn quan trọng cần nhấn mạnh hoặc cần minh họa** (con số, ví dụ, so sánh, quy trình, tham chiếu video/bài khác, tên công cụ). Chiếu toàn khung ~3–10s đúng lúc nói; **talking head vẫn hiện ở khung dọc dưới-phải**; phụ đề vẫn chạy (hoặc nhường chỗ cho caption lớn của thẻ).

Các mẫu (viết thành template tham số hóa, dữ liệu lấy từ lời nói/transcript, **không bịa số**):
1. **Thẻ SỐ LIỆU (khung 2)** — icon (mắt/tim/đồng hồ…) vàng phát sáng ở trên → nhãn nhỏ in hoa xám ("GẦN") → **SỐ rất lớn trắng, Montserrat ExtraBold ~260px, đếm tăng dần (count-up 1,2s, ease-out)** → chữ **serif nghiêng vàng** ("*lượt xem*") → nhãn phụ in hoa ("CHỈ TRONG 2 NGÀY").
2. **Thẻ THAM CHIẾU video/bài viết (khung 3)** — thẻ bo góc nổi ở giữa: ảnh thumbnail/logo + thanh tiến trình phát (chạy 0→~40%) + dòng tiêu đề in hoa + tên kênh xám; **badge nổi góc trên-phải** (pill vàng bo tròn, chữ đen, ví dụ "2 ngày"); thẻ vào bằng scale 0,92→1 + fade + blur→nét.
3. **SƠ ĐỒ LUỒNG (khung 4)** — các ô vuông bo góc (icon + nhãn đậm) nối bằng **mũi tên vàng vẽ dần (stroke-draw 0,4s)**; ô kế hiện sau khi mũi tên tới; mũi tên cuối đang vẽ dở = "đang chạy". Ví dụ: Video quay thô → Claude → Video hoàn chỉnh.
4. **THẺ CÁCH/BƯỚC có cửa sổ mô phỏng (khung 5)** — nhãn nhỏ in hoa ở trên ("CÁCH 1"), **cửa sổ giả (3 chấm đèn giao thông + tiêu đề)** chứa **checklist tick lần lượt** (✓ pop + chữ xuất hiện từng dòng) và **thanh tiến trình đầy dần**; **caption lớn ở dưới** kiểu phụ đề (sans trắng đậm + *serif nghiêng vàng*: "tự build *từ đầu*").
5. Mẫu bổ sung cùng ngôn ngữ: **so sánh 2 cột (trước/sau, cách 1/cách 2)**, **danh sách logo/công cụ hiện lần lượt**, **bước 1-2-3 có thanh tiến trình**, **trích dẫn/định nghĩa** (chữ lớn + từ khóa serif nghiêng vàng).

Ngôn ngữ thị giác chung: nền đen + lưới mờ, thẻ kính mờ viền sáng, glow vàng nhẹ quanh phần tử đang nhấn, **một ý mỗi cảnh**, chữ ≥ 40px (đọc được trên điện thoại), căn giữa, nhiều khoảng thở. Slide minh họa mục 4.5 nay dùng chung phong cách này thay cho bản `#141414` cũ.

## 2b. BỔ SUNG từ video mẫu thứ 2 ("Claude Code - Tạo Skill Tự Động Edit Video YouTube", 1:36 clip, 1280x720)
Quan sát từ video đầy đủ (đã xem khung hình trực tiếp):
- **Nhịp cảnh:** talking head toàn khung (chỉ ở hook/chuyển ý, kênh mình vẫn theo 4.1) → cảnh màn hình/web **có talking head thu nhỏ nổi bên phải** → thẻ minh họa toàn màn hình (nền tối) → quay lại màn hình. Khung talking head là **hình chữ nhật bo góc ~24px, gần vuông/dọc, có bóng đổ, đè nhẹ lên mép nội dung**; **kênh mình giữ dưới-phải theo 4.1**.
- **Phụ đề cũng chạy TRÊN cảnh màn hình** (không chỉ trên talking head), cỡ lớn, giữa-dưới; khi nền sáng/nhiều chữ phải có bóng/gradient tối nhẹ ở đáy để đọc được. Có cả **caption khổ lớn ~100–110px** cho câu chốt (như "hiệu ứng mà *animation*") đặt giữa-dưới trên nền đã làm tối.
- **Làm tối/mờ nền (dim + blur nhẹ)** phía sau khi hiện thẻ minh họa đè lên màn hình thật, để thẻ nổi bật.
- **Thẻ số liệu có icon minh họa theo nghĩa** (xếp đồng xu cho tiền, mắt cho lượt xem…). Trong video mẫu số "200" đã là màu vàng + đơn vị "triệu" trắng nhỏ → **hợp luôn tông vàng của mình**: số lớn VÀNG `#FFD700`, đơn vị trắng, nhãn kicker in hoa phía trên ("BEN ĐANG TIẾT KIỆM" → "TÔI ĐANG TIẾT KIỆM"…).
- **Thẻ danh sách đánh số (nền sáng/kính, tiêu đề in hoa nhỏ "VIỆC CỦA BEN")**: các dòng 1-2-3 với badge số bo tròn, hiện lần lượt (pop). Ban đầu là thẻ trống rồi chữ điền vào. Của mình: thẻ `#1A1A1A`/đen, badge số vàng chữ đen.
- **Pill nhãn trạng thái đè lên màn hình**: pill góc trên-trái có chấm đỏ ("● VIDEO DO CLAUDE EDIT · 2 ngày trước"); pill viền + badge xanh lá "✓ Đã nhận" (đổi trạng thái);
- **Khoanh vùng (sketch):** hộp viền ĐỎ bo góc quanh vùng cần chú ý trên màn hình thật (mô tả video…). Của mình: hộp viền **vàng** (đỏ chỉ dùng khi cần cảnh báo), vẽ dần quanh vùng, tự tắt 2–4s.
- **Mô phỏng quá trình:** cửa sổ giả "timeline · đang tự dựng" — các clip (khối bo góc) xuất hiện dần theo track, playhead trắng chạy ngang; cửa sổ mini phát video "Claude đang edit 78%" + thanh tiến trình, rồi chữ "edit *100%*" (số % bằng serif nghiêng). Dùng để minh họa "AI đang làm tự động".
- **Thẻ CÁCH 1 / CÁCH 2 + icon:** nhãn "CÁCH n" nhỏ in hoa; giữa là icon lớn (tài liệu `prompt.md` / thư mục) hoặc cửa sổ checklist; chip phụ (vd. "🔊 Sound effects"); caption lớn có từ serif nghiêng ("sở hữu *hệ thống*", "tự build *từ đầu*").
- **Zoom/phóng trang web** vào vùng đang nói để chữ đọc được (đồng nhất với 4.2); khung talking head giữ nguyên khi zoom.
- **Sơ đồ quy trình dài** ("Từ footage thô đến bản cuối": các ô nối mũi tên nhiều hàng) khi cần giải thích pipeline — dựng bằng template sơ đồ luồng, hiện dần từng nhánh, phóng vào nhánh đang nói.

## 3. ANIMATION (khung 4, 5 — ĐẶC BIỆT QUAN TRỌNG)
Mọi phần tử **không bao giờ "bật" cứng**; luôn có chuyển động vào/ra. Bộ chuyển động chuẩn:
- **Vào:** fade + trượt 20–40px + scale 0,94→1, **easing spring/back.out (overshoot nhẹ)** hoặc expo.out; 0,35–0,6s.
- **Stagger:** danh sách/checklist/các ô hiện lần lượt cách 0,25–0,5s, **đúng lúc từ tương ứng được nói** (neo theo word-timestamp).
- **Vẽ nét:** mũi tên/đường nối vẽ dần (stroke-dashoffset); khung/vòng khoanh vẽ theo hình.
- **Đếm số:** count-up có easing; kết thúc "nảy" nhẹ + glow chớp.
- **Tick:** dấu ✓ pop (scale 0→1,2→1) kèm ánh sáng chớp ngắn.
- **Thanh tiến trình:** chạy mượt đến mức đích, đầu thanh phát sáng.
- **Chữ:** hiện từng từ (word-by-word) hoặc từng dòng mask-reveal; từ serif nghiêng vàng vào sau từ sans ~0,1s để "nhấn".
- **Nền:** lưới/hạt ánh sáng trôi cực chậm (2–4px/s), không gây rối; glow thở nhẹ.
- **Ra:** fade + trượt nhẹ ngược hướng vào, 0,25s; chuyển giữa 2 cảnh minh họa = cross-dissolve/blur ngắn 0,3s (không hiệu ứng lòe loẹt).
- **Âm thanh:** mỗi nhịp hiện có SFX nhẹ (whoosh/click/pop) từ âm thanh thật, mix −22…−18 LUFS dưới giọng nói.
- Nhịp độ bám lời nói; không dồn animation lúc người nói đang chỉ trên màn hình.

## 4. Cách dựng kỹ thuật (đề xuất)
- Mỗi cảnh toàn màn hình / lớp phủ = **một composition HTML + GSAP (timeline pause, seek được)**, render thành **mp4 toàn khung** (cảnh toàn màn hình) hoặc **webm/mov có alpha** (lớp phụ đề), 1920x1080@30fps; `compose.py` chèn theo mốc thời gian (như cơ chế `cards.json`). Có thể dùng skill **hyperframes** / **tech-explainer-motion** để dựng bộ template.
- Phụ đề: word-timestamp Whisper → JSON cụm/từ nhấn → render lớp alpha (hoặc PIL + overlay ffmpeg nếu cần nhanh).
- Quy trình quyết định: (1) gắn nhãn "nhấn mạnh/minh họa" cho câu có con số, so sánh, định nghĩa, quy trình, tham chiếu; (2) chọn mẫu mục 2; (3) điền dữ liệu từ lời nói; (4) gắn mốc theo word-timestamp; (5) dựng + kiểm tra khung hình.
- Mật độ: cảnh toàn màn hình tối đa ~1 cảnh/45–60s, mỗi cảnh ≤10s; không dựng chồng lên đoạn người dùng **đang trình chiếu thật** (giữ quy tắc 4.4).

## 5. Xung đột với quy tắc cũ (đã xử lý trong SKILL.md)
- Video mẫu dùng talking head toàn khung; **kênh mình vẫn giữ quy tắc 4.1** (không cam toàn màn hình) — chỉ bắt chước **phụ đề + cảnh minh họa + animation**.
- Quy tắc cũ "phụ đề không in vào video" **bị thay thế**: phụ đề burn-in là mặc định.
