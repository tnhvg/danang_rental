"""Các hàm nhỏ dùng chung: định dạng giá, nén ảnh, hoa hồng, vị trí gần đúng, tìm tọa độ."""

import io
import random
import time
from datetime import date

import requests
from PIL import Image, ImageOps

THOI_DIEM_NAP = time.time()  # app.py dùng để biết file này có bị sửa sau khi nạp không

TAM_DA_NANG = (16.054, 108.225)
TY_LE_HOA_HONG = 0.083


def dinh_dang_gia(gia: int) -> str:
    """7000000 -> '7 triệu', 7500000 -> '7,5 triệu', 6972000 -> '6,97 triệu'."""
    trieu = round(gia / 1_000_000, 2)
    return f"{trieu:g}".replace(".", ",") + " triệu"


def hoa_hong(gia_thue: int, so_thang: int, ty_le_huong: float) -> int:
    """Hoa hồng = giá thuê × số tháng × 8,3% × tỷ lệ được hưởng (1 nếu trực tiếp, 0,5 nếu qua trung gian)."""
    return round(gia_thue * so_thang * TY_LE_HOA_HONG * ty_le_huong)


def mo_ta_trang_thai(trang_thai_hom_nay: str, ngay_trong: date | None) -> str:
    if trang_thai_hom_nay == "còn trống":
        return "Còn trống"
    if trang_thai_hom_nay == "sắp trống":
        return f"Trống từ {ngay_trong:%d/%m}"
    return "Đã có người thuê"


def nen_anh(du_lieu: bytes, canh_dai_nhat: int = 1280, chat_luong: int = 75) -> bytes:
    """Thu nhỏ ảnh chụp điện thoại (thường 3–5 MB) xuống khoảng 100–200 KB."""
    anh = Image.open(io.BytesIO(du_lieu))
    anh = ImageOps.exif_transpose(anh)  # xoay đúng chiều ảnh chụp dọc
    anh = anh.convert("RGB")             # bỏ nền trong suốt để lưu được JPEG
    anh.thumbnail((canh_dai_nhat, canh_dai_nhat))
    dau_ra = io.BytesIO()
    anh.save(dau_ra, format="JPEG", quality=chat_luong, optimize=True)
    return dau_ra.getvalue()


def vi_tri_gan_dung(toa_nha_id: int, vi_do: float, kinh_do: float) -> tuple[float, float]:
    """Dời vị trí đi tối đa khoảng 150 m để khách không biết chính xác tòa nào.

    Dùng toa_nha_id làm "hạt giống" ngẫu nhiên, nên cùng một tòa luôn bị dời
    đúng một kiểu: khách mở link nhiều lần cũng không đoán ra được vị trí thật.
    """
    ngau_nhien = random.Random(toa_nha_id)
    return (
        float(vi_do) + ngau_nhien.uniform(-0.0013, 0.0013),
        float(kinh_do) + ngau_nhien.uniform(-0.0013, 0.0013),
    )


def tim_toa_do(dia_chi: str) -> tuple[float, float] | None:
    """Đổi địa chỉ thành (vĩ độ, kinh độ) bằng dịch vụ miễn phí Nominatim của OpenStreetMap.

    Trả về None nếu không tìm thấy hoặc mất mạng. Khi đó người dùng tự bấm vị trí trên bản đồ.
    """
    try:
        phan_hoi = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{dia_chi}, Đà Nẵng, Việt Nam", "format": "json", "limit": 1},
            headers={"User-Agent": "danang_rental (quản lý căn hộ cá nhân)"},
            timeout=10,
        )
        ket_qua = phan_hoi.json()
    except (requests.RequestException, ValueError):
        return None
    if not ket_qua:
        return None
    return float(ket_qua[0]["lat"]), float(ket_qua[0]["lon"])
