"""Trang Cập nhật căn hộ: đổi trạng thái, giá, và xác nhận căn còn trống."""

import streamlit as st

from csdl import doc, ghi
from tien_ich import dinh_dang_gia, hoa_hong

TRANG_THAI = ["còn trống", "sắp trống", "đã cọc", "đã cho thuê"]
SO_NGAY_CANH_BAO = 7

st.title("🔄 Cập nhật căn hộ")

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
