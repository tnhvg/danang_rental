"""Trang Liên hệ: những người gửi căn cho tôi (chủ nhà, quản lý, trung gian)."""

import streamlit as st

from csdl import doc, ghi

st.title("📇 Liên hệ")
st.caption("Mỗi người chỉ nhập một lần. Người có vai trò 'trung gian' thì hoa hồng chia 50%.")

with st.form("them_lien_he", clear_on_submit=True):
    cot1, cot2 = st.columns(2)
    ten = cot1.text_input("Tên *")
    sdt = cot2.text_input("Số điện thoại")
    nhom_zalo = cot1.text_input("Tên group Zalo")
    vai_tro = cot2.selectbox("Vai trò *", ["chủ nhà", "quản lý", "trung gian"])
    ghi_chu = st.text_input("Ghi chú")
    if st.form_submit_button("Thêm liên hệ", type="primary"):
        if not ten.strip():
            st.error("Chưa nhập tên.")
        else:
            ghi(
                "INSERT INTO lien_he (ten, sdt, nhom_zalo, vai_tro, ghi_chu) VALUES (%s, %s, %s, %s, %s)",
                (ten.strip(), sdt.strip() or None, nhom_zalo.strip() or None, vai_tro, ghi_chu.strip() or None),
            )
            st.success(f"Đã thêm {ten}.")

danh_sach = doc("""
    SELECT l.ten AS "Tên", l.sdt AS "SĐT", l.nhom_zalo AS "Group Zalo", l.vai_tro AS "Vai trò",
           count(c.id) AS "Số căn đã gửi"
    FROM lien_he l LEFT JOIN can_ho c ON c.lien_he_id = l.id
    GROUP BY l.id ORDER BY l.ten
""")
st.dataframe(danh_sach, hide_index=True, width="stretch")
