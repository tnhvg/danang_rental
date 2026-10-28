-- DỮ LIỆU GIẢ chỉ để chạy thử trên máy. KHÔNG chạy file này trên database thật.
INSERT INTO lien_he (ten, sdt, nhom_zalo, vai_tro) VALUES
    ('Chị Lan', '0905000001', 'Căn hộ Mỹ An - Lan', 'chủ nhà'),
    ('Anh Minh (môi giới)', '0905000002', 'Nhóm Minh Sơn Trà', 'trung gian');

INSERT INTO toa_nha (ten_toa, loai_hinh, so_nha, ten_duong, khu_vuc_id, vi_do, kinh_do, thang_may, ho_boi, gym) VALUES
    ('Lan House', 'căn hộ dịch vụ', '12', 'Mỹ Đa Đông 12',
        (SELECT id FROM khu_vuc WHERE ten = 'Mỹ An'), 16.041200, 108.243500, true, false, false),
    ('Sea View Tower', 'chung cư', '88', 'Võ Nguyên Giáp',
        (SELECT id FROM khu_vuc WHERE ten = 'Phước Mỹ'), 16.065800, 108.246900, true, true, true),
    (NULL, 'căn hộ dịch vụ', 'K45/2', 'Hồ Nghinh',
        (SELECT id FROM khu_vuc WHERE ten = 'Sơn Trà'), 16.071500, 108.240200, false, false, false);

INSERT INTO can_ho (toa_nha_id, lien_he_id, ma_can, so_phong_ngu, dien_tich, tang, gia_thue,
                    ban_cong, phong_tam_vach_kinh, huong_view, mo_ta, trang_thai, ngay_trong) VALUES
    (1, 1, '201', 1, 40, 2, 7000000, true, true, 'thành phố', 'Studio mới, gần biển Mỹ Khê 300m', 'còn trống', NULL),
    (1, 1, '302', 2, 65, 3, 11000000, true, false, 'thành phố', 'Hai phòng ngủ rộng, có bếp riêng', 'sắp trống', current_date + 5),
    (2, 2, 'A1203', 2, 78, 12, 18000000, true, true, 'biển', 'View biển trực diện, hồ bơi vô cực', 'còn trống', NULL),
    (2, 2, 'B0805', 1, 50, 8, 12000000, false, true, 'biển', 'Một phòng ngủ, view biển chéo', 'đã cọc', NULL),
    (3, 2, '3B', 0, 30, 3, 5500000, false, false, 'không có view', 'Studio giá tốt trong kiệt yên tĩnh', 'còn trống', NULL);
