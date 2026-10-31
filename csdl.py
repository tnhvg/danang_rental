"""Kết nối database (csdl = cơ sở dữ liệu).

Mọi trang của web đều đọc và ghi dữ liệu qua hai hàm `doc` và `ghi` ở đây,
nên muốn đổi cách kết nối chỉ cần sửa một file này.
"""

import os
import re
from pathlib import Path

import psycopg
import streamlit as st
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row


def _chuoi_ket_noi() -> str:
    # Trên Streamlit Cloud: lấy từ mục Secrets. Trên máy: lấy từ biến môi trường.
    try:
        chuoi = st.secrets["DATABASE_URL"]
    except (KeyError, FileNotFoundError):
        chuoi = os.environ.get("DATABASE_URL")
    if not chuoi:
        st.error("Chưa cài **DATABASE_URL** (chuỗi kết nối Supabase) trong mục Secrets.")
        st.stop()
    if "xxxx" in chuoi or "MAT_KHAU_DATABASE" in chuoi or "[YOUR-PASSWORD]" in chuoi:
        st.error("DATABASE_URL vẫn còn **phần giữ chỗ** (`xxxx`, `MAT_KHAU_DATABASE` hoặc `[YOUR-PASSWORD]`). "
                 "Vào Supabase → Connect → Direct → Session pooler, copy nguyên chuỗi thật, "
                 "rồi thay `[YOUR-PASSWORD]` bằng mật khẩu database.")
        st.stop()
    return chuoi


# Lỗi kết nối hay gặp: (đoạn chữ trong lỗi gốc, giải thích và cách sửa)
LOI_KET_NOI = [
    ("password authentication failed",
     "Sai **mật khẩu database** trong DATABASE_URL. Kiểm tra lại phần mật khẩu, nhớ bỏ dấu `[ ]`. "
     "Quên mật khẩu thì vào Supabase → Project Settings → Database → Reset database password."),
    ("Tenant or user not found",
     "Sai **tên người dùng** trong DATABASE_URL. Với Session pooler, tên phải có dạng `postgres.` + mã "
     "project, hãy copy lại nguyên chuỗi từ Supabase (Connect → Direct → Session pooler)."),
    ("tenant/user",  # câu chữ mới của Supabase: "(ENOTFOUND) tenant/user ... not found"
     "Sai **tên người dùng** trong DATABASE_URL. Với Session pooler, tên phải có dạng `postgres.` + mã "
     "project, hãy copy lại nguyên chuỗi từ Supabase (Connect → Direct → Session pooler)."),
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


# Các file SQL web tự chạy khi khởi động, để không phải vào Supabase chạy tay
FILE_CAP_NHAT = [Path(__file__).parent / "sql" / "04_don_gian_hoa.sql"]
_da_cap_nhat_cau_truc = False


def _ket_noi():
    global _da_cap_nhat_cau_truc
    # prepare_threshold=None: tắt "câu lệnh chuẩn bị sẵn", vì cổng kết nối
    # (pooler) của Supabase không hỗ trợ.
    chuoi = _chuoi_ket_noi()
    try:
        # Spinner chỉ hiện nếu kết nối lâu hơn nửa giây, nên bình thường không thấy
        with st.spinner("Đang kết nối database..."):
            kn = psycopg.connect(chuoi, row_factory=dict_row, prepare_threshold=None, connect_timeout=10)
            if not _da_cap_nhat_cau_truc:
                for tep in FILE_CAP_NHAT:
                    kn.execute(tep.read_text(encoding="utf-8"))
                kn.commit()
                _da_cap_nhat_cau_truc = True
            return kn
    except psycopg.Error as loi:
        _dung_vi_loi(loi, chuoi)


def _an_mat_khau(van_ban: str, chuoi: str) -> str:
    """Xoá mật khẩu khỏi nội dung lỗi trước khi hiện lên màn hình."""
    try:
        mat_khau = conninfo_to_dict(chuoi).get("password")
    except psycopg.Error:
        mat_khau = None
    if mat_khau:
        van_ban = van_ban.replace(mat_khau, "***")
    # Phòng trường hợp chuỗi sai định dạng: che phần giữa "://tên:" và "@"
    return re.sub(r'(//[^:/@\s"]+:)[^@\s"]+@', r"\1***@", van_ban)


def _dung_vi_loi(loi: Exception, chuoi: str = ""):
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
    # Lỗi chưa có trong danh sách: hiện nội dung gốc (đã che mật khẩu) để chụp màn hình gửi đi
    st.error("Không kết nối được database. Chụp màn hình phần chi tiết bên dưới gửi người viết code.")
    st.code(f"{type(loi).__name__}: {_an_mat_khau(goc, chuoi)}", language=None)
    st.stop()


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
