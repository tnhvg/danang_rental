"""Trang Thêm căn hộ: nhập đặc điểm, giá, trạng thái và tải ảnh."""

import streamlit as st

from csdl import doc, ghi
from tien_ich import nen_anh

st.title("➕ Thêm căn hộ")

toa_nha = doc("""
    SELECT t.id, concat_ws(' · ', t.ten_toa, concat_ws(' ', t.so_nha, t.ten_duong), k.ten) AS nhan
    FROM toa_nha t JOIN khu_vuc k ON k.id = t.khu_vuc_id ORDER BY nhan
""")
lien_he = doc("SELECT id, ten || ' (' || vai_tro || ')' AS nhan FROM lien_he ORDER BY ten")
if not toa_nha or not lien_he:
    st.info("Mỗi căn hộ phải thuộc một **tòa nhà** và do một **người liên hệ** gửi, "
            "nên cần tạo hai thứ đó trước:")
    st.page_link("trang/lien_he.py", label=f"Bước 1: Thêm liên hệ {'✅' if lien_he else ''}", icon="📇")
    st.page_link("trang/toa_nha.py", label=f"Bước 2: Thêm tòa nhà {'✅' if toa_nha else ''}", icon="🏢")
    st.stop()

with st.form("them_can_ho", clear_on_submit=True):
    cot1, cot2 = st.columns(2)
    chon_toa = cot1.selectbox("Tòa nhà *", toa_nha, format_func=lambda t: t["nhan"])
    chon_lien_he = cot2.selectbox("Ai gửi căn này *", lien_he, format_func=lambda l: l["nhan"])

    c1, c2, c3, c4, c5 = st.columns(5)
    ma_can = c1.text_input("Số căn", help="Chỉ bạn thấy, khách không thấy")
    so_phong_ngu = c2.number_input("Phòng ngủ (0 = studio)", 0, 10, 1)
    so_phong_tam = c3.number_input("Phòng tắm", 0, 10, 1)
    dien_tich = c4.number_input("Diện tích (m²)", 0.0, 1000.0, 0.0, step=1.0)
    tang = c5.number_input("Tầng", 0, 100, 0)

    c1, c2, c3 = st.columns(3)
    gia_trieu = c1.number_input("Giá thuê (triệu/tháng) *", 0.0, 500.0, 0.0, step=0.5)
    huong_view = c2.selectbox("View", ["không có view", "biển", "sông", "núi", "thành phố"])
    noi_that = c3.selectbox("Nội thất", ["đầy đủ", "cơ bản", "không có"])

    c1, c2, c3, c4, c5 = st.columns(5)
    ban_cong = c1.checkbox("Ban công")
    vach_kinh = c2.checkbox("Phòng tắm vách kính")
    bon_tam = c3.checkbox("Bồn tắm")
    may_giat = c4.checkbox("Máy giặt riêng")
    thu_cung = c5.checkbox("Cho nuôi thú cưng")

    c1, c2 = st.columns(2)
    trang_thai = c1.selectbox("Trạng thái", ["còn trống", "sắp trống"])
    ngay_trong = c2.date_input("Ngày trống (nếu sắp trống)", value=None, format="DD/MM/YYYY")

    mo_ta = st.text_area("Mô tả cho khách đọc")
    ghi_chu = st.text_area("Ghi chú riêng (khách không thấy)")
    anh = st.file_uploader("Ảnh (ảnh đầu tiên làm ảnh bìa)", type=["jpg", "jpeg", "png", "webp"],
                           accept_multiple_files=True)

    if st.form_submit_button("Lưu căn hộ", type="primary"):
        if gia_trieu <= 0:
            st.error("Chưa nhập giá thuê.")
        elif trang_thai == "sắp trống" and not ngay_trong:
            st.error("Căn 'sắp trống' cần có ngày trống.")
        else:
            moi = ghi(
                """INSERT INTO can_ho (toa_nha_id, lien_he_id, ma_can, so_phong_ngu, so_phong_tam,
                       dien_tich, tang, gia_thue, ban_cong, phong_tam_vach_kinh, bon_tam,
                       may_giat_rieng, cho_nuoi_thu_cung, huong_view, noi_that, mo_ta,
                       ghi_chu_noi_bo, trang_thai, ngay_trong)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (chon_toa["id"], chon_lien_he["id"], ma_can.strip() or None, so_phong_ngu, so_phong_tam,
                 dien_tich or None, tang or None, round(gia_trieu * 1_000_000), ban_cong, vach_kinh,
                 bon_tam, may_giat, thu_cung, huong_view, noi_that, mo_ta.strip() or None,
                 ghi_chu.strip() or None, trang_thai,
                 ngay_trong if trang_thai == "sắp trống" else None),
            )
            for thu_tu, tep in enumerate(anh or []):
                ghi("INSERT INTO anh_can_ho (can_ho_id, du_lieu, thu_tu) VALUES (%s, %s, %s)",
                    (moi["id"], nen_anh(tep.getvalue()), thu_tu))
            st.success(f"Đã lưu căn hộ kèm {len(anh or [])} ảnh.")
