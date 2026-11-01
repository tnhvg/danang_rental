"""Thành phần giao diện dùng chung: trình xem ảnh có mũi tên, thẻ căn hộ cao bằng nhau.

Dùng ở trang Danh sách (quản lý) và trang khách xem.
"""

import html
import time

import streamlit as st

from csdl import doc

THOI_DIEM_NAP = time.time()  # app.py dùng để biết file này có bị sửa sau khi nạp không

CHU = {
    "truoc": {"vi": "Ảnh trước", "en": "Previous photo"},
    "sau": {"vi": "Ảnh sau", "en": "Next photo"},
    "phong_to": {"vi": "🔍 Phóng to ảnh", "en": "🔍 Enlarge photo"},
    "goi_y": {"vi": "Trên điện thoại: dùng hai ngón tay để zoom. Trên máy tính: bấm biểu tượng ⛶ ở góc ảnh.",
              "en": "On phone: pinch with two fingers to zoom. On computer: click the ⛶ icon on the photo."},
}

# CSS (quy tắc trình bày) chèn vào trang:
# - .st-key-mui_ten_...: hàng [◀ ảnh ▶] KHÔNG xếp chồng trên điện thoại (mặc định Streamlit xếp
#   các cột thành hàng dọc khi màn hình hẹp, mũi tên sẽ rơi xuống dưới ảnh).
# - .the-*: chữ trong thẻ căn hộ bị cắt bằng dấu "..." để mọi thẻ cao bằng nhau.
CSS = """
<style>
div[class*="st-key-mui_ten_"] [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.4rem; }
div[class*="st-key-mui_ten_"] [data-testid="stColumn"] { min-width: 0 !important; }
div[class*="st-key-mui_ten_"] button { padding-left: 0; padding-right: 0; min-height: 3rem; }
div[class*="st-key-mui_ten_"] button p { font-size: 1.4rem; }
.the-dong { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.6; }
.the-hai-dong { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
                line-height: 1.45; height: 2.9em; font-size: 0.875rem; opacity: 0.65; margin-bottom: 0.5rem; }
</style>
"""


def chen_css() -> None:
    st.html(CSS)


@st.cache_data(ttl=600, max_entries=30, show_spinner=False)
def anh_cua_can(can_ho_id: int) -> list[bytes]:
    """Toàn bộ ảnh của một căn. Lưu tạm 10 phút để bấm mũi tên không phải tải lại từ database.

    max_entries=30: chỉ nhớ ảnh của 30 căn gần nhất, tránh tốn bộ nhớ của web.
    Thêm ảnh mới cho căn thì gọi anh_cua_can.clear() để xoá bản lưu tạm.
    """
    return [bytes(a["du_lieu"]) for a in
            doc("SELECT du_lieu FROM anh_can_ho WHERE can_ho_id = %s ORDER BY thu_tu, id", (can_ho_id,))]


def _doi_anh(khoa: str, buoc: int, so_anh: int) -> None:
    # Chạy TRƯỚC khi vẽ lại, nên ảnh hiện ra đã là ảnh mới. % so_anh: qua ảnh cuối thì quay về ảnh đầu.
    st.session_state[khoa] = (st.session_state.get(khoa, 0) + buoc) % so_anh


def _anh_va_mui_ten(anh: list[bytes], khoa: str, nn: str, ten_hang: str) -> None:
    i = st.session_state.get(khoa, 0) % len(anh)
    if len(anh) == 1:
        st.image(anh[0], width="stretch")
        return
    with st.container(key=ten_hang):
        trai, giua, phai = st.columns([1.3, 8, 1.3], vertical_alignment="center")
        trai.button("◀", key=f"{ten_hang}_truoc", help=CHU["truoc"][nn], width="stretch",
                    on_click=_doi_anh, args=(khoa, -1, len(anh)))
        giua.image(anh[i], width="stretch")
        phai.button("▶", key=f"{ten_hang}_sau", help=CHU["sau"][nn], width="stretch",
                    on_click=_doi_anh, args=(khoa, 1, len(anh)))
    st.markdown(f"<div style='text-align:center; opacity:0.7'>{i + 1} / {len(anh)}</div>",
                unsafe_allow_html=True)


@st.dialog("📷", width="large")
def _hop_thoai_anh(anh: list[bytes], khoa: str, nn: str) -> None:
    """Cửa sổ nổi hiện ảnh cỡ lớn, có mũi tên chuyển ảnh ngay trong cửa sổ."""
    _anh_va_mui_ten(anh, khoa, nn, f"mui_ten_lon_{khoa}")
    st.caption(CHU["goi_y"][nn])


@st.fragment
def xem_anh(anh: list[bytes], khoa: str, nn: str = "vi") -> None:
    """Ảnh lớn có mũi tên ◀ ▶ hai bên, số thứ tự ảnh bên dưới, nút Phóng to.

    @st.fragment: bấm mũi tên chỉ vẽ lại phần ảnh này, không chạy lại cả trang nên nhanh hơn.
    khoa: tên riêng cho mỗi căn (ví dụ "anh_12") để các căn không nhớ lẫn ảnh đang xem của nhau.
    """
    if not anh:
        return
    _anh_va_mui_ten(anh, khoa, nn, f"mui_ten_{khoa}")
    if st.button(CHU["phong_to"][nn], key=f"{khoa}_nut_to"):
        _hop_thoai_anh(anh, khoa, nn)


def the_chu(cac_dong: list[str], dac_diem: str) -> None:
    """Phần chữ của thẻ căn hộ. cac_dong đã là HTML an toàn; dac_diem là chữ thường.

    Mỗi dòng trong cac_dong cắt bằng "..." nếu dài quá một dòng, đặc điểm tối đa hai dòng.
    """
    st.markdown("".join(f"<div class='the-dong'>{d}</div>" for d in cac_dong)
                + f"<div class='the-hai-dong'>{html.escape(dac_diem)}</div>", unsafe_allow_html=True)
