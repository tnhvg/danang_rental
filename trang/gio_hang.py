"""Trang Giỏ đã gửi: xem lại các giỏ đã tạo cho từng khách và lấy lại link."""

from urllib.parse import urlsplit

import streamlit as st

from csdl import doc

st.title("🧺 Giỏ đã gửi")

goc = urlsplit(st.context.url)
gio = doc("""
    SELECT g.ma_link, g.ngay_tao, k.ten, k.sdt, k.nhu_cau,
           count(gc.can_ho_id) AS so_can,
           count(*) FILTER (WHERE v.trang_thai_hom_nay IN ('còn trống', 'sắp trống')) AS con_trong
    FROM gio_hang g
    JOIN khach_hang k ON k.id = g.khach_hang_id
    LEFT JOIN gio_hang_can_ho gc ON gc.gio_hang_id = g.id
    LEFT JOIN v_can_ho v ON v.id = gc.can_ho_id
    GROUP BY g.id, k.id
    ORDER BY g.ngay_tao DESC
""")

if not gio:
    st.info("Chưa có giỏ nào. Vào trang 'Tìm căn & tạo giỏ' để tạo.")
for g in gio:
    with st.container(border=True):
        st.write(f"**{g['ten']}** {g['sdt'] or ''} · tạo ngày {g['ngay_tao']:%d/%m/%Y}")
        if g["nhu_cau"]:
            st.caption(g["nhu_cau"])
        st.write(f"{g['so_can']} căn, còn trống {g['con_trong']} căn")
        st.code(f"{goc.scheme}://{goc.netloc}/?gio={g['ma_link']}", language=None)
