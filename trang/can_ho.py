"""Trang Căn hộ: thêm căn mới kèm ảnh, và cập nhật trạng thái hằng ngày."""

import streamlit as st

from csdl import doc, ghi
from tien_ich import dinh_dang_gia, hoa_hong, nen_anh

TRANG_THAI = ["còn trống", "sắp trống", "đã cọc", "đã cho thuê"]
SO_NGAY_CANH_BAO = 7

st.title("🏠 Căn hộ")
tab_cap_nhat, tab_them = st.tabs(["Cập nhật trạng thái", "Thêm căn mới"])

# ---------------------------------------------------------------- Thêm căn mới
with tab_them:
    toa_nha = doc("""
        SELECT t.id, concat_ws(' · ', t.ten_toa, concat_ws(' ', t.so_nha, t.ten_duong), k.ten) AS nhan
        FROM toa_nha t JOIN khu_vuc k ON k.id = t.khu_vuc_id ORDER BY nhan
    """)
    lien_he = doc("SELECT id, ten || ' (' || vai_tro || ')' AS nhan FROM lien_he ORDER BY ten")
    if not toa_nha or not lien_he:
        st.info("Cần có ít nhất một tòa nhà và một liên hệ trước khi thêm căn.")
    else:
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

# ---------------------------------------------------------- Cập nhật trạng thái
with tab_cap_nhat:
    hien_ca_da_thue = st.toggle("Hiện cả căn đã cọc / đã cho thuê")
    can_ho = doc(f"""
        SELECT id, khu_vuc, ten_duong, ma_can, so_phong_ngu, gia_thue, trang_thai, trang_thai_hom_nay,
               ngay_trong, so_ngay_chua_xac_nhan, ten_lien_he, ty_le_huong
        FROM v_can_ho
        {"" if hien_ca_da_thue else "WHERE trang_thai_hom_nay IN ('còn trống', 'sắp trống')"}
        ORDER BY so_ngay_chua_xac_nhan DESC, khu_vuc
    """)
    can_kiem_tra = [c for c in can_ho if c["trang_thai_hom_nay"] in ("còn trống", "sắp trống")
                    and c["so_ngay_chua_xac_nhan"] > SO_NGAY_CANH_BAO]
    if can_kiem_tra:
        st.warning(f"⚠️ {len(can_kiem_tra)} căn đã hơn {SO_NGAY_CANH_BAO} ngày chưa hỏi lại chủ. "
                   "Hỏi chủ xem còn trống không trước khi gửi khách.")

    bang = [{
        "Mã": c["id"],
        "Khu vực": c["khu_vuc"],
        "Đường": c["ten_duong"],
        "Số căn": c["ma_can"],
        "PN": c["so_phong_ngu"],
        "Giá": dinh_dang_gia(c["gia_thue"]),
        "Trạng thái": c["trang_thai_hom_nay"]
                      + (f" ({c['ngay_trong']:%d/%m})" if c["trang_thai_hom_nay"] == "sắp trống" else ""),
        "Chưa xác nhận": f"{c['so_ngay_chua_xac_nhan']} ngày"
                         + (" ⚠️" if c["so_ngay_chua_xac_nhan"] > SO_NGAY_CANH_BAO else ""),
        "Người gửi": c["ten_lien_he"],
        "HH nếu ký 12 tháng": dinh_dang_gia(hoa_hong(c["gia_thue"], 12, float(c["ty_le_huong"]))),
    } for c in can_ho]
    chon = st.dataframe(bang, hide_index=True, width="stretch",
                        on_select="rerun", selection_mode="single-row", key="bang_can_ho")

    if chon.selection.rows:
        can = can_ho[chon.selection.rows[0]]
        st.subheader(f"Căn {can['ma_can'] or can['id']} · {can['ten_duong']}")
        with st.form("cap_nhat"):
            c1, c2, c3 = st.columns(3)
            trang_thai_moi = c1.selectbox("Trạng thái", TRANG_THAI, index=TRANG_THAI.index(can["trang_thai"]))
            ngay_trong_moi = c2.date_input("Ngày trống", value=can["ngay_trong"], format="DD/MM/YYYY")
            gia_moi = c3.number_input("Giá (triệu/tháng)", 0.5, 500.0, can["gia_thue"] / 1_000_000, step=0.5)
            st.caption("Bấm Lưu nghĩa là bạn vừa hỏi chủ xong: ngày xác nhận được đặt lại thành hôm nay.")
            if st.form_submit_button("Lưu", type="primary"):
                if trang_thai_moi == "sắp trống" and not ngay_trong_moi:
                    st.error("Căn 'sắp trống' cần có ngày trống.")
                else:
                    ghi("""UPDATE can_ho SET trang_thai = %s, ngay_trong = %s, gia_thue = %s,
                               ngay_xac_nhan = current_date WHERE id = %s""",
                        (trang_thai_moi, ngay_trong_moi if trang_thai_moi == "sắp trống" else None,
                         round(gia_moi * 1_000_000), can["id"]))
                    st.rerun()
