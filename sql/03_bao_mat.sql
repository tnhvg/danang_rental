-- Bước 3: khoá các bảng lại.
-- Supabase tự mở một "cổng" API cho mọi bảng. Bật Row Level Security (RLS: bảo mật
-- theo từng dòng) mà không cấp quyền nào thì cổng đó không đọc được gì.
-- Web của chúng ta kết nối thẳng bằng tài khoản chủ database nên vẫn đọc ghi bình thường.
ALTER TABLE khu_vuc            ENABLE ROW LEVEL SECURITY;
ALTER TABLE lien_he            ENABLE ROW LEVEL SECURITY;
ALTER TABLE toa_nha            ENABLE ROW LEVEL SECURITY;
ALTER TABLE can_ho             ENABLE ROW LEVEL SECURITY;
ALTER TABLE anh_can_ho         ENABLE ROW LEVEL SECURITY;
ALTER TABLE lich_su_trang_thai ENABLE ROW LEVEL SECURITY;
ALTER TABLE khach_hang         ENABLE ROW LEVEL SECURITY;
ALTER TABLE gio_hang           ENABLE ROW LEVEL SECURITY;
ALTER TABLE gio_hang_can_ho    ENABLE ROW LEVEL SECURITY;

-- VIEW mặc định chạy với quyền người tạo, nên sẽ "lách" qua RLS.
-- security_invoker bắt VIEW dùng quyền của người đang đọc.
ALTER VIEW v_can_ho SET (security_invoker = true);

-- Dùng giờ Việt Nam cho current_date và now(). Máy chủ Supabase mặc định dùng giờ UTC
-- (chậm 7 tiếng), nên nếu không đặt thì từ 0h đến 7h sáng "hôm nay" sẽ bị tính thành hôm qua.
DO $$
BEGIN
    EXECUTE format('ALTER DATABASE %I SET timezone TO %L', current_database(), 'Asia/Ho_Chi_Minh');
END
$$;
