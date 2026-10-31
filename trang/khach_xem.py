"""Trang khách xem giỏ hàng (mở bằng link ?gio=...). Mặc định tiếng Anh, có nút đổi sang tiếng Việt.

Trang này CHỈ đọc những cột khách được phép thấy: không có số căn, số nhà,
thông tin chủ nhà, ghi chú riêng hay hoa hồng.
"""

import os
import time

import folium
import streamlit as st
from streamlit_folium import st_folium

from csdl import doc
from tien_ich import vi_tri_gan_dung

THOI_DIEM_NAP = time.time()  # app.py dùng để biết file này có bị sửa sau khi nạp không

BAN_KINH_M = 300  # vòng tròn khu vực khách thấy trên bản đồ

# Mỗi câu chữ trên trang có hai bản: "en" (tiếng Anh) và "vi" (tiếng Việt)
CHU = {
    "link_sai": {"en": "This link is invalid or has expired. Please message me for a new link.",
                 "vi": "Link không đúng hoặc đã hết hạn. Bạn nhắn lại cho mình để nhận link mới nhé."},
    "tieu_de": {"en": "🏠 Apartments selected for {ten}", "vi": "🏠 Căn hộ chọn riêng cho {ten}"},
    "lien_he": {"en": "Like one? Send me its **number (#)** on Zalo [{sdt}](https://zalo.me/{sdt}) "
                      "and I will arrange a viewing.",
                "vi": "Thích căn nào, bạn nhắn **mã căn (#)** qua Zalo [{sdt}](https://zalo.me/{sdt}) "
                      "để mình hẹn lịch đi xem nhé."},
    "dia_chi_rieng": {"en": "📍 Circles on the map show the approximate area. "
                            "The exact address is shared when you book a viewing.",
                      "vi": "📍 Vòng tròn trên bản đồ là khu vực gần đúng. "
                            "Địa chỉ chính xác sẽ được gửi khi bạn hẹn đi xem."},
    "can": {"en": "Apartment", "vi": "Căn"},
    "thang": {"en": "month", "vi": "tháng"},
    "studio": {"en": "Studio", "vi": "Studio"},
    "phong_ngu": {"en": "{n} bedroom", "vi": "{n} phòng ngủ"},
    "phong_ngu_nhieu": {"en": "{n} bedrooms", "vi": "{n} phòng ngủ"},
    "con_trong": {"en": "Available now", "vi": "Còn trống"},
    "trong_tu": {"en": "Available from {ngay}", "vi": "Trống từ {ngay}"},
    "da_thue": {"en": "Already rented", "vi": "Đã có người thuê"},
    "them_anh": {"en": "See {n} more photos", "vi": "Xem thêm {n} ảnh"},
    "phong_tam": {"en": "{n} bathroom(s)", "vi": "{n} phòng tắm"},
    "tang": {"en": "floor {n}", "vi": "tầng {n}"},
    "toa_co": {"en": "Building amenities: ", "vi": "Tòa nhà có: "},
}
# Giá trị lưu trong database (tiếng Việt) -> chữ hiện cho khách
DICH = {
    "biển": {"en": "sea view", "vi": "view biển"},
    "sông": {"en": "river view", "vi": "view sông"},
    "núi": {"en": "mountain view", "vi": "view núi"},
    "thành phố": {"en": "city view", "vi": "view thành phố"},
    "đầy đủ": {"en": "fully furnished", "vi": "nội thất đầy đủ"},
    "cơ bản": {"en": "basic furniture", "vi": "nội thất cơ bản"},
    "không có": {"en": "unfurnished", "vi": "không có nội thất"},
    "ban_cong": {"en": "balcony", "vi": "ban công"},
    "phong_tam_vach_kinh": {"en": "glass shower", "vi": "phòng tắm vách kính"},
    "bon_tam": {"en": "bathtub", "vi": "bồn tắm"},
    "may_giat_rieng": {"en": "private washing machine", "vi": "máy giặt riêng"},
    "cho_nuoi_thu_cung": {"en": "pets allowed", "vi": "cho nuôi thú cưng"},
    "thang_may": {"en": "elevator", "vi": "thang máy"},
    "ho_boi": {"en": "swimming pool", "vi": "hồ bơi"},
    "gym": {"en": "gym", "vi": "gym"},
    "cho_de_o_to": {"en": "car parking", "vi": "chỗ để ô tô"},
}


def _sdt_zalo() -> str | None:
    try:
        return st.secrets["SDT_ZALO"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("SDT_ZALO")


def _gia(gia: int, nn: str) -> str:
    """Tiếng Anh: '7,000,000 VND'. Tiếng Việt: '7.000.000 đ'."""
    return f"{gia:,} VND" if nn == "en" else f"{gia:,} đ".replace(",", ".")


def hien_gio_hang(ma_link: str) -> None:
    nn = "vi" if st.segmented_control("Language", ["English", "Tiếng Việt"], default="English",
                                      label_visibility="collapsed") == "Tiếng Việt" else "en"

    def chu(khoa: str, **gia_tri) -> str:
        return CHU[khoa][nn].format(**gia_tri)

    khach = doc("""
        SELECT g.id, k.ten FROM gio_hang g JOIN khach_hang k ON k.id = g.khach_hang_id
        WHERE g.ma_link = %s
    """, (ma_link,))
    if not khach:
        st.error(chu("link_sai"))
        return

    can_ho = doc("""
        SELECT v.id, v.toa_nha_id, v.so_phong_ngu, v.so_phong_tam, v.dien_tich, v.tang, v.gia_thue,
               v.ban_cong, v.phong_tam_vach_kinh, v.bon_tam, v.may_giat_rieng, v.cho_nuoi_thu_cung,
               v.huong_view, v.noi_that, v.mo_ta, v.mo_ta_en, v.trang_thai_hom_nay, v.ngay_trong,
               v.ten_duong, v.khu_vuc, v.vi_do, v.kinh_do,
               v.thang_may, v.ho_boi, v.gym, v.cho_de_o_to
        FROM gio_hang_can_ho gc JOIN v_can_ho v ON v.id = gc.can_ho_id
        WHERE gc.gio_hang_id = %s
        -- Căn còn trống lên trước, căn đã có người thuê xuống cuối
        ORDER BY v.trang_thai_hom_nay NOT IN ('còn trống', 'sắp trống'), v.gia_thue
    """, (khach[0]["id"],))

    st.title(chu("tieu_de", ten=khach[0]["ten"]))
    sdt = _sdt_zalo()
    if sdt:
        st.markdown(chu("lien_he", sdt=sdt))

    # Bản đồ: mỗi căn là một vòng tròn khu vực, không phải điểm chính xác
    ban_do = folium.Map(location=[16.054, 108.225], zoom_start=13)
    diem = []
    for c in can_ho:
        if c["vi_do"] is None:
            continue
        vi_tri = vi_tri_gan_dung(c["toa_nha_id"], c["vi_do"], c["kinh_do"])
        diem.append(vi_tri)
        folium.Circle(vi_tri, radius=BAN_KINH_M, color="#2563eb", fill=True, fill_opacity=0.2,
                      tooltip=f"#{c['id']} · {_gia(c['gia_thue'], nn)}").add_to(ban_do)
    if diem:  # không căn nào có vị trí thì bỏ hẳn bản đồ
        ban_do.fit_bounds(diem, max_zoom=15)
        st_folium(ban_do, height=380, use_container_width=True, returned_objects=[], key="ban_do_khach")
    st.caption(chu("dia_chi_rieng"))

    for c in can_ho:
        n = c["so_phong_ngu"]
        phong = chu("studio") if n == 0 else chu("phong_ngu" if n == 1 else "phong_ngu_nhieu", n=n)
        tieu_de = f"{chu('can')} #{c['id']} · {phong} · {_gia(c['gia_thue'], nn)}/{chu('thang')}"
        with st.container(border=True):
            if c["trang_thai_hom_nay"] not in ("còn trống", "sắp trống"):
                # Căn đã có người thuê: vẫn hiện nhưng gạch ngang, để khách hiểu vì sao
                st.markdown(f"~~{tieu_de}~~ · :gray[**{chu('da_thue')}**]")
                continue
            trang_thai = chu("con_trong") if c["trang_thai_hom_nay"] == "còn trống" \
                else chu("trong_tu", ngay=f"{c['ngay_trong']:%d/%m}")
            st.markdown(f"### {tieu_de}")
            # Chỉ hiện tên đường và khu vực, KHÔNG hiện số nhà
            st.markdown(f":green[**{trang_thai}**] · {c['ten_duong']}, {c['khu_vuc']}")

            anh = doc("SELECT du_lieu FROM anh_can_ho WHERE can_ho_id = %s ORDER BY thu_tu, id", (c["id"],))
            if anh:
                st.image(bytes(anh[0]["du_lieu"]), width="stretch")
                if len(anh) > 1:
                    with st.expander(chu("them_anh", n=len(anh) - 1)):
                        st.image([bytes(a["du_lieu"]) for a in anh[1:]], width=300)

            dac_diem = [
                f"{float(c['dien_tich']):g} m²" if c["dien_tich"] else None,
                chu("phong_tam", n=c["so_phong_tam"]),
                chu("tang", n=c["tang"]) if c["tang"] else None,
                DICH[c["huong_view"]][nn] if c["huong_view"] in DICH else None,
                DICH[c["noi_that"]][nn],
                *[DICH[cot][nn] for cot in ("ban_cong", "phong_tam_vach_kinh", "bon_tam",
                                            "may_giat_rieng", "cho_nuoi_thu_cung") if c[cot]],
            ]
            st.write(" · ".join(d for d in dac_diem if d))
            tien_ich_toa = [DICH[cot][nn] for cot in ("thang_may", "ho_boi", "gym", "cho_de_o_to") if c[cot]]
            if tien_ich_toa:
                st.write(chu("toa_co") + ", ".join(tien_ich_toa))
            # Mô tả: ưu tiên đúng ngôn ngữ khách chọn, không có thì dùng bản còn lại
            mo_ta = (c["mo_ta_en"] or c["mo_ta"]) if nn == "en" else (c["mo_ta"] or c["mo_ta_en"])
            if mo_ta:
                st.write(mo_ta)
