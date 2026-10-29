# danang_rental: Quản lý căn hộ cho thuê tại Đà Nẵng

## Bài toán

Tôi làm sale cho thuê căn hộ tại Đà Nẵng. Chủ nhà và người quản lý gửi căn hộ qua rất nhiều group chat Zalo,
tin nhắn trôi nhanh nên khó nắm được căn nào còn trống, căn nào đã cọc. Khi tư vấn khách, tôi phải lục lại
từng group để tìm căn phù hợp.

Dự án này xây dựng một trang web để:

1. Lưu tất cả căn hộ ở **một nơi duy nhất**, kèm ảnh, đặc điểm và trạng thái.
2. Hiển thị căn hộ trên **bản đồ Đà Nẵng** để tìm căn theo khu vực khách muốn.
3. Tạo **giỏ hàng** gồm các căn phù hợp với từng khách và gửi khách **một đường link**.

## Quy trình sử dụng

```
Chủ gửi căn qua Zalo
  → Tôi nhập căn vào web (địa chỉ, đặc điểm, ảnh)
  → Căn hiện trên bản đồ
Khách hỏi thuê
  → Tôi lọc theo khu vực, số phòng ngủ, giá, ngày dọn vào
  → Chọn các căn phù hợp bỏ vào giỏ
  → Gửi link giỏ hàng cho khách
Chủ báo đã cọc
  → Tôi đổi trạng thái căn (không xoá)
```

## Trạng thái căn hộ

| Trạng thái | Khách có thấy không |
|---|---|
| Còn trống | Có |
| Sắp trống (kèm ngày trống) | Có, hiện "Trống từ ngày ..." |
| Đã cọc | Không (trong giỏ đã gửi: hiện mờ, ghi "Đã có người thuê") |
| Đã cho thuê | Không (trong giỏ đã gửi: hiện mờ, ghi "Đã có người thuê") |

## Phiên bản 1 (MVP: phiên bản đơn giản nhất dùng được)

- [x] Thêm tòa nhà: nhập địa chỉ, web tìm vị trí, tôi kiểm tra và kéo chấm về đúng chỗ
- [x] Thêm căn hộ: form nhập đặc điểm, tải ảnh, chọn trạng thái
- [x] Bản đồ hiển thị căn hộ, màu theo trạng thái
- [x] Bộ lọc: tên đường, số phòng ngủ, khoảng giá, ngày dọn vào
- [x] Giỏ hàng và link gửi khách (khách không thấy thông tin chủ nhà và hoa hồng)
- [x] Trang quản lý có mật khẩu, chỉ tôi vào được

## Phiên bản sau

- Lọc theo bán kính và khoảng cách tới biển, công viên
- Khách bấm "Tôi thích căn này" ngay trong link
- Gợi ý căn mới phù hợp cho khách cũ
- Theo dõi hoa hồng: `giá thuê × số tháng hợp đồng × 8,3%` (qua trung gian thì chia 50%)
- Phân tích dữ liệu: căn loại nào cho thuê nhanh, giá/m² theo khu, nguồn nào mang lại nhiều hợp đồng

## Công nghệ

| Phần | Công cụ | Lý do chọn |
|---|---|---|
| Cơ sở dữ liệu và lưu ảnh | PostgreSQL trên Supabase | Miễn phí, dùng SQL |
| Giao diện web | Streamlit (Python) | Đã dùng ở dự án trước |
| Bản đồ | OpenStreetMap | Miễn phí, không cần thẻ thanh toán |

## Cấu trúc dự án

```
app.py                  Điểm bắt đầu: chia trang khách xem / trang quản lý (có mật khẩu)
csdl.py                 Kết nối database, hai hàm doc() và ghi()
tien_ich.py             Hàm dùng chung: định dạng giá, nén ảnh, hoa hồng, tìm tọa độ
trang/
  tim_can.py            Bộ lọc + bản đồ + giỏ hàng + tạo link
  can_ho.py             Thêm căn kèm ảnh, cập nhật trạng thái, cảnh báo căn lâu chưa xác nhận
  toa_nha.py            Thêm tòa nhà, ghim vị trí trên bản đồ
  lien_he.py            Chủ nhà, quản lý, trung gian
  gio_hang.py           Xem lại các giỏ đã gửi khách
  khach_xem.py          Trang khách mở từ link (không lộ thông tin chủ, số căn, hoa hồng)
sql/
  01_bang_co_ban.sql    Bảng khu vực, liên hệ, tòa nhà
  02_can_ho_gio_hang.sql Bảng căn hộ, ảnh, lịch sử trạng thái, khách, giỏ hàng + VIEW v_can_ho
  03_bao_mat.sql        Khoá bảng trên Supabase, đặt giờ Việt Nam
  du_lieu_mau.sql       Dữ liệu giả để chạy thử trên máy (KHÔNG chạy trên database thật)
tests/                  Kiểm thử các hàm trong tien_ich.py
```

## Đưa web lên mạng

### 1. Tạo database trên Supabase

1. Đăng ký tài khoản miễn phí tại https://supabase.com, bấm **New project**, chọn vùng **Singapore**
   (gần Việt Nam nhất). Ghi lại mật khẩu database.
2. Vào **SQL Editor**, lần lượt dán nội dung và bấm **Run** cho từng file theo đúng thứ tự:
   `01_bang_co_ban.sql` → `02_can_ho_gio_hang.sql` → `03_bao_mat.sql`.
3. Bấm nút **Connect** ở đầu trang, chọn ô **Direct · Connection string**, chọn kiểu kết nối
   **Session pooler**, copy chuỗi kết nối và thay `[YOUR-PASSWORD]` bằng mật khẩu database.
   Phải dùng Session pooler vì kết nối trực tiếp của gói miễn phí chỉ hỗ trợ IPv6,
   còn Streamlit Cloud chỉ dùng IPv4.

### 2. Đưa web lên Streamlit Cloud

1. Vào https://share.streamlit.io, đăng nhập bằng GitHub, bấm **Create app**.
2. Chọn repo `danang_rental`, nhánh `main`, file `app.py`.
3. Mở **Advanced settings → Secrets**, dán nội dung theo mẫu `.streamlit/secrets.toml.example`
   (chuỗi kết nối Supabase, mật khẩu quản lý, số Zalo).
4. Bấm **Deploy**.

## Chạy thử trên máy

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # rồi điền thông tin thật
streamlit run app.py
pytest                                                       # chạy kiểm thử
```

