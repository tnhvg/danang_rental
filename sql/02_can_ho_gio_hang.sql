-- Bước 2: căn hộ, ảnh, lịch sử trạng thái, khách hàng và giỏ hàng.

CREATE TABLE can_ho (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    toa_nha_id      INTEGER NOT NULL REFERENCES toa_nha (id),
    lien_he_id      INTEGER NOT NULL REFERENCES lien_he (id),  -- ai gửi căn này cho tôi

    ma_can          TEXT,                 -- số căn, ví dụ "A1203" (chỉ tôi thấy)
    so_phong_ngu    SMALLINT NOT NULL CHECK (so_phong_ngu BETWEEN 0 AND 10),  -- 0 = studio
    so_phong_tam    SMALLINT NOT NULL DEFAULT 1 CHECK (so_phong_tam BETWEEN 0 AND 10),
    dien_tich       NUMERIC(6, 1) CHECK (dien_tich > 0),   -- m²
    tang            SMALLINT,
    gia_thue        INTEGER NOT NULL CHECK (gia_thue > 0),  -- đồng/tháng

    -- Đặc điểm
    ban_cong            BOOLEAN NOT NULL DEFAULT false,
    phong_tam_vach_kinh BOOLEAN NOT NULL DEFAULT false,
    bon_tam             BOOLEAN NOT NULL DEFAULT false,
    may_giat_rieng      BOOLEAN NOT NULL DEFAULT false,
    cho_nuoi_thu_cung   BOOLEAN NOT NULL DEFAULT false,
    huong_view  TEXT NOT NULL DEFAULT 'không có view'
                CHECK (huong_view IN ('biển', 'sông', 'núi', 'thành phố', 'không có view')),
    noi_that    TEXT NOT NULL DEFAULT 'đầy đủ'
                CHECK (noi_that IN ('đầy đủ', 'cơ bản', 'không có')),

    mo_ta           TEXT,                 -- khách đọc được
    ghi_chu_noi_bo  TEXT,                 -- chỉ tôi đọc được

    -- Trạng thái: căn hết thì đổi trạng thái, không xoá
    trang_thai  TEXT NOT NULL DEFAULT 'còn trống'
                CHECK (trang_thai IN ('còn trống', 'sắp trống', 'đã cọc', 'đã cho thuê')),
    ngay_trong  DATE,                     -- chỉ dùng khi 'sắp trống'
    ngay_xac_nhan DATE NOT NULL DEFAULT current_date,  -- lần cuối hỏi chủ: căn còn không
    ngay_tao    TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- 'sắp trống' bắt buộc phải có ngày trống
    CHECK (trang_thai <> 'sắp trống' OR ngay_trong IS NOT NULL)
);

-- Ảnh được nén nhỏ (khoảng 100–200 KB) rồi lưu thẳng trong database.
-- Xoá căn hộ thì ảnh của căn đó tự xoá theo (ON DELETE CASCADE).
CREATE TABLE anh_can_ho (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    can_ho_id   INTEGER NOT NULL REFERENCES can_ho (id) ON DELETE CASCADE,
    du_lieu     BYTEA NOT NULL,           -- nội dung file ảnh JPEG
    thu_tu      SMALLINT NOT NULL DEFAULT 0,  -- ảnh thứ tự 0 là ảnh bìa
    ngay_tao    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Mỗi lần đổi trạng thái được ghi lại một dòng. Sau này dùng để phân tích:
-- căn loại nào cho thuê nhanh, mất bao nhiêu ngày từ lúc nhận căn tới lúc có khách.
CREATE TABLE lich_su_trang_thai (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    can_ho_id   INTEGER NOT NULL REFERENCES can_ho (id) ON DELETE CASCADE,
    trang_thai  TEXT NOT NULL,
    thoi_diem   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Trigger: database TỰ ghi lịch sử mỗi khi trạng thái thay đổi,
-- nên không bao giờ sót dù đổi từ web hay sửa tay.
CREATE FUNCTION ghi_lich_su_trang_thai() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' OR NEW.trang_thai IS DISTINCT FROM OLD.trang_thai THEN
        INSERT INTO lich_su_trang_thai (can_ho_id, trang_thai) VALUES (NEW.id, NEW.trang_thai);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER can_ho_doi_trang_thai
    AFTER INSERT OR UPDATE OF trang_thai ON can_ho
    FOR EACH ROW EXECUTE FUNCTION ghi_lich_su_trang_thai();

CREATE TABLE khach_hang (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ten             TEXT NOT NULL,
    sdt             TEXT,
    nhu_cau         TEXT,                 -- ghi tự do: khu vực, view, yêu cầu đặc biệt...
    ngan_sach_toi_da INTEGER,
    ngay_don_vao    DATE,
    ngay_tao        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ma_link là chuỗi ngẫu nhiên khó đoán, nằm trong đường link gửi khách.
CREATE TABLE gio_hang (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    khach_hang_id   INTEGER NOT NULL REFERENCES khach_hang (id),
    ma_link         TEXT NOT NULL UNIQUE,
    ngay_tao        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Một giỏ có nhiều căn, một căn nằm trong nhiều giỏ.
-- Khoá chính gồm HAI cột: cùng một căn không thể bỏ vào cùng một giỏ hai lần.
CREATE TABLE gio_hang_can_ho (
    gio_hang_id INTEGER NOT NULL REFERENCES gio_hang (id) ON DELETE CASCADE,
    can_ho_id   INTEGER NOT NULL REFERENCES can_ho (id),
    PRIMARY KEY (gio_hang_id, can_ho_id)
);

-- VIEW (bảng ảo): không lưu dữ liệu, mỗi lần đọc sẽ tính lại từ bảng gốc.
-- Ở đây tính "trạng thái hôm nay": căn 'sắp trống' đã tới ngày trống thì coi là 'còn trống'.
CREATE VIEW v_can_ho AS
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
    -- Hoa hồng: trung gian thì chia đôi
    CASE WHEN l.vai_tro = 'trung gian' THEN 0.5 ELSE 1.0 END AS ty_le_huong
FROM can_ho c
JOIN toa_nha t ON t.id = c.toa_nha_id
JOIN khu_vuc k ON k.id = t.khu_vuc_id
JOIN lien_he l ON l.id = c.lien_he_id;
