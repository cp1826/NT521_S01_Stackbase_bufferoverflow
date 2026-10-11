# DỰ ÁN: STACK-BASED BUFFER OVERFLOW

> **Tài liệu bàn giao ngữ cảnh cho các cuộc trò chuyện tiếp theo**  
> Ngày lập kế hoạch: 11/10/2026  
> Thời lượng dự kiến: **5 ngày**  
> Định hướng: nghiên cứu lý thuyết, xây dựng lab, quan sát lỗi, đánh giá điều kiện khai thác và biện pháp phòng chống.

## 1. Thông tin dự án

- **Tên:** Stack-based Buffer Overflow.
- **Mô tả:** Phân tích lỗi ghi dữ liệu vượt quá kích thước vùng đệm trên stack, có thể làm thay đổi dữ liệu điều khiển hoặc luồng thực thi. Tập trung vào nguyên nhân, điều kiện khai thác và biện pháp bảo vệ.
- **Phạm vi:** Chương trình C/C++ nhỏ tự xây dựng; chạy trong Ubuntu VM được kiểm soát; mô phỏng ghi tràn, quan sát bằng debugger, kiểm tra công cụ phát hiện và sửa lỗi.
- **Mục tiêu:** (1) Giải thích nguyên nhân; (2) minh họa cách dữ liệu ghi tràn ảnh hưởng bộ nhớ Stack; (3) phân biệt crash, ghi đè dữ liệu và khả năng chuyển hướng luồng điều khiển; (4) đánh giá công cụ/cơ chế bảo vệ; (5) trình bày kết quả có bằng chứng.
- **Nguyên tắc:** Chỉ thực nghiệm với mã nguồn và hệ thống được phép kiểm thử. Không coi crash tự động đồng nghĩa với khả năng chiếm quyền điều khiển; không coi Stack Canary/ASLR/NX là cách sửa lỗi tận gốc.

## 2. Lịch trình tổng quan

| Ngày | Trọng tâm | Đầu ra bắt buộc |
|---|---|---|
| **1** | Nghiên cứu Stack, Stack Frame, CWE-121, nguyên nhân | Tài liệu lý thuyết 2–3 trang; sơ đồ Stack và cơ chế ghi tràn |
| **2** | Thiết lập Ubuntu VM và chương trình lỗi | Source C, test case và bằng chứng tái hiện lỗi |
| **3** | Dùng GDB quan sát bộ nhớ, phân tích điều kiện khai thác | Demo tác động lên biến trạng thái; ảnh/log debug và nhận xét |
| **4** | Secure coding và cơ chế bảo vệ | Bản sửa mã nguồn, thử nghiệm Stack Canary, bảng so sánh |
| **5** | Báo cáo, slide, diễn tập demo | Báo cáo 12–18 trang, slide 10–12 trang, mã nguồn và demo ổn định |

## 3. Kế hoạch chi tiết

### Ngày 1 — Lý thuyết và phạm vi

**Mục tiêu:** Giải thích được Stack-based Buffer Overflow bằng lời và sơ đồ.

- [ ] Nghiên cứu Stack, Stack Frame, biến cục bộ, tham số hàm.
- [ ] Tìm hiểu Stack Pointer (SP/RSP), Base/Frame Pointer (BP/RBP), Instruction Pointer (IP/RIP), Return Address.
- [ ] Nắm cơ chế ghi quá kích thước `char buffer[N]`, byte kết thúc chuỗi `\0`, undefined behavior.
- [ ] Phân biệt Stack-based và Heap-based Buffer Overflow; phân biệt lỗi tràn bộ đệm với Stack Exhaustion.
- [ ] Nghiên cứu MITRE **CWE-121**; các API thiếu kiểm soát kích thước như `strcpy()`, `gets()` và nhập `%s` không giới hạn.
- [ ] Viết mô hình **Source – Sink – Assumption**: dữ liệu không tin cậy → thao tác ghi → giả định kích thước không được xác thực.
- [ ] Vẽ sơ đồ stack frame trước/sau khi ghi tràn (chú thích sơ đồ mang tính minh họa, bố cục thực tế tùy kiến trúc và trình biên dịch).

**Đầu ra:** `docs/01_ly_thuyet.md`; 1–2 sơ đồ minh họa; bảng thuật ngữ.

### Ngày 2 — Thiết lập lab và tái hiện lỗ hổng

**Mục tiêu:** Có một chương trình C dễ đọc thể hiện lỗi ghi tràn và một tập test lặp lại được.

- [ ] Dùng **Ubuntu VM**, cài **GCC**, **GDB**, tùy chọn **pwndbg** và VS Code.
- [ ] Viết chương trình mẫu với bộ đệm nhỏ và thao tác sao chép không kiểm tra độ dài, chỉ dùng trong lab.
- [ ] Tạo ít nhất 3 test case: chuỗi vừa buffer, chuỗi ngắn hơn, chuỗi dài hơn; tính cả `\0` khi xác định kích thước.
- [ ] Biên dịch bản debug (`-g -O0`) và bản có **AddressSanitizer** (`-fsanitize=address`).
- [ ] Chạy từng test; lưu stdout/stderr, mã thoát, ảnh hoặc log của AddressSanitizer.
- [ ] Ghi rõ môi trường: OS, kiến trúc, bản GCC, câu lệnh build để tái lập.

**Đầu ra:** `src/vulnerable.c`, `tests/`, `evidence/day2/`, `docs/02_moi_truong_va_tai_hien.md`.

### Ngày 3 — Phân tích bộ nhớ và điều kiện khai thác

**Mục tiêu:** Dùng bằng chứng bộ nhớ giải thích tác động thực tế của lỗi.

- [ ] Đặt breakpoint trước thao tác sao chép và quan sát biến cục bộ bằng **GDB**.
- [ ] Kiểm tra bộ nhớ trước/sau khi ghi, sử dụng lệnh debug phù hợp với kiến trúc.
- [ ] Xây dựng/quan sát một demo mô phỏng ghi tràn có thể thay đổi **biến trạng thái** trong lab; không giả định thứ tự bố trí biến luôn cố định.
- [ ] Giải thích khái niệm dữ liệu điều khiển như saved frame pointer/return address và các điều kiện khiến việc ghi tràn có thể ảnh hưởng tới chúng.
- [ ] Phân loại kết quả thực nghiệm: (a) phát hiện lỗi; (b) hỏng dữ liệu; (c) crash; (d) thay đổi luồng điều khiển nếu thực sự có bằng chứng. Không tuyên bố mức cao hơn bằng chứng.
- [ ] Chụp ảnh, lưu log GDB, chú thích địa chỉ và giá trị liên quan.

**Đầu ra:** `docs/03_phan_tich_bo_nho.md`, `evidence/day3/`, bản demo tác động lên dữ liệu.

### Ngày 4 — Phòng chống và kiểm chứng

**Mục tiêu:** So sánh các biện pháp giảm thiểu và cách sửa tận gốc.

- [ ] Sửa lỗi bằng giới hạn độ dài đầu vào/sao chép và xử lý chuỗi kết thúc null đúng cách.
- [ ] Viết `src/fixed.c` và kiểm thử cùng bộ dữ liệu từ ngày 2.
- [ ] Biên dịch, đánh giá với **Stack Canary** (`-fstack-protector-strong`) ở trường hợp phù hợp.
- [ ] Nghiên cứu vai trò của **NX/DEP, ASLR, PIE** và giới hạn của từng cơ chế; không nhất thiết thực hiện kỹ thuật vượt bảo vệ.
- [ ] Chạy **AddressSanitizer** với bản đã sửa để xác minh các test ca trước không còn báo lỗi tương ứng.
- [ ] Lập bảng so sánh bản lỗi / bản có cơ chế giảm thiểu / bản sửa triệt để: hành vi, bằng chứng, ưu điểm, giới hạn.

**Đầu ra:** `src/fixed.c`, `docs/04_phong_chong.md`, `evidence/day4/`, bảng đánh giá.

### Ngày 5 — Tổng hợp và trình bày

**Mục tiêu:** Bàn giao một dự án có thể trình diễn và được đánh giá độc lập.

- [ ] Viết báo cáo **12–18 trang**, có trích dẫn tài liệu và chứng cứ riêng của lab.
- [ ] Làm slide **10–12 trang**, ưu tiên sơ đồ và ảnh kết quả thay vì văn bản dài.
- [ ] Chuẩn bị kịch bản demo: chạy bản lỗi → chứng minh phát hiện/tràn → xem bộ nhớ → chạy bản sửa → so sánh.
- [ ] Kiểm tra chạy lại toàn bộ lệnh từ môi trường sạch hoặc snapshot VM.
- [ ] Chuẩn bị câu hỏi phản biện và trả lời: vì sao lỗi xảy ra, điều kiện thực sự khai thác, Stack Canary làm gì, ASLR/NX giải quyết gì, tại sao cần sửa source.
- [ ] Đóng gói source, test cases, log, hình minh họa, report, slide, README.

**Đầu ra:** `report/`, `slides/`, `README.md`, kịch bản demo và toàn bộ thư mục dự án.

## 4. Công cụ dự kiến

| Công cụ | Mục đích | Mức độ |
|---|---|---|
| Ubuntu VM | Môi trường thực nghiệm tách biệt | Cần |
| GCC | Biên dịch C, bật compiler protections | Cần |
| GDB | Quan sát biến, địa chỉ, Stack | Cần |
| AddressSanitizer | Phát hiện ghi ngoài giới hạn | Cần |
| VS Code | Viết mã và quản lý dự án | Khuyến nghị |
| pwndbg | Trực quan hóa debug trong GDB | Tùy chọn |
| Ghidra | Phân tích nhị phân | Nâng cao, không bắt buộc |

## 5. Ba demo trọng tâm

1. **Demo 1 — Tái hiện và phát hiện:** Chạy chương trình C chứa buffer 8 byte với chuỗi ngắn và chuỗi quá dài; dùng AddressSanitizer ghi nhận `stack-buffer-overflow` và vị trí lỗi.
2. **Demo 2 — Quan sát hậu quả:** Dùng GDB kiểm tra Stack và demo tự tạo để cho thấy dữ liệu ngoài giới hạn có thể sửa một biến trạng thái; giải thích điều kiện mà overflow có thể ảnh hưởng Return Address, không kết luận vượt quá dữ liệu quan sát.
3. **Demo 3 — Phòng chống:** So sánh chương trình lỗi, bản bật Stack Canary và bản đã sửa code có kiểm tra kích thước; lưu kết quả để đối chiếu.

**Ưu tiên nếu thiếu thời gian:** Hoàn thiện Demo 1 và Demo 3 (bản sửa), cộng phần quan sát bộ nhớ tối thiểu của Demo 2. Không cần làm ROP hoặc vượt ASLR/NX trong phạm vi 5 ngày.

## 6. Dàn ý báo cáo

1. **Tổng quan:** Đề tài, lý do, mục tiêu và phạm vi.
2. **Cơ sở lý thuyết:** Stack/Stack Frame, buffer overflow, CWE-121.
3. **Phân tích lỗ hổng:** Source–Sink–Assumption, nguyên nhân, điều kiện và hậu quả.
4. **Thực nghiệm:** Setup, mã nguồn, test case, GDB/ASan, ảnh/log, giải thích kết quả.
5. **Phòng chống:** Sửa code, Stack Canary, ASLR, NX/DEP, PIE, so sánh thực nghiệm.
6. **Kết luận:** Kết quả đạt được, giới hạn, bài học và hướng phát triển.

## 7. Cấu trúc thư mục đề xuất

```text
stack-based-buffer-overflow/
├── README.md
├── src/
│   ├── vulnerable.c
│   └── fixed.c
├── tests/
├── docs/
│   ├── 01_ly_thuyet.md
│   ├── 02_moi_truong_va_tai_hien.md
│   ├── 03_phan_tich_bo_nho.md
│   └── 04_phong_chong.md
├── evidence/
│   ├── day2/
│   ├── day3/
│   └── day4/
├── report/
└── slides/
```

## 8. Checklist nghiệm thu

- [ ] Lý giải được nguyên nhân tràn bộ đệm trên Stack.
- [ ] Có sơ đồ Stack minh họa rõ ràng, lưu ý phụ thuộc trình biên dịch.
- [ ] Có mã nguồn lỗi và test case tái lập.
- [ ] Có bằng chứng AddressSanitizer hoặc tương đương về lỗi ghi ngoài giới hạn.
- [ ] Có ảnh/log GDB hỗ trợ phân tích bộ nhớ.
- [ ] Có demo chứng minh tác động thực tế trên dữ liệu trong lab.
- [ ] Có mã nguồn đã sửa và test xác minh.
- [ ] Có bảng phân biệt sửa lỗi gốc với compiler/runtime mitigations.
- [ ] Có báo cáo, slide và kịch bản demo hoạt động.

## 9. Tài liệu tham khảo

- MITRE CWE-121 — Stack-based Buffer Overflow: https://cwe.mitre.org/data/definitions/121.html
- GCC Instrumentation Options (AddressSanitizer, Stack Protector): https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html
- GDB Documentation: https://sourceware.org/gdb/documentation/

## 10. Hướng dẫn tiếp tục ở cuộc chat khác

Khi mở cuộc chat mới, tải lên file Markdown này và gửi:

> Tôi đang thực hiện dự án "Stack-based Buffer Overflow" theo kế hoạch 5 ngày trong file đính kèm. Hãy dùng file làm ngữ cảnh chính, hỗ trợ tôi thực hiện **Ngày [N]**, từng bước với lý thuyết, câu lệnh/mã nguồn thử nghiệm trong Ubuntu VM, cách kiểm chứng và các đầu ra cần lưu. Hãy phân biệt điều đã thực hiện với điều mới chỉ dự kiến; đừng tự giả định rằng tôi đã hoàn thành các công việc trước.

**Ghi chú trạng thái:** Đây là **kế hoạch dự kiến**, chưa xác nhận bất kỳ công việc nào đã được hoàn thành. Môi trường lab và tiến độ cần cập nhật trong các cuộc chat tiếp theo.
