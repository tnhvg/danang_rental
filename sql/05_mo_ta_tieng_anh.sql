-- Bước 5: mô tả tiếng Anh cho khách nước ngoài.
-- Web tự chạy file này mỗi lần khởi động (chạy lại nhiều lần cũng không sao).

ALTER TABLE can_ho ADD COLUMN IF NOT EXISTS mo_ta_en TEXT;

-- c.* trong VIEW chỉ gồm các cột có lúc tạo VIEW, nên phải tạo lại để có thêm cột mo_ta_en.
DROP VIEW IF EXISTS v_can_ho;
CREATE VIEW v_can_ho WITH (security_invoker = true) AS
SELECT
    c.*,
    CASE
        WHEN c.trang_thai = 'sắp trống' AND c.ngay_trong <= current_date THEN 'còn trống'
        ELSE c.trang_thai
    END AS trang_thai_hom_nay,
    current_date - c.ngay_xac_nhan AS so_ngay_chua_xac_nhan,
    t.ten_toa, t.loai_hinh, t.so_nha, t.ten_duong, t.vi_do, t.kinh_do,
    t.thang_may, t.ho_boi, t.gym, t.cho_de_o_to, t.gan_cong_trinh,
    k.ten AS khu_vuc,
    l.ten AS ten_lien_he, l.sdt AS sdt_lien_he, l.vai_tro,
    CASE WHEN l.vai_tro = 'trung gian' THEN 0.5 ELSE 1.0 END AS ty_le_huong
FROM can_ho c
JOIN toa_nha t ON t.id = c.toa_nha_id
JOIN khu_vuc k ON k.id = t.khu_vuc_id
LEFT JOIN lien_he l ON l.id = c.lien_he_id;
