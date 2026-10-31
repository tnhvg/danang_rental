"""Kết nối database (csdl = cơ sở dữ liệu).

Mọi trang của web đều đọc và ghi dữ liệu qua hai hàm `doc` và `ghi` ở đây,
nên muốn đổi cách kết nối chỉ cần sửa một file này.
"""

import os

import psycopg
import streamlit as st
from psycopg.rows import dict_row


def _chuoi_ket_noi() -> str:
    # Trên Streamlit Cloud: lấy từ mục Secrets. Trên máy: lấy từ biến môi trường.
    try:
        return st.secrets["DATABASE_URL"]
    except (KeyError, FileNotFoundError):
        pass
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    st.error("Chưa cài **DATABASE_URL** (chuỗi kết nối Supabase) trong mục Secrets.")
    st.stop()


# Lỗi kết nối hay gặp: (đoạn chữ trong lỗi gốc, giải thích và cách sửa)
LOI_KET_NOI = [
    ("password authentication failed",
     "Sai **mật khẩu database** trong DATABASE_URL. Kiểm tra lại phần mật khẩu, nhớ bỏ dấu `[ ]`. "
     "Quên mật khẩu thì vào Supabase → Project Settings → Database → Reset database password."),
    ("Tenant or user not found",
     "Sai **tên người dùng** trong DATABASE_URL. Với Session pooler, tên phải có dạng `postgres.xxxx` "
     "(có dấu chấm và mã project), hãy copy lại nguyên chuỗi từ Supabase."),
    ("failed to resolve host",
     "Sai **địa chỉ máy chủ** trong DATABASE_URL. Nếu chuỗi có `db.xxxx.supabase.co` thì bạn đang dùng "
     "Direct connection: hãy chọn **Session pooler** (địa chỉ có chữ `pooler.supabase.com`)."),
    ("Network is unreachable",
     "Streamlit Cloud không tới được database. Hãy dùng chuỗi **Session pooler** thay cho Direct connection."),
    ("connection timeout expired",
     "Chờ 10 giây mà database **không trả lời**. Hai nguyên nhân hay gặp:\n"
     "1. DATABASE_URL đang dùng **Direct connection**: trong Supabase bấm Connect → Direct → chọn "
     "**Session pooler** rồi copy lại chuỗi (có chữ `pooler.supabase.com`).\n"
     "2. Project Supabase **đang tạm dừng** (paused): vào supabase.com, mở project, bấm **Restore**."),
    ('missing "=" after',
     "DATABASE_URL **sai định dạng**. Chuỗi phải bắt đầu bằng `postgresql://` và nằm trong dấu ngoặc kép."),
]


def _ket_noi():
    # prepare_threshold=None: tắt "câu lệnh chuẩn bị sẵn", vì cổng kết nối
    # (pooler) của Supabase không hỗ trợ.
    chuoi = _chuoi_ket_noi()
    try:
        # Spinner chỉ hiện nếu kết nối lâu hơn nửa giây, nên bình thường không thấy
        with st.spinner("Đang kết nối database..."):
            return psycopg.connect(chuoi, row_factory=dict_row, prepare_threshold=None, connect_timeout=10)
    except psycopg.Error as loi:
        _dung_vi_loi(loi)


def _dung_vi_loi(loi: Exception):
    """Đổi lỗi kỹ thuật thành lời giải thích tiếng Việt rồi dừng trang."""
    if isinstance(loi, psycopg.errors.UndefinedTable):
        st.error("Database **chưa có bảng**. Vào Supabase → SQL Editor, chạy lần lượt 3 file "
                 "`sql/01_bang_co_ban.sql`, `sql/02_can_ho_gio_hang.sql`, `sql/03_bao_mat.sql`.")
        st.stop()
    goc = str(loi)
    for doan_chu, giai_thich in LOI_KET_NOI:
        if doan_chu in goc:
            st.error(giai_thich)
            st.stop()
    raise loi  # lỗi lạ: để Streamlit hiện chi tiết, chụp màn hình gửi người viết code


def doc(sql: str, tham_so=None) -> list[dict]:
    """Chạy câu SELECT, trả về danh sách các dòng. Mỗi dòng là một dict {tên cột: giá trị}."""
    with _ket_noi() as kn:
        try:
            return kn.execute(sql, tham_so).fetchall()
        except psycopg.errors.UndefinedTable as loi:
            _dung_vi_loi(loi)


def ghi(sql: str, tham_so=None) -> dict | None:
    """Chạy INSERT/UPDATE/DELETE. Nếu câu lệnh có RETURNING thì trả về dòng đầu tiên."""
    with _ket_noi() as kn:
        try:
            con_tro = kn.execute(sql, tham_so)
        except psycopg.errors.UndefinedTable as loi:
            _dung_vi_loi(loi)
        return con_tro.fetchone() if con_tro.description else None
