# Ghi chú kỹ thuật (đã kiểm chứng trên dự án Hermes)

## File Camtasia
- Dự án = thư mục `X.tscproj/` chứa `X.tscproj` (JSON, version 7.0) + media. **Mở file `.tscproj` bên trong.** Không ghi đè; tạo file mới `X-CAT.tscproj` cùng thư mục.
- Đơn vị thời gian: `editRate = 705600000` tick/giây; 30fps → 1 khung = 23.520.000 tick. Mọi `start/duration/mediaStart/mediaDuration` phải **chia hết cho 1 khung**.
- `timeline.sceneTrack.scenes[0].csml.tracks[]`: `medias[]`, `transitions[]`. Track 1 thường = cam (VMFile) + mic (AMFile); track 0 = màn hình (ScreenVMFile) + âm hệ thống; track 2+ = callout/slide người dùng chèn.
- `UnifiedMedia` = {video, audio} cùng `start/duration/mediaStart`. Cắt = nhân bản media, đổi `id` (mọi object có `id` số phải duy nhất), cập nhật `start` (ripple), `duration`, `mediaStart`, `mediaDuration` (cả cấp UnifiedMedia lẫn video/audio con).
- Tham số hữu ích (dùng ở giai đoạn dựng, KHÔNG đụng ở giai đoạn cắt): `AMFile.attributes.gain` (2.0 = 200%), `loudnessNormalization`, `ScreenVMFile.parameters.cursorScale` (3.5 = 350%), `cursorOpacity`.
- `cut_tscproj.js` đã kiểm tra: id duy nhất, không chồng lấp, căn khung, tổng thời lượng đúng. **Chưa được mở thử trong app Camtasia** → khi giao file cho người dùng phải nói rõ và nhờ họ báo nếu Camtasia không mở được.
- Transitions bị bỏ (tham chiếu id media cũ); raw project vừa quay không có.

## File .trec (thực chất là MP4 + hộp tùy biến)
- Luồng: video 0 = màn hình (codec `tscc2`, 1920x1080), video 1 = cam (h264 1280x720), audio 0 = **mic**, audio 1 = âm hệ thống (thường im).
- **Màn hình `tscc2` chỉ xuất khung khi nội dung đổi.** Sau khi tua `-ss`, khung đầu có thể đến trễ (0,7s) → nếu ghép lên nền sẽ thành **khung đen**. Cách sửa: tua sớm ≥3,2s (khoảng cách khung chốt 2,667s) rồi `fps=30:start_time=0,trim=start=M:duration=D,setpts=PTS-STARTPTS`.
- **Con trỏ chuột KHÔNG nằm trong khung hình.** Dữ liệu ở hộp `TSCM` cuối file (box size=1 → 64-bit; các chunk `DATA`): GUID `2b7b6af2` = bản ghi 16 byte `<double t, int32 x, int32 y>`, `t` = **giây tính từ đầu video** (âm = lúc đếm ngược 3s), x,y = pixel màn hình 1920x1080, theo sự kiện (có thể rất dày ~1 kHz); bản ghi cuối là rác (t rất âm). Vị trí tại thời điểm T = bản ghi cuối có t ≤ T (nội suy nếu cách < 0,1s). Đã xác nhận: tại giây 44,8 con trỏ đúng nút "+" mở tab mới. GUID `2b7b6af5` (16 byte `<double t, int a, int b>`) = sự kiện bấm (chưa phân loại chính xác). Đọc bằng `scripts/trec_cursor.py`.
- Vẽ con trỏ: sprite mũi tên đen viền trắng cao ≈ 66px (350%), đầu mũi tên đặt đúng (x,y); vẽ lên khung màn hình nguồn TRƯỚC khi zoom/thu nhỏ.

## Taskbar Windows
- Có hay không tùy từng file quay (quay vùng → không có; quay toàn màn hình → có, cao ~60px, đồng hồ/ngày ở góc phải dưới).
- Nhận diện bằng OCR đồng hồ/ngày ở vùng 520x110 góc phải dưới (`scripts/detect_taskbar.py`), bỏ phiếu trên 5 khung/file; có → **cắt 64px dưới đáy** của khung nguồn (không cắt khi file không có taskbar, tránh mất chân trang slide).

## Làm mờ riêng tư
- QR: `cv2.QRCodeDetector().detect` hoạt động (khung 1920x1080, ~0,4s). OCR: `rapidocr-onnxruntime` nhận đúng email (độ tin cậy 0,98).
- **OCR chậm trên CPU: ~7s/khung 1080p** (GPU onnxruntime không chạy được với CUDA 12 pip hiện có). Chạy **1 tiến trình**, lấy mẫu mỗi 3–4s, bỏ qua khung giống khung trước, chạy nền. Chạy 3 tiến trình song song làm chậm hơn (tranh CPU).
- Mẫu cần làm mờ: email, số điện thoại (`(0|\+84)\d{9,10}`), chuỗi dài ngẫu nhiên ≥20 ký tự lẫn chữ-số (API key/token/password), `sk-…`, bot token `\d{8,}:[\w-]{30,}`, IP, QR; ô password. Làm mờ bằng mosaic (pixelize) + blur để không khôi phục được; mở rộng khung 10px; giữ từ lúc xuất hiện đến lúc biến mất (+0,3s).

## Phát hiện lỗi hình
- `scan_blank.py`: khung "chết" = vùng cửa sổ màn hình gần đồng nhất VÀ tối (p95−p5 ≤ 12 và p95 < 60). `blackdetect` của ffmpeg báo sai với giao diện tối.
- `detect_taskswitch.py`: bảng Alt-Tab = vùng giữa màn hình xám trung tính rộng + viền xanh chọn cửa sổ. Trả về **ứng viên**, phải xem ảnh xác nhận (có thể nhầm cửa sổ hộp thoại).
