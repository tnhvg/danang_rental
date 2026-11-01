"""Thành phần giao diện dùng chung: trình xem ảnh (dùng ở trang Danh sách và trang khách xem).

Không đưa nhiều ảnh vào MỘT lệnh st.image: làm vậy chúng dính thành một cụm, không xem riêng
từng ảnh được. Ở đây mỗi lúc chỉ hiện một ảnh lớn, chọn ảnh bằng các nút số.
"""

import time

import streamlit as st

THOI_DIEM_NAP = time.time()  # app.py dùng để biết file này có bị sửa sau khi nạp không

CHU = {
    "chon_anh": {"vi": "Chọn ảnh", "en": "Choose photo"},
    "phong_to": {"vi": "🔍 Phóng to ảnh", "en": "🔍 Enlarge photo"},
    "goi_y": {"vi": "Trên điện thoại: dùng hai ngón tay để zoom. Trên máy tính: bấm biểu tượng ⛶ ở góc ảnh.",
              "en": "On phone: pinch with two fingers to zoom. On computer: click the ⛶ icon on the photo."},
}


@st.dialog("📷", width="large")
def _hop_thoai_anh(anh: list[bytes], khoa: str, nn: str) -> None:
    """Cửa sổ nổi hiện ảnh cỡ lớn, chuyển ảnh ngay trong cửa sổ."""
    i = st.pills(CHU["chon_anh"][nn], list(range(1, len(anh) + 1)), required=True,
                 default=st.session_state.get(khoa, 1), key=f"{khoa}_lon",
                 label_visibility="collapsed", wrap=True) if len(anh) > 1 else 1
    st.image(anh[i - 1], width="stretch")
    st.caption(CHU["goi_y"][nn])


def xem_anh(anh: list[bytes], khoa: str, nn: str = "vi") -> None:
    """Hiện một ảnh lớn; phía trên là nút số 1, 2, 3... để đổi ảnh, phía dưới là nút Phóng to.

    khoa: tên riêng cho mỗi căn (ví dụ "anh_12") để các căn không nhớ lẫn ảnh đang chọn của nhau.
    """
    if not anh:
        return
    if len(anh) > 1:
        # wrap=True: nhiều ảnh thì các nút số xuống dòng, không bị khuất bên phải
        i = st.pills(CHU["chon_anh"][nn], list(range(1, len(anh) + 1)), required=True, default=1,
                     key=khoa, label_visibility="collapsed", wrap=True)
    else:
        i = 1
    st.image(anh[i - 1], width="stretch", caption=f"{i} / {len(anh)}")
    if st.button(CHU["phong_to"][nn], key=f"{khoa}_nut_to"):
        _hop_thoai_anh(anh, khoa, nn)
