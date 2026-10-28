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
        return os.environ["DATABASE_URL"]


def _ket_noi():
    # prepare_threshold=None: tắt "câu lệnh chuẩn bị sẵn", vì cổng kết nối
    # (pooler) của Supabase không hỗ trợ.
    return psycopg.connect(_chuoi_ket_noi(), row_factory=dict_row, prepare_threshold=None)


def doc(sql: str, tham_so=None) -> list[dict]:
    """Chạy câu SELECT, trả về danh sách các dòng. Mỗi dòng là một dict {tên cột: giá trị}."""
    with _ket_noi() as kn:
        return kn.execute(sql, tham_so).fetchall()


def ghi(sql: str, tham_so=None) -> dict | None:
    """Chạy INSERT/UPDATE/DELETE. Nếu câu lệnh có RETURNING thì trả về dòng đầu tiên."""
    with _ket_noi() as kn:
        con_tro = kn.execute(sql, tham_so)
        return con_tro.fetchone() if con_tro.description else None
