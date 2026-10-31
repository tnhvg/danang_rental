"""Trang Vị trí trên bản đồ: ghim hoặc sửa vị trí cho các địa chỉ đã lưu.

Khi thêm căn, web tự tìm vị trí từ địa chỉ. Địa chỉ nào tìm không ra (hay ra sai)
thì vào đây bấm lên bản đồ để ghim lại.
Không dùng st.form ở trang này vì bản đồ nằm trong form thì không bấm được.
"""

import folium
import streamlit as st
from streamlit_folium import st_folium

from csdl import doc, ghi
from tien_ich import TAM_DA_NANG, tim_toa_do

st.title("📍 Vị trí trên bản đồ")

toa_nha = doc("""
    SELECT t.id, t.ten_toa, t.so_nha, t.ten_duong, t.vi_do, t.kinh_do, k.ten AS khu_vuc, count(c.id) AS so_can
    FROM toa_nha t JOIN khu_vuc k ON k.id = t.khu_vuc_id LEFT JOIN can_ho c ON c.toa_nha_id = t.id
    GROUP BY t.id, k.ten
    ORDER BY t.vi_do IS NOT NULL, k.ten, t.ten_duong   -- địa chỉ chưa có vị trí lên đầu
""")
if not toa_nha:
    st.info("Chưa có địa chỉ nào. Thêm căn ở trang ➕ Thêm căn hộ, địa chỉ sẽ tự xuất hiện ở đây.")
    st.stop()

chua_co = sum(t["vi_do"] is None for t in toa_nha)
if chua_co:
    st.warning(f"{chua_co} địa chỉ chưa có vị trí trên bản đồ (đánh dấu ❌ trong danh sách).")


def nhan(t: dict) -> str:
    dia_chi = " ".join(x for x in [t["so_nha"], t["ten_duong"]] if x)
    ten = f"{t['ten_toa']} · " if t["ten_toa"] else ""
    return f"{'✅' if t['vi_do'] is not None else '❌'} {ten}{dia_chi}, {t['khu_vuc']} ({t['so_can']} căn)"


toa = st.selectbox("Chọn địa chỉ", toa_nha, format_func=nhan)

# Mỗi địa chỉ có một chỗ nhớ riêng cho điểm vừa bấm, đổi địa chỉ thì không bị lẫn
khoa = f"vi_tri_{toa['id']}"
if khoa not in st.session_state and toa["vi_do"] is not None:
    st.session_state[khoa] = (float(toa["vi_do"]), float(toa["kinh_do"]))
vi_tri = st.session_state.get(khoa)

c1, c2 = st.columns([1, 3])
if c1.button("🔍 Tìm lại theo địa chỉ"):
    toa_do = tim_toa_do(f"{toa['so_nha'] or ''} {toa['ten_duong']}, {toa['khu_vuc']}".strip())
    if toa_do:
        st.session_state[khoa] = toa_do
        st.rerun()
    st.warning("Không tìm thấy. Bạn bấm trực tiếp lên bản đồ để chọn vị trí.")
c2.caption("Bấm lên bản đồ đúng chỗ căn hộ, chấm đỏ sẽ dời tới đó, rồi bấm **Lưu vị trí**.")

ban_do = folium.Map(location=vi_tri or TAM_DA_NANG, zoom_start=17 if vi_tri else 13)
if vi_tri:
    folium.Marker(vi_tri, tooltip="Vị trí đang chọn", icon=folium.Icon(color="red")).add_to(ban_do)
ket_qua = st_folium(ban_do, height=450, use_container_width=True,
                    returned_objects=["last_clicked"], key=f"ban_do_{toa['id']}")
if ket_qua and ket_qua.get("last_clicked"):
    diem_bam = (ket_qua["last_clicked"]["lat"], ket_qua["last_clicked"]["lng"])
    if diem_bam != vi_tri:
        st.session_state[khoa] = diem_bam
        st.rerun()

if st.button("💾 Lưu vị trí", type="primary", disabled=vi_tri is None):
    ghi("UPDATE toa_nha SET vi_do = %s, kinh_do = %s WHERE id = %s",
        (round(vi_tri[0], 6), round(vi_tri[1], 6), toa["id"]))
    st.toast("Đã lưu vị trí ✅")
    st.rerun()
