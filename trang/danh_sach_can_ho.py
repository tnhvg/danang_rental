"""Trang Danh sách căn hộ: xem lại mọi căn đã lưu (ảnh + thông tin), đổi trạng thái, thêm ảnh."""

import streamlit as st

from csdl import doc, ghi
from tien_ich import dinh_dang_gia, hoa_hong, mo_ta_trang_thai, nen_anh

TRANG_THAI = ["còn trống", "sắp trống", "đã cọc", "đã cho thuê"]
SO_NGAY_CANH_BAO = 7

st.title("📋 Danh sách căn hộ")

c1, c2 = st.columns([3, 1])
tu_khoa = c1.text_input("🔍 Tìm theo tên đường, tên tòa, số căn, mô tả, ghi chú", placeholder="Ví dụ: Mỹ Đa")
hien_ca_da_thue = c2.toggle("Hiện cả căn đã cọc / đã thuê")

dieu_kien, tham_so = [], []
if not hien_ca_da_thue:
    dieu_kien.append("trang_thai_hom_nay IN ('còn trống', 'sắp trống')")
if tu_khoa.strip():
    # ILIKE: tìm không phân biệt chữ hoa chữ thường; % nghĩa là "bất kỳ chữ nào trước/sau"
    dieu_kien.append("""concat_ws(' ', ten_duong, ten_toa, ma_can, khu_vuc, mo_ta, ghi_chu_noi_bo, ten_lien_he)
                        ILIKE %s""")
    tham_so.append(f"%{tu_khoa.strip()}%")
can_ho = doc(f"""
    SELECT * FROM v_can_ho
    {"WHERE " + " AND ".join(dieu_kien) if dieu_kien else ""}
    ORDER BY ngay_tao DESC
""", tham_so)

if not can_ho:
    st.info("Không có căn nào. Thêm căn ở trang ➕ Thêm căn hộ.")
    st.page_link("trang/them_can_ho.py", label="Thêm căn hộ", icon="➕")
    st.stop()

can_kiem_tra = [c for c in can_ho if c["trang_thai_hom_nay"] in ("còn trống", "sắp trống")
                and c["so_ngay_chua_xac_nhan"] > SO_NGAY_CANH_BAO]
if can_kiem_tra:
    st.warning(f"⚠️ {len(can_kiem_tra)} căn đã hơn {SO_NGAY_CANH_BAO} ngày chưa hỏi lại chủ. "
               "Hỏi chủ xem còn trống không trước khi gửi khách.")

st.caption(f"{len(can_ho)} căn. Bấm ô vuông đầu dòng để xem ảnh và cập nhật.")
bang = [{
    "Mã": c["id"],
    "Địa chỉ": " ".join(x for x in [c["so_nha"], c["ten_duong"]] if x),
    "Khu vực": c["khu_vuc"],
    "Tòa": c["ten_toa"] or "",
    "Số căn": c["ma_can"] or "",
    "PN": "Studio" if c["so_phong_ngu"] == 0 else str(c["so_phong_ngu"]),
    "Giá": dinh_dang_gia(c["gia_thue"]),
    "Trạng thái": mo_ta_trang_thai(c["trang_thai_hom_nay"], c["ngay_trong"])
                  if c["trang_thai_hom_nay"] in ("còn trống", "sắp trống") else c["trang_thai_hom_nay"],
    "Chưa hỏi lại chủ": f"{c['so_ngay_chua_xac_nhan']} ngày"
                        + (" ⚠️" if c["so_ngay_chua_xac_nhan"] > SO_NGAY_CANH_BAO else ""),
    "Người gửi": c["ten_lien_he"] or "",
} for c in can_ho]
chon = st.dataframe(bang, hide_index=True, width="stretch",
                    on_select="rerun", selection_mode="single-row", key="bang_can_ho")

if not chon.selection.rows or chon.selection.rows[0] >= len(can_ho):
    st.stop()

# ---------------------------------------------------------------- Chi tiết căn
can = can_ho[chon.selection.rows[0]]
st.divider()
phong = "Studio" if can["so_phong_ngu"] == 0 else f"{can['so_phong_ngu']} phòng ngủ"
st.subheader(f"#{can['id']} · {phong} · {dinh_dang_gia(can['gia_thue'])}/tháng")
st.write(f"📍 {' '.join(x for x in [can['so_nha'], can['ten_duong']] if x)}, {can['khu_vuc']}"
         + (f" · tòa {can['ten_toa']}" if can["ten_toa"] else "")
         + (f" · căn {can['ma_can']}" if can["ma_can"] else ""))

cot_anh, cot_thong_tin = st.columns([3, 2])
with cot_anh:
    anh = doc("SELECT du_lieu FROM anh_can_ho WHERE can_ho_id = %s ORDER BY thu_tu, id", (can["id"],))
    if anh:
        st.image(bytes(anh[0]["du_lieu"]), width="stretch")
        if len(anh) > 1:
            st.image([bytes(a["du_lieu"]) for a in anh[1:]], width=160)
    else:
        st.info("Căn này chưa có ảnh.")
    with st.form("them_anh", clear_on_submit=True):
        anh_moi = st.file_uploader("Thêm ảnh cho căn này", type=["jpg", "jpeg", "png", "webp"],
                                   accept_multiple_files=True)
        if st.form_submit_button("Tải ảnh lên") and anh_moi:
            for i, tep in enumerate(anh_moi):
                ghi("INSERT INTO anh_can_ho (can_ho_id, du_lieu, thu_tu) VALUES (%s, %s, %s)",
                    (can["id"], nen_anh(tep.getvalue()), len(anh) + i))
            st.rerun()

with cot_thong_tin:
    dac_diem = [
        f"{float(can['dien_tich']):g} m²" if can["dien_tich"] else None,
        f"{can['so_phong_tam']} phòng tắm",
        f"tầng {can['tang']}" if can["tang"] else None,
        f"view {can['huong_view']}" if can["huong_view"] != "không có view" else None,
        f"nội thất {can['noi_that']}",
        "ban công" if can["ban_cong"] else None,
        "phòng tắm vách kính" if can["phong_tam_vach_kinh"] else None,
        "bồn tắm" if can["bon_tam"] else None,
        "máy giặt riêng" if can["may_giat_rieng"] else None,
        "nuôi thú cưng" if can["cho_nuoi_thu_cung"] else None,
        "thang máy" if can["thang_may"] else None,
        "hồ bơi" if can["ho_boi"] else None,
        "gym" if can["gym"] else None,
        "chỗ để ô tô" if can["cho_de_o_to"] else None,
    ]
    st.write(" · ".join(d for d in dac_diem if d))
    if can["mo_ta"]:
        st.write(f"**Mô tả:** {can['mo_ta']}")
    if can["ghi_chu_noi_bo"]:
        st.write(f"**Ghi chú riêng:** {can['ghi_chu_noi_bo']}")
    if can["ten_lien_he"]:
        st.write(f"**Người gửi:** {can['ten_lien_he']} {can['sdt_lien_he'] or ''} ({can['vai_tro']})")
    st.write(f"**Hoa hồng nếu ký 12 tháng:** "
             f"{dinh_dang_gia(hoa_hong(can['gia_thue'], 12, float(can['ty_le_huong'])))}")

    with st.form("cap_nhat"):
        st.write("**Cập nhật**")
        trang_thai_moi = st.selectbox("Trạng thái", TRANG_THAI, index=TRANG_THAI.index(can["trang_thai"]))
        ngay_trong_moi = st.date_input("Ngày trống (nếu sắp trống)", value=can["ngay_trong"], format="DD/MM/YYYY")
        gia_moi = st.number_input("Giá (triệu/tháng)", 0.5, 500.0, can["gia_thue"] / 1_000_000, step=0.5)
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
