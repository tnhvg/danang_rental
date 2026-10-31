"""Trang Thêm căn hộ: tải ảnh và điền thông tin trong MỘT form, bấm Lưu là xong.

Người dùng không cần tạo tòa nhà hay liên hệ trước. Khi lưu, web tự:
- tìm tòa nhà cùng địa chỉ đã có, chưa có thì tạo mới (và tự tìm vị trí trên bản đồ);
- tìm người gửi cùng số điện thoại / tên đã có, chưa có thì tạo mới.
"""

import streamlit as st

from csdl import doc, ghi
from tien_ich import nen_anh, tim_toa_do

st.title("➕ Thêm căn hộ")
st.caption("Ô có dấu * là bắt buộc. Các ô khác biết thì điền, không biết thì bỏ trống.")

khu_vuc = doc("SELECT id, ten FROM khu_vuc ORDER BY ten")
duong_da_co = [d["ten_duong"] for d in doc("SELECT DISTINCT ten_duong FROM toa_nha ORDER BY ten_duong")]


def chuan_hoa_duong(ten: str) -> str:
    """Gõ 'mỹ đa  đông 12' mà đã có 'Mỹ Đa Đông 12' thì dùng cách viết cũ, để không thành hai đường khác nhau."""
    ten = " ".join(ten.split())
    for da_co in duong_da_co:
        if da_co.lower() == ten.lower():
            return da_co
    return ten


def tim_hoac_tao_toa_nha(so_nha, ten_duong, khu, ten_toa, loai_hinh, tien_ich) -> tuple[int, bool]:
    """Trả về (id tòa nhà, có tìm được vị trí không)."""
    da_co = doc("""SELECT id, vi_do FROM toa_nha
                   WHERE coalesce(so_nha, '') = %s AND lower(ten_duong) = lower(%s) AND khu_vuc_id = %s""",
                (so_nha, ten_duong, khu["id"]))
    if da_co:
        toa = da_co[0]
        # Tòa đã có: chỉ bổ sung tiện ích mới tích (không xoá tiện ích cũ)
        ghi("""UPDATE toa_nha SET ten_toa = coalesce(ten_toa, %s), thang_may = thang_may OR %s,
                   ho_boi = ho_boi OR %s, gym = gym OR %s, cho_de_o_to = cho_de_o_to OR %s
               WHERE id = %s""",
            (ten_toa, *tien_ich, toa["id"]))
        return toa["id"], toa["vi_do"] is not None
    toa_do = tim_toa_do(f"{so_nha} {ten_duong}, {khu['ten']}".strip())
    moi = ghi("""INSERT INTO toa_nha (ten_toa, loai_hinh, so_nha, ten_duong, khu_vuc_id, vi_do, kinh_do,
                                      thang_may, ho_boi, gym, cho_de_o_to)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
              (ten_toa, loai_hinh, so_nha or None, ten_duong, khu["id"],
               toa_do[0] if toa_do else None, toa_do[1] if toa_do else None, *tien_ich))
    return moi["id"], toa_do is not None


def tim_hoac_tao_lien_he(ten, sdt, la_trung_gian) -> int | None:
    if not ten and not sdt:
        return None
    vai_tro = "trung gian" if la_trung_gian else "chủ nhà"
    da_co = doc("SELECT id FROM lien_he WHERE sdt = %s", (sdt,)) if sdt else \
        doc("SELECT id FROM lien_he WHERE lower(ten) = lower(%s) AND vai_tro = %s", (ten, vai_tro))
    if da_co:
        return da_co[0]["id"]
    return ghi("INSERT INTO lien_he (ten, sdt, vai_tro) VALUES (%s, %s, %s) RETURNING id",
               (ten or sdt, sdt or None, vai_tro))["id"]


with st.form("them_can_ho", clear_on_submit=True):
    anh = st.file_uploader("📷 Ảnh căn hộ (chọn nhiều ảnh một lúc được, ảnh đầu tiên làm ảnh bìa)",
                           type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)

    st.subheader("📍 Căn hộ ở đâu")
    c1, c2, c3 = st.columns([1, 2, 2])
    so_nha = c1.text_input("Số nhà", placeholder="12 hoặc K45/2")
    ten_duong = c2.text_input("Tên đường *", placeholder="Ví dụ: Mỹ Đa Đông 12")
    chon_khu = c3.selectbox("Khu vực *", khu_vuc, index=None, format_func=lambda k: k["ten"],
                            placeholder="Chọn khu vực")
    c1, c2, c3 = st.columns(3)
    ten_toa = c1.text_input("Tên tòa nhà (nếu có)")
    ma_can = c2.text_input("Số căn (khách không thấy)")
    loai_hinh = c3.selectbox("Loại", ["căn hộ dịch vụ", "chung cư", "nhà nguyên căn"])

    st.subheader("🏠 Thông tin căn")
    c1, c2, c3, c4 = st.columns(4)
    gia_trieu = c1.number_input("Giá thuê (triệu/tháng) *", 0.0, 500.0, 0.0, step=0.5)
    so_phong_ngu = c2.number_input("Phòng ngủ (0 = studio)", 0, 10, 1)
    dien_tich = c3.number_input("Diện tích (m²)", 0.0, 1000.0, 0.0, step=1.0)
    tang = c4.number_input("Tầng", 0, 100, 0)
    c1, c2, c3, c4 = st.columns(4)
    so_phong_tam = c1.number_input("Phòng tắm", 0, 10, 1)
    huong_view = c2.selectbox("View", ["không có view", "biển", "sông", "núi", "thành phố"])
    noi_that = c3.selectbox("Nội thất", ["đầy đủ", "cơ bản", "không có"])
    trang_thai = c4.selectbox("Trạng thái", ["còn trống", "sắp trống"])
    ngay_trong = st.date_input("Ngày trống (chỉ điền nếu 'sắp trống')", value=None, format="DD/MM/YYYY")

    st.write("Đặc điểm")
    c1, c2, c3, c4, c5 = st.columns(5)
    ban_cong = c1.checkbox("Ban công")
    vach_kinh = c2.checkbox("Phòng tắm vách kính")
    bon_tam = c3.checkbox("Bồn tắm")
    may_giat = c4.checkbox("Máy giặt riêng")
    thu_cung = c5.checkbox("Nuôi thú cưng")
    c1, c2, c3, c4, _ = st.columns(5)
    thang_may = c1.checkbox("Thang máy")
    ho_boi = c2.checkbox("Hồ bơi")
    gym = c3.checkbox("Gym")
    cho_de_o_to = c4.checkbox("Chỗ để ô tô")

    mo_ta = st.text_area("Mô tả cho khách đọc", placeholder="Ví dụ: gần biển Mỹ Khê 300m, yên tĩnh, có bếp riêng")
    ghi_chu = st.text_area("Ghi chú riêng (khách không thấy)", placeholder="Ví dụ: chủ dễ thương lượng giá")

    st.subheader("👤 Ai gửi căn này (không bắt buộc)")
    c1, c2, c3 = st.columns(3)
    ten_nguoi_gui = c1.text_input("Tên chủ / người gửi")
    sdt_nguoi_gui = c2.text_input("Số điện thoại")
    la_trung_gian = c3.checkbox("Qua trung gian (hoa hồng chia 50%)")

    luu = st.form_submit_button("💾 Lưu căn hộ", type="primary", width="stretch")

if luu:
    thieu = [ten for ten, gia_tri in [("tên đường", ten_duong.strip()), ("khu vực", chon_khu), ("giá thuê", gia_trieu)]
             if not gia_tri]
    if thieu:
        st.error("Chưa điền: " + ", ".join(thieu) + ". Bạn điền lại giúp mình nhé.")
    elif trang_thai == "sắp trống" and not ngay_trong:
        st.error("Căn 'sắp trống' cần có ngày trống.")
    else:
        with st.spinner("Đang lưu..."):
            toa_nha_id, co_vi_tri = tim_hoac_tao_toa_nha(
                so_nha.strip(), chuan_hoa_duong(ten_duong), chon_khu, ten_toa.strip() or None, loai_hinh,
                (thang_may, ho_boi, gym, cho_de_o_to))
            lien_he_id = tim_hoac_tao_lien_he(ten_nguoi_gui.strip(), sdt_nguoi_gui.strip(), la_trung_gian)
            moi = ghi(
                """INSERT INTO can_ho (toa_nha_id, lien_he_id, ma_can, so_phong_ngu, so_phong_tam, dien_tich,
                       tang, gia_thue, ban_cong, phong_tam_vach_kinh, bon_tam, may_giat_rieng,
                       cho_nuoi_thu_cung, huong_view, noi_that, mo_ta, ghi_chu_noi_bo, trang_thai, ngay_trong)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (toa_nha_id, lien_he_id, ma_can.strip() or None, so_phong_ngu, so_phong_tam, dien_tich or None,
                 tang or None, round(gia_trieu * 1_000_000), ban_cong, vach_kinh, bon_tam, may_giat, thu_cung,
                 huong_view, noi_that, mo_ta.strip() or None, ghi_chu.strip() or None, trang_thai,
                 ngay_trong if trang_thai == "sắp trống" else None),
            )
            for thu_tu, tep in enumerate(anh or []):
                ghi("INSERT INTO anh_can_ho (can_ho_id, du_lieu, thu_tu) VALUES (%s, %s, %s)",
                    (moi["id"], nen_anh(tep.getvalue()), thu_tu))
        st.success(f"✅ Đã lưu căn #{moi['id']} kèm {len(anh or [])} ảnh. Form đã được làm trống để nhập căn tiếp theo.")
        if not co_vi_tri:
            st.info("Chưa tìm được vị trí của địa chỉ này trên bản đồ. Căn vẫn được lưu bình thường; "
                    "khi rảnh bạn vào trang **Vị trí trên bản đồ** để ghim giúp.")
