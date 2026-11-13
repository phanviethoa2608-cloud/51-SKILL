> **CẬP NHẬT (quy tắc mới thay thế):** khung cam tròn/viền tím trong tài liệu này KHÔNG còn dùng - talking head là khung dọc bo góc, mặc định dưới-phải, không đổi chỗ; overlay ưu tiên giữa-dưới. Phần màu sắc, chữ, lower-third, thanh tiến trình vẫn dùng được.

# Phân tích video mẫu `video demo edit.mp4` (1920x1080, 30fps, 4:17)

Phương pháp: chụp 1 khung/2 giây (129 khung) + chụp full-res khung chính, đo pixel màu. Mốc thời gian dưới đây là xấp xỉ (±2s).

## Cấu trúc tổng thể (kiểu "demo màn hình + cam tròn")
Video nền là **quay màn hình** (Claude desktop, TikTok, Miro, Google Flow/Drive), người nói chỉ hiện ở **cam tròn góc trên phải** suốt video. Mọi overlay bám đúng lời nói.

| Mốc | Cảnh | Overlay / kỹ thuật |
|---|---|---|
| 0:00-0:12 | Màn hình Claude + TikTok kênh mẫu | Lower-third **"TẠO RA 1 CÔNG TY AI TOÀN NHÂN SỰ ẢO"** hiện dần theo từng cụm từ (đây là câu hook); pill dọc "Tạo ảnh / Làm video / Xây kênh / Đăng bài" hiện lần lượt ở bên phải |
| 0:12-0:26 | Phát video con ngựa… (TikTok) | Sub chân: "THƯỚC PHIM **TRIỆU VIEW**"; "Sáng mai thức dậy… video **đã xong · đang lên kênh**" |
| 0:26-0:50 | Miro "Hướng dẫn đầy đủ về Subagent" | Logo chip ChatGPT → Gemini → Claude xuất hiện lần lượt; sub "LÀM ĐƯỢC VIỆC CỦA **CẢ MỘT CÔNG TY**" |
| 0:50-1:10 | Miro | Tiêu đề lớn "TRONG VIDEO NÀY: **3 BƯỚC**" trên gradient đen đỉnh khung; thanh tiến trình 3 bước ở đáy (①②③) hiện từng bước theo lời |
| 1:10-1:55 | Video TikTok của chính tác giả (nested) | Tag góc trái "Video do **Claude AI** tự edit"; sub từng cụm trên ngực; pill phải "Tự thêm chữ / Tự zoom ra·vào / Chỉnh độ nét + bộ lọc"; **thẻ trắng "level 4 cuối cùng / Code" → "code web"** (card chữ-đỏ trên nền trắng, minh họa) với cross-dissolve |
| ~2:02 | **Thẻ đầu phần** (nền đen) | "1 2 3 / PHẦN 1 / Hiểu luồng AI làm việc" |
| 2:04-2:55 | Miro phóng to sơ đồ AI | Thanh tiến trình bước 1 sáng vàng; pill "Cách cũ: bạn ra lệnh **từng việc**" → "Mới: AI ra lệnh cho các AI khác"; sub "TẠO MÔI TRƯỜNG **ĐỂ AI LÀM VIỆC TRONG AI**" |
| 2:56-3:20 | Miro kết quả thực tế | Không overlay nhiều - để người xem đọc bảng |
| 3:20-3:40 | Claude chat → thao tác | Pill "Claude – bản tải về máy" → "Kênh mẫu muốn xây" → "Google Flow – tạo ảnh, video" → "Google Drive – căn nhà của AI" (xếp chồng) |
| 3:40-4:17 | Miro ghi chú | Pill dưới trái/phải: "Sub-agent = nhiều Agent làm cùng nhau", "MCP = cánh tay của AI", "…chạm vào các **ứng dụng** bên ngoài"; thẻ ghi chú Miro được gõ trực tiếp |

## Công thức lặp lại (dùng làm mẫu khi edit video mới)
1. **Cam tròn cố định** góc trên phải, viền gradient tím; cảnh title card dùng viền gradient xanh lục-xanh lam.
2. **Mỗi khái niệm mới → 1 pill/tag** (nền đen mờ, 1 từ khóa vàng). Pill xếp chồng theo thời gian, xóa cả cụm khi đổi ý/cảnh.
3. **Câu chốt/ý lớn → lower-third in hoa** 1-2 dòng ở đáy trên gradient tối, hiện từng cụm theo lời nói; 1-3 từ vàng.
4. **Danh sách tên (công cụ/logo) → chip dọc**, hiện lần lượt từng chip đúng lúc từ được nói.
5. **Phần/chương → title card** nền đen + thanh số 1-2-3; trong video, thanh tiến trình 3 pill ở đáy báo đang ở bước nào.
6. **Nội dung màn hình**: phóng đúng vùng đang nói (sơ đồ Miro phóng to), con trỏ chuột luôn thấy; không để chữ quá nhỏ.
7. **Chuyển cảnh**: cut hoặc cross-dissolve ngắn; không dùng hiệu ứng phức tạp.

## Màu và kích thước đo được
- Vàng nhấn: `#F6E348` (badge/số/từ khóa), vàng nhạt đường kẻ `#F6E77B`.
- Xanh than (nút chưa chọn): `#171E37`. Nền title card: gần đen `#050508`.
- Viền cam tròn: tím lavender `#B48AFD` / `#B783F9`, đáy `#8C88BC` (gradient dọc, tím sáng ở trên → xanh lam nhạt ở dưới).
- Cam tròn: ⌀≈270px, tâm ≈ (1752,150).
- Khung quay màn hình: x 96→1825, y 55→1025, bo góc ~28px, nền ngoài tối.
- Chữ pill ~34px đậm; lower-third ~54px; tiêu đề thẻ phần ~95px; số bước ~32px.

## Việc chưa đo được (cần hỏi/lấy thêm)
- Tên phông chính xác; easing/tốc độ từng hiệu ứng; âm lượng/âm thanh SFX (chưa phân tích âm thanh, không có bản ghi lời); tùy bản, hãy đối chiếu `video demo edit.mp4` khi dựng.
