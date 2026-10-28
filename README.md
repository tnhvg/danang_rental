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

- [ ] Thêm tòa nhà: nhập địa chỉ, web tìm vị trí, tôi kiểm tra và kéo chấm về đúng chỗ
- [ ] Thêm căn hộ: form nhập đặc điểm, tải ảnh, chọn trạng thái
- [ ] Bản đồ hiển thị căn hộ, màu theo trạng thái
- [ ] Bộ lọc: tên đường, số phòng ngủ, khoảng giá, ngày dọn vào
- [ ] Giỏ hàng và link gửi khách (khách không thấy thông tin chủ nhà và hoa hồng)
- [ ] Trang quản lý có mật khẩu, chỉ tôi vào được

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
