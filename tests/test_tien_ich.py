import io

from PIL import Image

from tien_ich import dinh_dang_gia, hoa_hong, nen_anh, vi_tri_gan_dung


def test_dinh_dang_gia():
    assert dinh_dang_gia(7_000_000) == "7 triệu"
    assert dinh_dang_gia(7_500_000) == "7,5 triệu"
    assert dinh_dang_gia(6_972_000) == "6,97 triệu"


def test_hoa_hong_truc_tiep_va_trung_gian():
    # 15 triệu × 12 tháng × 8,3% = 14,94 triệu; qua trung gian còn một nửa
    assert hoa_hong(15_000_000, 12, 1.0) == 14_940_000
    assert hoa_hong(15_000_000, 12, 0.5) == 7_470_000
    assert hoa_hong(15_000_000, 6, 1.0) == 7_470_000


def test_nen_anh_thu_nho_anh_lon():
    anh_goc = io.BytesIO()
    Image.new("RGB", (4000, 3000), "blue").save(anh_goc, format="PNG")
    anh_nen = Image.open(io.BytesIO(nen_anh(anh_goc.getvalue())))
    assert anh_nen.format == "JPEG"
    assert max(anh_nen.size) == 1280


def test_vi_tri_gan_dung_on_dinh_va_khong_qua_xa():
    lan_1 = vi_tri_gan_dung(7, 16.05, 108.24)
    lan_2 = vi_tri_gan_dung(7, 16.05, 108.24)
    assert lan_1 == lan_2  # cùng tòa luôn dời giống nhau
    assert lan_1 != (16.05, 108.24)  # nhưng không trùng vị trí thật
    assert abs(lan_1[0] - 16.05) < 0.002 and abs(lan_1[1] - 108.24) < 0.002
