# Bằng chứng Ngày 2

Chưa có log thực nghiệm Ubuntu VM tại thời điểm chuẩn bị bộ lab.
Không dùng kết quả dự kiến trong hướng dẫn thay cho bằng chứng đã chạy.

Chạy `python3 tests/run_day2.py` trong Ubuntu VM để tạo thư mục theo thời gian UTC.
Mỗi lần chạy có bản source, checksum, môi trường, lệnh build, binary và 8 bộ log.
Mỗi bộ gồm input, command, stdout, stderr, exitcode; `summary.csv` tổng hợp kết quả.
`environment.json` có trường `vm_product` cần bổ sung thủ công.

Giữ nguyên stderr gốc. Mã âm trong log Python biểu thị tiến trình bị signal trên
Linux (ví dụ `-11` là SIGSEGV); Bash thường biểu diễn cùng signal bằng `128 + signal`.
Mã khác 0 hoặc chỉ có `AddressSanitizer:DEADLYSIGNAL` chưa đủ chứng minh lỗi cụ thể.
Đọc báo cáo `stack-buffer-overflow`, loại truy cập WRITE, call stack và đối tượng buffer.
