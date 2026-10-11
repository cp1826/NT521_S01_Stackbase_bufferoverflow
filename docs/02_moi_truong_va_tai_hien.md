# Ngày 2 — Môi trường và tái hiện Stack-based Buffer Overflow

## 1. Trạng thái thực hiện

- Người học xác nhận: đã có **Ubuntu 24.04 trên VirtualBox**, đã cài **GCC/GDB**.
- Đã chuẩn bị trong thư mục dự án: source, 4 test case, script thu thập log và hướng dẫn này.
- Chưa ghi nhận phiên bản GCC/GDB cụ thể, kiến trúc CPU hay kết quả chạy trong VM.
- Chưa xác nhận Ngày 1 đã hoàn thành. Phần lý thuyết dưới đây là kiến thức tối thiểu để làm Ngày 2.
- Các kết quả ở phần “dự kiến” là tiêu chí đối chiếu, không phải log thực nghiệm.

Mục tiêu hôm nay: chứng minh thao tác ghi vượt giới hạn của một buffer trên stack,
có đầu vào và bằng chứng tái lập. Quan sát biến trạng thái/GDB thuộc Ngày 3;
sửa code và so sánh Stack Canary thuộc Ngày 4.

## 2. Bước 1 — Kiểm tra môi trường và đưa dự án vào VM

Mở Terminal **bên trong Ubuntu**, chạy:

```bash
cat /etc/os-release
uname -m
gcc --version
gdb --version
python3 --version
```

Ghi nhận tên OS, phiên bản, kiến trúc (ví dụ x86_64 hoặc aarch64), phiên bản GCC/GDB.
Không suy ra kiến trúc chỉ từ việc dùng Ubuntu. Python 3 chỉ dùng để chạy bộ thu log;
không cần pip hoặc thư viện ngoài. Nếu thiếu Python, cài bằng `sudo apt install python3`.

Chép thư mục `NT521_S01_Stackbase_bufferoverflow` từ Windows vào thư mục Home
trong Ubuntu bằng shared folder của VirtualBox hoặc cách chuyển file bạn đang dùng.
Chỉ cần source, tests, docs và kế hoạch; không cần chép `.git`.
Ví dụ nếu đã chép vào Home:

```bash
cd ~/NT521_S01_Stackbase_bufferoverflow
pwd
ls src tests docs
```

Nếu dùng thư mục khác, thay đường dẫn `cd` theo vị trí thực tế. Đường dẫn ổ `D:`
của Windows không phải đường dẫn trong Ubuntu. Nên build trong Home để tránh
vấn đề quyền thực thi của shared folder. Có thể tạo snapshot VM trước lab để dễ khôi phục.
VS Code/pwndbg là tùy chọn; GCC, GDB và Terminal đã đủ cho Ngày 2.

**Điểm kiểm tra:** Terminal tìm thấy GCC/GDB/Python và file `src/vulnerable.c`.

## 3. Bước 2 — Hiểu ranh giới buffer trước khi chạy

Trong lab, `buffer` là biến mảng cục bộ của hàm `copy_input`, dùng làm ví dụ bộ đệm
trên stack. `strcpy(destination, source)` sao chép chuỗi cho đến và bao gồm byte
kết thúc `\0`; hàm không nhận kích thước của đích.

Với `char buffer[8]`, chỉ có chỉ số `0` đến `7` hợp lệ. Điều kiện chứa chuỗi là:

```text
strlen(input) + 1 <= sizeof buffer
```

`strlen` đếm byte trước `\0`, không đếm `\0`. Tất cả test ở đây dùng ASCII,
vì chữ tiếng Việt mã hóa UTF-8 có thể dùng nhiều byte cho một ký tự.

```text
Chỉ số:       0   1   2   3   4   5   6    7  | 8 (ngoài buffer)
7 ký tự:      A   B   C   D   E   F   G   \0  |
8 ký tự:      A   B   C   D   E   F   G    H  | \0  <-- ghi quá 1 byte
```

Đây là sơ đồ byte của buffer, không mô tả thứ tự các biến, saved frame pointer
hay return address trong stack frame thực tế.

Ghi ngoài mảng dẫn đến **undefined behavior**: ngôn ngữ C không đảm bảo kết quả.
Chương trình có thể vẫn in dữ liệu, crash hoặc bị cơ chế bảo vệ dừng lại.
Thoát 0 không chứng minh an toàn; crash không chứng minh kiểm soát luồng thực thi.

Mô hình Source–Sink–Assumption của mẫu:

| Thành phần | Trong chương trình |
|---|---|
| Source | `argv[1]`, chuỗi được truyền từ dòng lệnh |
| Sink | `strcpy(buffer, input)` |
| Assumption sai | Mặc nhiên tin chuỗi cùng `\0` luôn vừa 8 byte |
| Kiểm tra còn thiếu | Xác minh độ dài trước khi ghi vào đích |

Đây phù hợp với định nghĩa lỗi buffer được cấp phát trên stack của
[MITRE CWE-121](https://cwe.mitre.org/data/definitions/121.html).

**Điểm kiểm tra:** giải thích được vì sao 8 ký tự vẫn gây lỗi trong buffer 8 byte.

## 4. Bước 3 — Đọc mã mẫu

```bash
nl -ba src/vulnerable.c
```

Đọc theo thứ tự:

1. `main` yêu cầu đúng một đối số, tránh truy cập `argv[1]` khi không có dữ liệu.
2. `copy_input` tạo `char buffer[8] = {0}`.
3. `printf` cho biết dung lượng, độ dài và số byte cần sao chép.
4. `fflush(stdout)` giữ dòng này trong log nếu ASan dừng ngay sau đó.
5. `strcpy` cố ý bỏ kiểm tra độ dài để tái hiện lỗi.
6. Dòng in buffer sau sao chép chỉ đáng tin khi đầu vào vừa buffer. Khi đã ghi
   ngoài mảng, không dùng phần in sau đó làm bằng chứng chương trình an toàn.

Không thay `strcpy` bằng hàm khác ở Ngày 2: bản sửa sẽ là đầu ra riêng của Ngày 4.

## 5. Bước 4 — Xác định test case

| File | Chuỗi | Byte dữ liệu | Byte gồm `\0` | Quan hệ với buffer 8 byte |
|---|---|---:|---:|---|
| `tests/short.txt` | `ABC` | 3 | 4 | Ngắn hơn |
| `tests/exact.txt` | `ABCDEFG` | 7 | 8 | Vừa đủ |
| `tests/off_by_one.txt` | `ABCDEFGH` | 8 | 9 | Tràn đúng 1 byte |
| `tests/long.txt` | `ABCDEFGHIJKLMNOP` | 16 | 17 | Vượt dung lượng 9 byte |

File text có thể có newline cuối file. Script bỏ newline CR/LF cuối file rồi
truyền chuỗi làm **một đối số**, nên newline đó không thuộc payload trong bảng.
Byte `\0` không lưu trong file test: nó là byte kết thúc chuỗi C được `strcpy` sao chép.
Manifest `tests/cases.json` ghi độ dài và phân loại dự kiến.

## 6. Bước 5 — Build hai phiên bản

Chạy tại thư mục gốc của dự án trong Ubuntu:

```bash
mkdir -p build
gcc -std=c11 -Wall -Wextra -g -O0 -fno-omit-frame-pointer \
    src/vulnerable.c -o build/vulnerable_debug
gcc -std=c11 -Wall -Wextra -g -O0 -fno-omit-frame-pointer \
    -fsanitize=address src/vulnerable.c -o build/vulnerable_asan
```

- `-g`: thông tin debug giúp báo cáo liên hệ với source.
- `-O0`: tắt tối ưu hóa cho lab dễ theo dõi.
- `-fno-omit-frame-pointer`: hỗ trợ stack trace.
- `-fsanitize=address`: bật kiểm tra truy cập bộ nhớ trong bản ASan; cũng phải
  có ở bước link, như lệnh compile/link kết hợp trên.
- `-Wall -Wextra`: cảnh báo biên dịch; không có cảnh báo không đồng nghĩa không có lỗi.

ASan thêm instrumentation/runtime và làm thay đổi bố cục bộ nhớ. Không lấy
địa chỉ/offset của bản ASan để suy ra bố cục bản debug. Ngày 2 dùng cấu hình
bảo vệ mặc định của hệ thống, không cần thay đổi ASLR/NX hay tắt Stack Canary.

Các cờ ASan, debug và frame pointer được mô tả trong
[GCC Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html).

**Điểm kiểm tra:** cả hai lệnh build thành công. Nếu báo lỗi, lưu nguyên thông báo;
chưa chuyển sang kết luận về buffer overflow.

## 7. Bước 6 — Chạy thủ công để hiểu hành vi

Trước hết chạy hai ca hợp lệ:

```bash
./build/vulnerable_debug ABC
echo "exit=$?"
./build/vulnerable_debug ABCDEFG
echo "exit=$?"
```

Dự kiến lần lượt thấy `required_bytes=4` và `required_bytes=8`, in đúng chuỗi,
mã thoát 0. `echo` phải đứng ngay sau lệnh cần đọc mã thoát.

Sau đó chạy ASan với ca tràn một byte:

```bash
ASAN_OPTIONS=halt_on_error=1:abort_on_error=0:detect_leaks=0:color=never \
    ./build/vulnerable_asan ABCDEFGH
echo "exit=$?"
```

Dự kiến: lỗi `AddressSanitizer: stack-buffer-overflow`, truy cập `WRITE`, stack
trace dẫn tới `strcpy`/`copy_input`, mô tả vùng của biến `buffer`, rồi mã thoát khác 0.
Không cố định địa chỉ, offset stack hay kích thước WRITE trong tài liệu: lấy số
thực tế từ log. Runtime có thể báo kích thước của cả thao tác sao chép, khác với
số byte vượt giới hạn.

**Điểm kiểm tra:** tìm được loại lỗi, thao tác WRITE, source line và đối tượng
buffer 8 byte trong log. Nếu chưa có, giữ log để kiểm tra nguyên nhân.

## 8. Bước 7 — Thu đủ bằng chứng cho mọi test

```bash
python3 tests/run_day2.py
echo "runner_exit=$?"
```

Script tự build lại từ source và chạy **4 test × 2 phiên bản**, dùng đối số trực tiếp
qua Python, không dùng shell để thực thi payload. Script không cài gói hay đổi
cấu hình bảo vệ. Mỗi lần chạy tạo một thư mục mới, ví dụ:

```text
evidence/day2/<thoi_gian_UTC>/
  environment.json, os-release.txt, gcc-version.stdout.txt, ...
  build-debug.command.txt, build-asan.command.txt, ...
  vulnerable.c, cases.json, sha256.json
  build/vulnerable_debug, build/vulnerable_asan
  debug-short.input.txt, debug-short.stdout.txt, ...
  asan-off_by_one.stderr.txt, asan-off_by_one.exitcode.txt, ...
  summary.csv
```

Script in đường dẫn evidence cụ thể. Dùng đường dẫn đó để đọc `summary.csv`
và `asan-off_by_one.stderr.txt`, `asan-long.stderr.txt`. Bổ sung tên VirtualBox
và cấu hình VM (RAM/vCPU nếu muốn) vào ghi chép môi trường hoặc trường `vm_product`.
Ảnh chụp terminal ASan là bổ sung hữu ích; log đầy đủ đã đáp ứng yêu cầu bằng chứng.

`EXPECTED` là kết quả phù hợp tiêu chí đối chiếu; `INVESTIGATE` yêu cầu đọc log.
Với ca tràn ở bản debug, script luôn ghi nhận undefined behavior và không buộc
phải crash. Mã thoát 0 của **runner** nghĩa bộ kiểm tra khớp tiêu chí, không nghĩa
mọi tiến trình con đều thoát 0; các ca tràn ASan được kỳ vọng thoát khác 0.

## 9. Bước 8 — Đọc và ghi nhận kết quả

| Phiên bản | short/exact: dự kiến | off_by_one/long: dự kiến |
|---|---|---|
| Debug | In đúng chuỗi, exit 0 | Undefined behavior; ghi nhận hành vi thực tế |
| ASan | Không báo lỗi tương ứng, exit 0 | Báo `stack-buffer-overflow`, WRITE, exit khác 0 |

Hoàn thành bảng dưới đây **sau khi chạy**, dựa vào `summary.csv` và stderr gốc:

| Phiên bản | Ca | Mã thoát thực tế | Lỗi/hiện tượng quan sát | File bằng chứng |
|---|---|---|---|---|
| Debug | short | Chưa chạy | Chưa ghi nhận | — |
| Debug | exact | Chưa chạy | Chưa ghi nhận | — |
| Debug | off_by_one | Chưa chạy | Chưa ghi nhận | — |
| Debug | long | Chưa chạy | Chưa ghi nhận | — |
| ASan | short | Chưa chạy | Chưa ghi nhận | — |
| ASan | exact | Chưa chạy | Chưa ghi nhận | — |
| ASan | off_by_one | Chưa chạy | Chưa ghi nhận | — |
| ASan | long | Chưa chạy | Chưa ghi nhận | — |

Khi có đúng báo cáo WRITE ngoài `buffer`, có thể viết kết luận:
“Với đầu vào … byte, `strcpy` cần ghi … byte kể cả null vào buffer 8 byte.
ASan báo ghi ngoài giới hạn tại …, chứng minh lỗi ghi tràn trong cấu hình đã chạy.”
Điền các dấu `…` từ test và log. Chưa có cơ sở kết luận ghi đè return address,
chuyển hướng luồng điều khiển hay chiếm quyền từ kết quả Ngày 2.

## 10. Xử lý các kết quả chưa khớp

- **Debug không crash:** phù hợp khả năng của undefined behavior; đọc ASan để
  chứng minh lỗi ghi ngoài giới hạn.
- **Chỉ có `DEADLYSIGNAL`:** chưa đủ chứng cứ lỗi cụ thể. Giữ log, kiểm tra cả
  hai ca hợp lệ, phiên bản GCC/runtime, đúng binary ASan và chạy lại một lần.
  Nếu vẫn xảy ra, cần chẩn đoán môi trường trước khi kết luận.
- **Thiếu ASan runtime hoặc link thất bại:** đọc `build-asan.stderr.txt`; kiểm tra
  bộ GCC từ kho Ubuntu. Không gọi lỗi build là bằng chứng tràn bộ đệm.
- **Ca 7 ký tự báo lỗi:** kiểm tra payload thật, newline, copy sai source hoặc
  chạy nhầm binary; runner lưu input byte và checksum để đối chiếu.
- **Permission denied trong shared folder:** chép source/test vào Home rồi build lại.

## 11. Checklist nghiệm thu Ngày 2

- [x] Source C mẫu và các ca kiểm thử đã được chuẩn bị.
- [ ] Ghi nhận OS/kiến trúc/phiên bản GCC/GDB cụ thể từ VM.
- [ ] Build debug và ASan thành công trong Ubuntu VM.
- [ ] Chạy đủ 8 lượt, lưu input/stdout/stderr/mã thoát.
- [ ] Hai ca hợp lệ không báo lỗi ASan tương ứng.
- [ ] Có báo cáo ASan chứng minh WRITE ngoài buffer ở ca tràn.
- [ ] Điền bảng kết quả thực tế và kết luận theo bằng chứng.

## Tài liệu đối chiếu

- [MITRE CWE-121](https://cwe.mitre.org/data/definitions/121.html): định nghĩa và phạm vi lỗi.
- [GCC Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html): ASan và thông tin debug.
- [Ubuntu — Install and manage packages](https://ubuntu.com/server/docs/how-to/software/package-management/): cài gói nếu cần.

Kế hoạch 5 ngày là tài liệu ngữ cảnh; trạng thái thực tế ở mục 1 được cập nhật theo
xác nhận của người học, không mặc định các checklist trong kế hoạch đã hoàn thành.
