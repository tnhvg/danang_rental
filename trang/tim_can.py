"""Trang chính: lọc căn theo nhu cầu khách, xem trên bản đồ, bỏ vào giỏ và tạo link gửi khách."""

import secrets
from urllib.parse import urlsplit

import folium
import streamlit as st
from streamlit_folium import st_folium

from csdl import doc, ghi
from tien_ich import TAM_DA_NANG, dinh_dang_gia, mo_ta_trang_thai

MAU_TRANG_THAI = {"còn trống": "green", "sắp trống": "orange"}

st.title("🗺️ Tìm căn & tạo giỏ hàng")
gio = st.session_state.setdefault("gio", [])  # danh sách mã căn đang chọn cho khách

# ------------------------------------------------------------------- Bộ lọc
can_ho = doc("""
    SELECT * FROM v_can_ho
    WHERE trang_thai_hom_nay IN ('còn trống', 'sắp trống')
    ORDER BY gia_thue
""")

with st.sidebar:
    st.header("Nhu cầu của khách")
    khu = st.multiselect("Khu vực", sorted({c["khu_vuc"] for c in can_ho}))
    duong = st.multiselect("Đường", sorted({c["ten_duong"] for c in can_ho}))
    phong_ngu = st.multiselect("Số phòng ngủ", sorted({c["so_phong_ngu"] for c in can_ho}),
                               format_func=lambda n: "Studio" if n == 0 else f"{n} PN")
    gia_toi_da = st.number_input("Giá tối đa (triệu/tháng, 0 = không giới hạn)", 0.0, 500.0, 0.0, step=1.0)
    ngay_don_vao = st.date_input("Ngày dọn vào", value=None, format="DD/MM/YYYY",
                                 help="Hiện căn còn trống và căn sắp trống trước ngày này")
    view = st.multiselect("View", ["biển", "sông", "núi", "thành phố"])
    can_ban_cong = st.checkbox("Phải có ban công")
    can_ho_boi = st.checkbox("Tòa có hồ bơi")


def phu_hop(c: dict) -> bool:
    if khu and c["khu_vuc"] not in khu:
        return False
    if duong and c["ten_duong"] not in duong:
        return False
    if phong_ngu and c["so_phong_ngu"] not in phong_ngu:
        return False
    if gia_toi_da and c["gia_thue"] > gia_toi_da * 1_000_000:
        return False
    if ngay_don_vao and c["trang_thai_hom_nay"] == "sắp trống" and c["ngay_trong"] > ngay_don_vao:
        return False
    if view and c["huong_view"] not in view:
        return False
    if can_ban_cong and not c["ban_cong"]:
        return False
    if can_ho_boi and not c["ho_boi"]:
        return False
    return True


ket_qua = [c for c in can_ho if phu_hop(c)]
st.write(f"**{len(ket_qua)}** căn phù hợp (trên tổng {len(can_ho)} căn còn trống hoặc sắp trống)")

# ------------------------------------------------------------------- Bản đồ
# Gom các căn theo tòa nhà: mỗi tòa là một chấm, bấm vào chấm thấy danh sách căn.
theo_toa: dict[int, list[dict]] = {}
for c in ket_qua:
    theo_toa.setdefault(c["toa_nha_id"], []).append(c)

ban_do = folium.Map(location=TAM_DA_NANG, zoom_start=13)
for cac_can in theo_toa.values():
    dau = cac_can[0]
    co_can_trong = any(c["trang_thai_hom_nay"] == "còn trống" for c in cac_can)
    noi_dung = "<br>".join(
        f"#{c['id']} · {'Studio' if c['so_phong_ngu'] == 0 else str(c['so_phong_ngu']) + ' PN'}"
        f" · {dinh_dang_gia(c['gia_thue'])} · {mo_ta_trang_thai(c['trang_thai_hom_nay'], c['ngay_trong'])}"
        for c in cac_can
    )
    tieu_de = dau["ten_toa"] or f"{dau['so_nha'] or ''} {dau['ten_duong']}".strip()
    folium.Marker(
        [float(dau["vi_do"]), float(dau["kinh_do"])],
        tooltip=f"{tieu_de} ({len(cac_can)} căn)",
        popup=folium.Popup(f"<b>{tieu_de}</b><br>{noi_dung}", max_width=320),
        icon=folium.Icon(color=MAU_TRANG_THAI["còn trống" if co_can_trong else "sắp trống"], icon="home"),
    ).add_to(ban_do)

if theo_toa:
    ban_do.fit_bounds([[float(c["vi_do"]), float(c["kinh_do"])] for c in ket_qua], max_zoom=16)
st_folium(ban_do, height=450, use_container_width=True, returned_objects=[], key="ban_do_tim_can")
st.caption("🟢 có căn còn trống · 🟠 chỉ có căn sắp trống. Số # trên bản đồ là mã căn trong bảng dưới.")

# --------------------------------------------------------- Bảng kết quả + chọn
bang = [{
    "Mã": c["id"],
    "Khu vực": c["khu_vuc"],
    "Đường": c["ten_duong"],
    "PN": "Studio" if c["so_phong_ngu"] == 0 else str(c["so_phong_ngu"]),  # cả cột phải cùng kiểu chữ
    "m²": c["dien_tich"],
    "Giá": dinh_dang_gia(c["gia_thue"]),
    "View": c["huong_view"],
    "Ban công": "✓" if c["ban_cong"] else "",
    "Trạng thái": mo_ta_trang_thai(c["trang_thai_hom_nay"], c["ngay_trong"]),
    "Trong giỏ": "🧺" if c["id"] in gio else "",
} for c in ket_qua]
chon = st.dataframe(bang, hide_index=True, width="stretch",
                    on_select="rerun", selection_mode="multi-row", key="bang_ket_qua")
if st.button("➕ Thêm các căn đã chọn vào giỏ", disabled=not chon.selection.rows):
    for dong in chon.selection.rows:
        if dong < len(ket_qua) and ket_qua[dong]["id"] not in gio:
            gio.append(ket_qua[dong]["id"])
    st.rerun()

# ------------------------------------------------------------------- Giỏ hàng
st.divider()
st.subheader(f"🧺 Giỏ hàng ({len(gio)} căn)")
if gio:
    theo_ma = {c["id"]: c for c in can_ho}
    for ma in list(gio):
        c = theo_ma.get(ma)
        cot1, cot2 = st.columns([6, 1])
        cot1.write(f"#{ma} · {c['ten_duong']}, {c['khu_vuc']} · {dinh_dang_gia(c['gia_thue'])}"
                   if c else f"#{ma} (không còn trống)")
        if cot2.button("Bỏ", key=f"bo_{ma}"):
            gio.remove(ma)
            st.rerun()

    with st.form("tao_gio"):
        st.write("Thông tin khách")
        cot1, cot2 = st.columns(2)
        ten_khach = cot1.text_input("Tên khách *")
        sdt_khach = cot2.text_input("Số điện thoại / Zalo")
        nhu_cau = st.text_area("Nhu cầu", placeholder="Ví dụ: 2PN gần biển, dưới 12 triệu, có ban công")
        if st.form_submit_button("Tạo link gửi khách", type="primary"):
            if not ten_khach.strip():
                st.error("Chưa nhập tên khách.")
            else:
                khach = ghi(
                    """INSERT INTO khach_hang (ten, sdt, nhu_cau, ngan_sach_toi_da, ngay_don_vao)
                       VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (ten_khach.strip(), sdt_khach.strip() or None, nhu_cau.strip() or None,
                     round(gia_toi_da * 1_000_000) or None, ngay_don_vao),
                )
                # token_urlsafe: chuỗi ngẫu nhiên khó đoán, người lạ không mò ra giỏ của khách khác
                ma_link = secrets.token_urlsafe(8)
                gio_moi = ghi("INSERT INTO gio_hang (khach_hang_id, ma_link) VALUES (%s, %s) RETURNING id",
                              (khach["id"], ma_link))
                for ma in gio:
                    ghi("INSERT INTO gio_hang_can_ho (gio_hang_id, can_ho_id) VALUES (%s, %s)",
                        (gio_moi["id"], ma))
                st.session_state["link_vua_tao"] = ma_link
                st.session_state["gio"] = []
                st.rerun()

if ma_link := st.session_state.get("link_vua_tao"):
    goc = urlsplit(st.context.url)
    st.success("Đã tạo giỏ hàng. Copy link dưới đây gửi cho khách:")
    st.code(f"{goc.scheme}://{goc.netloc}/?gio={ma_link}", language=None)
