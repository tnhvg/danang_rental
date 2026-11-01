"""Trang Danh sách căn hộ: các căn hiện dạng thẻ (ảnh bìa, vị trí, giá, đặc điểm).
Bấm "Xem chi tiết" để xem từng ảnh, toàn bộ thông tin, đổi trạng thái, thêm ảnh.
"""

import html
import io

import streamlit as st
from PIL import Image

from csdl import doc, ghi
from giao_dien import anh_cua_can, chen_css, the_chu, xem_anh
from tien_ich import dinh_dang_gia, hoa_hong, mo_ta_trang_thai, nen_anh, thu_nho

TRANG_THAI = ["còn trống", "sắp trống", "đã cọc", "đã cho thuê"]
SO_NGAY_CANH_BAO = 7
SO_CAN_MOI_LAN = 12   # mỗi lần hiện 12 thẻ, bấm "Xem thêm" để hiện tiếp
SO_COT = 3


@st.cache_data(ttl=3600, show_spinner=False)
def anh_bia(ds_id: tuple[int, ...]) -> dict[int, bytes]:
    """Ảnh bìa nhỏ của các căn đang hiện. Lưu tạm (cache) 1 giờ để không phải tải lại mỗi lần bấm."""
    dong = doc("""SELECT DISTINCT ON (can_ho_id) can_ho_id, du_lieu FROM anh_can_ho
                  WHERE can_ho_id = ANY(%s) ORDER BY can_ho_id, thu_tu, id""", (list(ds_id),))
    return {d["can_ho_id"]: thu_nho(bytes(d["du_lieu"])) for d in dong}


@st.cache_data(show_spinner=False)
def anh_trong() -> bytes:
    """Khung xám thay ảnh cho căn chưa có ảnh, để các thẻ vẫn cao bằng nhau."""
    dau_ra = io.BytesIO()
    Image.new("RGB", (480, 360), (226, 232, 240)).save(dau_ra, format="JPEG")
    return dau_ra.getvalue()


def ten_phong(c: dict) -> str:
    return "Studio" if c["so_phong_ngu"] == 0 else f"{c['so_phong_ngu']} phòng ngủ"


def dia_chi(c: dict) -> str:
    return ", ".join(x for x in [" ".join(y for y in [c["so_nha"], c["ten_duong"]] if y), c["khu_vuc"]] if x)


def dac_diem(c: dict) -> list[str]:
    ds = [
        f"{float(c['dien_tich']):g} m²" if c["dien_tich"] else None,
        f"view {c['huong_view']}" if c["huong_view"] != "không có view" else None,
        "ban công" if c["ban_cong"] else None,
        "cho nuôi thú cưng" if c["cho_nuoi_thu_cung"] else None,
        "phòng tắm vách kính" if c["phong_tam_vach_kinh"] else None,
        "bồn tắm" if c["bon_tam"] else None,
        "máy giặt riêng" if c["may_giat_rieng"] else None,
        "hồ bơi" if c["ho_boi"] else None,
        "gym" if c["gym"] else None,
        "thang máy" if c["thang_may"] else None,
        "chỗ để ô tô" if c["cho_de_o_to"] else None,
        f"nội thất {c['noi_that']}",
    ]
    return [d for d in ds if d]


def trang_thai_html(c: dict) -> str:
    """Trạng thái có màu, dạng HTML (dùng trong thẻ có cắt chữ)."""
    if c["trang_thai_hom_nay"] == "còn trống":
        return "<b style='color:#16a34a'>Còn trống</b>"
    if c["trang_thai_hom_nay"] == "sắp trống":
        return f"<b style='color:#ea580c'>{mo_ta_trang_thai('sắp trống', c['ngay_trong'])}</b>"
    return f"<b style='opacity:0.6'>{c['trang_thai_hom_nay'].capitalize()}</b>"


def trang_thai_mau(c: dict) -> str:
    """Trạng thái có màu: xanh = còn trống, cam = sắp trống, xám = đã cọc / đã thuê."""
    if c["trang_thai_hom_nay"] == "còn trống":
        return ":green[**Còn trống**]"
    if c["trang_thai_hom_nay"] == "sắp trống":
        return f":orange[**{mo_ta_trang_thai('sắp trống', c['ngay_trong'])}**]"
    return f":gray[**{c['trang_thai_hom_nay'].capitalize()}**]"


# ================================================================ Chi tiết một căn
def hien_chi_tiet(can_id: int) -> None:
    ket_qua = doc("SELECT * FROM v_can_ho WHERE id = %s", (can_id,))
    if st.button("← Quay lại danh sách"):
        del st.session_state["can_dang_xem"]
        st.rerun()
    if not ket_qua:
        st.error("Không tìm thấy căn này.")
        return
    can = ket_qua[0]
    st.subheader(f"📍 {dia_chi(can)}")
    st.markdown(f"#{can['id']} · **{ten_phong(can)} · {dinh_dang_gia(can['gia_thue'])}/tháng** · "
                + trang_thai_mau(can)
                + (f" · tòa {can['ten_toa']}" if can["ten_toa"] else "")
                + (f" · căn {can['ma_can']}" if can["ma_can"] else ""))

    cot_anh, cot_thong_tin = st.columns([3, 2])
    with cot_anh:
        anh = anh_cua_can(can["id"])
        if anh:
            xem_anh(anh, f"anh_{can['id']}")
        else:
            st.info("Căn này chưa có ảnh.")
        with st.form("them_anh", clear_on_submit=True):
            anh_moi = st.file_uploader("Thêm ảnh cho căn này", type=["jpg", "jpeg", "png", "webp"],
                                       accept_multiple_files=True)
            if st.form_submit_button("Tải ảnh lên") and anh_moi:
                for i, tep in enumerate(anh_moi):
                    ghi("INSERT INTO anh_can_ho (can_ho_id, du_lieu, thu_tu) VALUES (%s, %s, %s)",
                        (can["id"], nen_anh(tep.getvalue()), len(anh) + i))
                anh_bia.clear()      # ảnh bìa có thể đã đổi
                anh_cua_can.clear()  # xoá bản lưu tạm để thấy ảnh mới
                st.rerun()

    with cot_thong_tin:
        st.write(" · ".join([f"{can['so_phong_tam']} phòng tắm"]
                            + ([f"tầng {can['tang']}"] if can["tang"] else []) + dac_diem(can)))
        if can["mo_ta"]:
            st.write(f"**Mô tả:** {can['mo_ta']}")
        if can["mo_ta_en"]:
            st.write(f"**Mô tả tiếng Anh:** {can['mo_ta_en']}")
        if can["ghi_chu_noi_bo"]:
            st.write(f"**Ghi chú riêng:** {can['ghi_chu_noi_bo']}")
        if can["ten_lien_he"]:
            st.write(f"**Người gửi:** {can['ten_lien_he']} {can['sdt_lien_he'] or ''} ({can['vai_tro']})")
        st.write(f"**Hoa hồng nếu ký 12 tháng:** "
                 f"{dinh_dang_gia(hoa_hong(can['gia_thue'], 12, float(can['ty_le_huong'])))}")
        st.write(f"**Lần cuối hỏi chủ:** {can['so_ngay_chua_xac_nhan']} ngày trước")

        with st.form("cap_nhat"):
            st.write("**Cập nhật**")
            trang_thai_moi = st.selectbox("Trạng thái", TRANG_THAI, index=TRANG_THAI.index(can["trang_thai"]))
            ngay_trong_moi = st.date_input("Ngày trống (nếu sắp trống)", value=can["ngay_trong"],
                                           format="DD/MM/YYYY")
            gia_moi = st.number_input("Giá (triệu/tháng)", 0.5, 500.0, can["gia_thue"] / 1_000_000, step=0.5)
            mo_ta_moi = st.text_area("Mô tả (tiếng Việt)", value=can["mo_ta"] or "")
            mo_ta_en_moi = st.text_area("Mô tả tiếng Anh", value=can["mo_ta_en"] or "")
            st.caption("Bấm Lưu nghĩa là bạn vừa hỏi chủ xong: ngày xác nhận được đặt lại thành hôm nay.")
            if st.form_submit_button("Lưu", type="primary"):
                if trang_thai_moi == "sắp trống" and not ngay_trong_moi:
                    st.error("Căn 'sắp trống' cần có ngày trống.")
                else:
                    ghi("""UPDATE can_ho SET trang_thai = %s, ngay_trong = %s, gia_thue = %s, mo_ta = %s,
                               mo_ta_en = %s, ngay_xac_nhan = current_date WHERE id = %s""",
                        (trang_thai_moi, ngay_trong_moi if trang_thai_moi == "sắp trống" else None,
                         round(gia_moi * 1_000_000), mo_ta_moi.strip() or None, mo_ta_en_moi.strip() or None,
                         can["id"]))
                    st.toast("Đã lưu ✅")
                    st.rerun()


chen_css()

if "can_dang_xem" in st.session_state:
    hien_chi_tiet(st.session_state["can_dang_xem"])
    st.stop()

# ================================================================ Danh sách dạng thẻ
st.title("📋 Danh sách căn hộ")

c1, c2 = st.columns([3, 1])
tu_khoa = c1.text_input("🔍 Tìm theo tên đường, tên tòa, số căn, mô tả, ghi chú", placeholder="Ví dụ: Mỹ Đa")
hien_ca_da_thue = c2.toggle("Hiện cả căn đã cọc / đã thuê")

dieu_kien, tham_so = [], []
if not hien_ca_da_thue:
    dieu_kien.append("trang_thai_hom_nay IN ('còn trống', 'sắp trống')")
if tu_khoa.strip():
    # ILIKE: tìm không phân biệt chữ hoa chữ thường; % nghĩa là "bất kỳ chữ nào trước/sau"
    dieu_kien.append("""concat_ws(' ', ten_duong, ten_toa, ma_can, khu_vuc, mo_ta, mo_ta_en, ghi_chu_noi_bo,
                                  ten_lien_he)
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
    st.warning(f"⚠️ {len(can_kiem_tra)} căn đã hơn {SO_NGAY_CANH_BAO} ngày chưa hỏi lại chủ "
               "(thẻ có dấu ⚠️). Hỏi chủ xem còn trống không trước khi gửi khách.")

so_hien = st.session_state.get("so_can_hien", SO_CAN_MOI_LAN)
dang_hien = can_ho[:so_hien]
st.caption(f"Đang hiện {len(dang_hien)} / {len(can_ho)} căn, mới thêm lên trước.")
bia = anh_bia(tuple(c["id"] for c in dang_hien))

for dau_hang in range(0, len(dang_hien), SO_COT):
    for c, cot in zip(dang_hien[dau_hang:dau_hang + SO_COT], st.columns(SO_COT)):
        with cot.container(border=True):
            st.image(bia.get(c["id"], anh_trong()), width="stretch")
            # html.escape: chữ bạn gõ (tên đường...) được hiện đúng nguyên văn, không bị hiểu nhầm thành HTML
            canh_bao = " · ⚠️" if (c["so_ngay_chua_xac_nhan"] > SO_NGAY_CANH_BAO
                                   and c["trang_thai_hom_nay"] in ("còn trống", "sắp trống")) else ""
            phong = "Studio" if c["so_phong_ngu"] == 0 else f"{c['so_phong_ngu']} PN"
            # Trạng thái nằm dòng riêng để không bao giờ bị dấu "..." che mất
            the_chu([f"📍 <b>{html.escape(dia_chi(c))}</b>",
                     f"{phong} · <b>{dinh_dang_gia(c['gia_thue'])}/tháng</b>",
                     f"{trang_thai_html(c)}{canh_bao}"],
                    " · ".join(dac_diem(c)))
            if st.button("Xem chi tiết", key=f"xem_{c['id']}", width="stretch"):
                st.session_state["can_dang_xem"] = c["id"]
                st.rerun()

if len(can_ho) > so_hien:
    if st.button(f"Xem thêm {min(SO_CAN_MOI_LAN, len(can_ho) - so_hien)} căn", width="stretch"):
        st.session_state["so_can_hien"] = so_hien + SO_CAN_MOI_LAN
        st.rerun()
