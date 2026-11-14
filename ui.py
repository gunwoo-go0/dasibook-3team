"""여러 화면이 같이 쓰는 Streamlit 도우미: 데이터 불러오기, 도서 표, 완료 메시지."""
import pandas as pd
import streamlit as st

from core.common import LABELS, ON_SALE, SOLD, BookError, to_int, won
from core.storage import load_books

BOOK_COLUMNS = ("book_id", "title", "consignor_id", "price", "status")  # 질의응답에서 확정한 표시 항목 5개
STATUS_TEXT = {ON_SALE: "● 판매중", SOLD: "● 판매완료"}
STATUS_STYLE = {ON_SALE: "color: #1a7f37; font-weight: 600", SOLD: "color: #8c959f"}


def load_data() -> pd.DataFrame:
    """books.csv를 읽는다. 읽을 수 없으면 이유만 보여 주고 이 화면을 멈춘다(앱은 종료되지 않는다)."""
    try:
        return load_books()
    except BookError as exc:
        st.error(str(exc))
        st.stop()


def book_view(df: pd.DataFrame, columns=BOOK_COLUMNS):
    """도서 표: 판매 가격은 천 단위 쉼표와 '원', 판매 상태는 글자색으로 구분한다."""
    view = df[list(columns)].copy()
    if "price" in view:
        view["price"] = [won(n) if (n := to_int(x)) is not None else x for x in view["price"]]
    if "fee_rate" in view:
        view["fee_rate"] = [f"{x}%" for x in view["fee_rate"]]
    if "status" in view:
        view["status"] = [STATUS_TEXT.get(s, s) for s in view["status"]]
    view = view.rename(columns=LABELS)
    styled = view.style
    if LABELS["status"] in view:
        colors = {STATUS_TEXT[k]: v for k, v in STATUS_STYLE.items()}
        styled = styled.map(lambda s: colors.get(s, "color: #cf222e"), subset=[LABELS["status"]])
    return styled


def show_books(df: pd.DataFrame, columns=BOOK_COLUMNS) -> None:
    st.dataframe(book_view(df, columns), hide_index=True)


def flash(key: str, text: str, kind: str = "success") -> None:
    """다음에 show_flash를 부를 때 한 번 보여 줄 메시지를 남긴다. kind는 success 또는 error."""
    st.session_state[f"flash_{key}"] = (kind, text)


def show_flash(key: str) -> None:
    item = st.session_state.pop(f"flash_{key}", None)
    if item:
        kind, text = item
        (st.error if kind == "error" else st.success)(text)
