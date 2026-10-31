"""Trang khách xem giỏ hàng (mở bằng link ?gio=...).

Trang này CHỈ đọc những cột khách được phép thấy: không có số căn, số nhà,
thông tin chủ nhà, ghi chú riêng hay hoa hồng.
"""

import os

import folium
import streamlit as st
from streamlit_folium import st_folium

from csdl import doc
from tien_ich import dinh_dang_gia, mo_ta_trang_thai, vi_tri_gan_dung

BAN_KINH_M = 300  # vòng tròn khu vực khách thấy trên bản đồ


def _sdt_zalo() -> str | None:
    try:
        return st.secrets["SDT_ZALO"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("SDT_ZALO")


def hien_gio_hang(ma_link: str) -> None:
    khach = doc("""
        SELECT g.id, k.ten FROM gio_hang g JOIN khach_hang k ON k.id = g.khach_hang_id
        WHERE g.ma_link = %s
    """, (ma_link,))
    if not khach:
        st.error("Link không đúng hoặc đã hết hạn. Bạn nhắn lại cho mình để nhận link mới nhé.")
        return

    can_ho = doc("""
        SELECT v.id, v.toa_nha_id, v.so_phong_ngu, v.so_phong_tam, v.dien_tich, v.tang, v.gia_thue,
               v.ban_cong, v.phong_tam_vach_kinh, v.bon_tam, v.may_giat_rieng, v.cho_nuoi_thu_cung,
               v.huong_view, v.noi_that, v.mo_ta, v.trang_thai_hom_nay, v.ngay_trong,
               v.ten_duong, v.khu_vuc, v.vi_do, v.kinh_do, v.loai_hinh,
               v.thang_may, v.ho_boi, v.gym, v.cho_de_o_to
        FROM gio_hang_can_ho gc JOIN v_can_ho v ON v.id = gc.can_ho_id
        WHERE gc.gio_hang_id = %s
        -- Căn còn trống lên trước, căn đã có người thuê xuống cuối
        ORDER BY v.trang_thai_hom_nay NOT IN ('còn trống', 'sắp trống'), v.gia_thue
    """, (khach[0]["id"],))

    st.title(f"🏠 Căn hộ chọn riêng cho {khach[0]['ten']}")
    sdt = _sdt_zalo()
    if sdt:
        st.markdown(f"Thích căn nào, bạn nhắn **mã căn** qua Zalo [{sdt}](https://zalo.me/{sdt}) "
                    "để mình hẹn lịch đi xem nhé.")

    # Bản đồ: mỗi căn là một vòng tròn khu vực, không phải điểm chính xác
    ban_do = folium.Map(location=[16.054, 108.225], zoom_start=13)
    diem = []
    for c in can_ho:
        if c["vi_do"] is None:
            continue
        vi_tri = vi_tri_gan_dung(c["toa_nha_id"], c["vi_do"], c["kinh_do"])
        diem.append(vi_tri)
        folium.Circle(vi_tri, radius=BAN_KINH_M, color="#2563eb", fill=True, fill_opacity=0.2,
                      tooltip=f"Căn #{c['id']} · {dinh_dang_gia(c['gia_thue'])}").add_to(ban_do)
    if diem:  # không căn nào có vị trí thì bỏ hẳn bản đồ
        ban_do.fit_bounds(diem, max_zoom=15)
        st_folium(ban_do, height=380, use_container_width=True, returned_objects=[], key="ban_do_khach")

    for c in can_ho:
        con_hieu_luc = c["trang_thai_hom_nay"] in ("còn trống", "sắp trống")
        with st.container(border=True):
            phong = "Studio" if c["so_phong_ngu"] == 0 else f"{c['so_phong_ngu']} phòng ngủ"
            tieu_de = f"Căn #{c['id']} · {phong} · {dinh_dang_gia(c['gia_thue'])}/tháng"
            trang_thai = mo_ta_trang_thai(c["trang_thai_hom_nay"], c["ngay_trong"])
            if not con_hieu_luc:
                # Căn đã có người thuê: vẫn hiện nhưng mờ đi, để khách hiểu vì sao
                st.markdown(f"~~{tieu_de}~~ · :gray[**{trang_thai}**]")
                continue
            st.markdown(f"### {tieu_de}")
            st.markdown(f":green[**{trang_thai}**] · {c['ten_duong']}, {c['khu_vuc']}")

            anh = doc("SELECT du_lieu FROM anh_can_ho WHERE can_ho_id = %s ORDER BY thu_tu", (c["id"],))
            if anh:
                st.image(bytes(anh[0]["du_lieu"]), width="stretch")
                if len(anh) > 1:
                    with st.expander(f"Xem thêm {len(anh) - 1} ảnh"):
                        st.image([bytes(a["du_lieu"]) for a in anh[1:]], width=300)

            dac_diem = [
                f"{float(c['dien_tich']):g} m²" if c["dien_tich"] else None,
                f"{c['so_phong_tam']} phòng tắm",
                f"tầng {c['tang']}" if c["tang"] else None,
                f"view {c['huong_view']}" if c["huong_view"] != "không có view" else None,
                f"nội thất {c['noi_that']}",
                "ban công" if c["ban_cong"] else None,
                "phòng tắm vách kính" if c["phong_tam_vach_kinh"] else None,
                "bồn tắm" if c["bon_tam"] else None,
                "máy giặt riêng" if c["may_giat_rieng"] else None,
                "cho nuôi thú cưng" if c["cho_nuoi_thu_cung"] else None,
            ]
            tien_ich_toa = [ten for ten, co in [("thang máy", c["thang_may"]), ("hồ bơi", c["ho_boi"]),
                                                ("gym", c["gym"]), ("chỗ để ô tô", c["cho_de_o_to"])] if co]
            st.write(" · ".join(d for d in dac_diem if d))
            if tien_ich_toa:
                st.write("Tòa nhà có: " + ", ".join(tien_ich_toa))
            if c["mo_ta"]:
                st.write(c["mo_ta"])
