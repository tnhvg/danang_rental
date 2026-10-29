-- Bước 1: ba bảng nền tảng của hệ thống.
--   khu_vuc : danh sách khu vực cố định (để lọc không bị sai chính tả)
--   lien_he : người gửi căn hộ cho tôi (chủ nhà, quản lý hoặc trung gian)
--   toa_nha : thông tin giống nhau cho mọi căn trong cùng một tòa

-- Khu vực tách thành bảng riêng thay vì gõ tay vào toa_nha, để "Sơn Trà" và
-- "son tra" không thành hai khu khác nhau. Muốn thêm khu mới chỉ cần thêm một dòng.
CREATE TABLE khu_vuc (
    id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- tự đánh số 1, 2, 3...
    ten  TEXT NOT NULL UNIQUE                               -- không được trống, không được trùng
);

-- Mỗi người chỉ lưu một lần. Căn hộ sẽ trỏ tới người gửi căn đó.
-- vai_tro quyết định hoa hồng: 'trung gian' thì chia 50%, còn lại tôi nhận đủ.
CREATE TABLE lien_he (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ten         TEXT NOT NULL,
    sdt         TEXT,                     -- lưu dạng chữ: số điện thoại không đem cộng trừ
    nhom_zalo   TEXT,                     -- tên group Zalo nơi người này gửi căn
    vai_tro     TEXT NOT NULL CHECK (vai_tro IN ('chủ nhà', 'quản lý', 'trung gian')),
    ghi_chu     TEXT,
    ngay_tao    TIMESTAMPTZ NOT NULL DEFAULT now()  -- tự ghi thời điểm nhập
);

CREATE TABLE toa_nha (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ten_toa     TEXT,                     -- được trống vì nhiều nhà không có tên
    loai_hinh   TEXT NOT NULL CHECK (loai_hinh IN ('chung cư', 'căn hộ dịch vụ', 'nhà nguyên căn')),

    -- Vị trí
    so_nha      TEXT,                     -- dạng chữ vì có địa chỉ kiểu "K45/2"
    ten_duong   TEXT NOT NULL,
    khu_vuc_id  INTEGER NOT NULL REFERENCES khu_vuc (id),  -- foreign key trỏ sang bảng khu_vuc
    vi_do       NUMERIC(9, 6) NOT NULL,   -- ví dụ 16.054321 (6 chữ số thập phân ≈ chính xác tới 10 cm)
    kinh_do     NUMERIC(9, 6) NOT NULL,

    -- Tiện ích trong tòa (đúng/sai)
    thang_may   BOOLEAN NOT NULL DEFAULT false,
    ho_boi      BOOLEAN NOT NULL DEFAULT false,
    gym         BOOLEAN NOT NULL DEFAULT false,
    cho_de_o_to BOOLEAN NOT NULL DEFAULT false,

    -- Công trình đang xây gần đó: kèm ngày ghi nhận vì công trình rồi sẽ xây xong
    gan_cong_trinh          BOOLEAN NOT NULL DEFAULT false,
    ngay_ghi_nhan_cong_trinh DATE,

    ghi_chu     TEXT,
    ngay_tao    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Danh sách khu vực ban đầu, theo cách khách hay gọi. Sửa hoặc thêm tùy thực tế.
INSERT INTO khu_vuc (ten) VALUES
    ('Sơn Trà'),
    ('An Hải'),
    ('Phước Mỹ'),
    ('An Thượng'),
    ('Mỹ An'),
    ('Khuê Mỹ'),
    ('Ngũ Hành Sơn'),
    ('Hải Châu'),
    ('Nam Việt Á'),
    ('Hòa Cường'),
    ('Hòa Xuân'),
    ('Thanh Khê'),
    ('Cẩm Lệ'),
    ('Liên Chiểu');
