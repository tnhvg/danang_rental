"""Trang Tòa nhà: thêm tòa mới và ghim vị trí lên bản đồ.

Không dùng st.form ở trang này vì bản đồ nằm trong form thì không bấm được.
Các ô nhập được giữ lại nhờ st.session_state (bộ nhớ của trang trong lúc đang mở).
"""

import folium
import streamlit as st
from streamlit_folium import st_folium

from csdl import doc, ghi
from tien_ich import TAM_DA_NANG, tim_toa_do

st.title("🏢 Tòa nhà")

khu_vuc = doc("SELECT id, ten FROM khu_vuc ORDER BY ten")
duong_da_co = [d["ten_duong"] for d in doc("SELECT DISTINCT ten_duong FROM toa_nha ORDER BY ten_duong")]

st.subheader("Thêm tòa nhà")
cot1, cot2, cot3 = st.columns([1, 2, 2])
so_nha = cot1.text_input("Số nhà", placeholder="12 hoặc K45/2")
# accept_new_options: chọn tên đường đã có (tránh gõ sai chính tả) hoặc gõ tên đường mới
ten_duong = cot2.selectbox("Tên đường *", duong_da_co, index=None, accept_new_options=True,
                           placeholder="Chọn hoặc gõ tên đường mới")
chon_khu = cot3.selectbox("Khu vực *", khu_vuc, index=None, format_func=lambda k: k["ten"])

cot1, cot2 = st.columns(2)
ten_toa = cot1.text_input("Tên tòa (nếu có)")
loai_hinh = cot2.selectbox("Loại hình *", ["căn hộ dịch vụ", "chung cư", "nhà nguyên căn"])

st.write("Tiện ích trong tòa")
c1, c2, c3, c4 = st.columns(4)
thang_may = c1.checkbox("Thang máy")
ho_boi = c2.checkbox("Hồ bơi")
gym = c3.checkbox("Gym")
cho_de_o_to = c4.checkbox("Chỗ để ô tô")
gan_cong_trinh = st.checkbox("Gần công trình đang xây (ồn)")

# --- Vị trí ---
st.write("**Vị trí:** bấm *Tìm theo địa chỉ*, rồi bấm lên bản đồ để chỉnh lại cho đúng chỗ.")
if st.button("🔍 Tìm theo địa chỉ", disabled=not ten_duong):
    toa_do = tim_toa_do(f"{so_nha} {ten_duong}".strip())
    if toa_do:
        st.session_state["vi_tri_moi"] = toa_do
    else:
        st.warning("Không tìm thấy địa chỉ. Bạn bấm trực tiếp lên bản đồ để chọn vị trí.")

vi_tri = st.session_state.get("vi_tri_moi")
ban_do = folium.Map(location=vi_tri or TAM_DA_NANG, zoom_start=17 if vi_tri else 13)
if vi_tri:
    folium.Marker(vi_tri, tooltip="Vị trí tòa nhà").add_to(ban_do)
ket_qua = st_folium(ban_do, height=400, use_container_width=True,
                    returned_objects=["last_clicked"], key="ban_do_toa_nha")
if ket_qua and ket_qua.get("last_clicked"):
    diem_bam = (ket_qua["last_clicked"]["lat"], ket_qua["last_clicked"]["lng"])
    if diem_bam != vi_tri:
        st.session_state["vi_tri_moi"] = diem_bam
        st.rerun()

if st.button("Lưu tòa nhà", type="primary"):
    if not (ten_duong and chon_khu and vi_tri):
        st.error("Cần có tên đường, khu vực và vị trí trên bản đồ.")
    else:
        ghi(
            """INSERT INTO toa_nha (ten_toa, loai_hinh, so_nha, ten_duong, khu_vuc_id, vi_do, kinh_do,
                                   thang_may, ho_boi, gym, cho_de_o_to, gan_cong_trinh, ngay_ghi_nhan_cong_trinh)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                       CASE WHEN %s THEN current_date END)""",
            (ten_toa.strip() or None, loai_hinh, so_nha.strip() or None, ten_duong.strip(), chon_khu["id"],
             round(vi_tri[0], 6), round(vi_tri[1], 6),
             thang_may, ho_boi, gym, cho_de_o_to, gan_cong_trinh, gan_cong_trinh),
        )
        st.session_state.pop("vi_tri_moi", None)
        st.success("Đã lưu tòa nhà.")

st.subheader("Danh sách tòa nhà")
st.dataframe(doc("""
    SELECT coalesce(t.ten_toa, '') AS "Tên", concat_ws(' ', t.so_nha, t.ten_duong) AS "Địa chỉ",
           k.ten AS "Khu vực", t.loai_hinh AS "Loại", count(c.id) AS "Số căn"
    FROM toa_nha t JOIN khu_vuc k ON k.id = t.khu_vuc_id LEFT JOIN can_ho c ON c.toa_nha_id = t.id
    GROUP BY t.id, k.ten ORDER BY k.ten, t.ten_duong
"""), hide_index=True, width="stretch")
