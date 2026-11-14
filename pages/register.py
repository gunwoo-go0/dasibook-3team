"""SCR-01 위탁 도서 등록 (F-01, SF-01 입력과 검사, SF-02 등록 저장)."""
import streamlit as st

from core.common import ON_SALE, BookError
from core.register import add_book, check_book, done_message
from core.storage import save_books
from ui import flash, load_data, show_flash

TEXT_KEYS = ["reg_book_id", "reg_title", "reg_consignor"]
NUMBER_KEYS = ["reg_price", "reg_fee"]

# 등록에 성공한 다음 화면에서만 입력칸을 비운다. 실패하면 입력값을 그대로 둔다.
if st.session_state.pop("reg_clear", False):
    for key in TEXT_KEYS:
        st.session_state[key] = ""
    for key in NUMBER_KEYS:
        st.session_state[key] = None

st.title("위탁 도서 등록")

with st.form("register_form", border=False):
    book_id = st.text_input("도서 ID \\*", placeholder="예: B013", key="reg_book_id")
    title = st.text_input("도서명 \\*", placeholder="도서 제목", key="reg_title")
    consignor_id = st.text_input("위탁자 ID \\*", placeholder="예: C001", key="reg_consignor")
    price = st.number_input("판매 가격 \\* (원)", value=None, step=100, placeholder="0보다 큰 정수",
                            key="reg_price")
    # 12.5 같은 소수를 그대로 받아 검사에서 막도록 실수 칸으로 둔다(정수 칸은 12로 잘라 버린다).
    fee_rate = st.number_input("수수료율 \\* (%)", value=None, step=1.0, format="%g", placeholder="1~99 정수",
                               key="reg_fee")
    st.text_input("판매 상태", value=ON_SALE, disabled=True)
    submitted = st.form_submit_button("등록", type="primary")

if submitted:
    try:
        book = check_book(book_id, title, consignor_id, price, fee_rate)  # 필수값 → 가격 → 수수료율 → ID 형식
        df = load_data()  # 저장 직전에 다시 읽어 중복을 확인한다
        save_books(add_book(df, book))  # ID 중복 → 저장
    except BookError as exc:
        st.error(str(exc))
    else:
        flash("register", done_message(book))
        st.session_state["reg_clear"] = True
        st.rerun()

show_flash("register")
