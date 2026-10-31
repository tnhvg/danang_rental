"""Điểm bắt đầu của web. Chạy bằng lệnh: streamlit run app.py

Web có hai phần:
- Link có ?gio=... : trang khách xem giỏ hàng, không cần đăng nhập.
- Còn lại       : trang quản lý, phải nhập mật khẩu.
"""

import hmac
import os

import streamlit as st

st.set_page_config(page_title="Căn hộ Đà Nẵng", page_icon="🏠", layout="wide")


def _mat_khau_dung() -> str:
    try:
        return st.secrets["MAT_KHAU"]
    except (KeyError, FileNotFoundError):
        pass
    if "MAT_KHAU" in os.environ:
        return os.environ["MAT_KHAU"]
    st.error("Chưa cài **MAT_KHAU** trong mục Secrets. Vào Manage app → Settings → Secrets để thêm, "
             "theo mẫu trong file `.streamlit/secrets.toml.example`.")
    st.stop()


def da_dang_nhap() -> bool:
    if st.session_state.get("da_dang_nhap"):
        return True
    st.title("🏠 Quản lý căn hộ Đà Nẵng")
    with st.form("dang_nhap"):
        mat_khau = st.text_input("Mật khẩu", type="password")
        if st.form_submit_button("Đăng nhập"):
            # compare_digest: so sánh an toàn, không để lộ mật khẩu qua thời gian so sánh
            if hmac.compare_digest(mat_khau, _mat_khau_dung()):
                st.session_state["da_dang_nhap"] = True
                st.rerun()
            st.error("Sai mật khẩu.")
    return False


ma_gio = st.query_params.get("gio")
if ma_gio:
    from trang.khach_xem import hien_gio_hang

    hien_gio_hang(ma_gio)
    st.stop()

if not da_dang_nhap():
    st.stop()

trang = st.navigation({
    "Căn hộ": [
        st.Page("trang/them_can_ho.py", title="Thêm căn hộ", icon="➕", default=True),
        st.Page("trang/danh_sach_can_ho.py", title="Danh sách căn hộ", icon="📋"),
    ],
    "Tư vấn khách": [
        st.Page("trang/tim_can.py", title="Tìm căn trên bản đồ & tạo giỏ", icon="🗺️"),
        st.Page("trang/gio_hang.py", title="Giỏ đã gửi khách", icon="🧺"),
    ],
    "Khác": [
        st.Page("trang/toa_nha.py", title="Vị trí trên bản đồ", icon="📍"),
        st.Page("trang/lien_he.py", title="Người gửi căn", icon="📇"),
    ],
})
trang.run()
