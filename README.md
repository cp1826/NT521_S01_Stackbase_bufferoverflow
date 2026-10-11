# NT521_S01_Stackbase_bufferoverflow

Mini seminar: Stack-based Buffer Overflow trong chương trình C tự xây dựng.

Kế hoạch tổng thể: [Kế hoạch 5 ngày](Ke_hoach_Stack_Based_Buffer_Overflow_5_ngay.md).
Thực hiện Ngày 2 theo [hướng dẫn từng bước](docs/02_moi_truong_va_tai_hien.md).

Môi trường do người học xác nhận: Ubuntu 24.04 trong VirtualBox, đã cài GCC/GDB.
Đã chuẩn bị source và test; chưa có bằng chứng thực nghiệm Ubuntu VM trong repo.

Trong Ubuntu VM, tại thư mục gốc của dự án:

```bash
python3 tests/run_day2.py
```

Script dùng Python standard library, build bản debug và ASan, chạy 4 ca cho
mỗi bản và ghi kết quả vào `evidence/day2/<thoi_gian_UTC>/`.
Đọc hướng dẫn trước khi dùng script để hiểu byte null, ranh giới buffer và cách
phân biệt kết quả dự kiến với kết quả quan sát. Chương trình C cố ý có lỗi cho lab.
