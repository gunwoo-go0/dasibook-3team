"""SCR-03 판매 상태 변경 (F-03, SF-06 판매 대상 선택, SF-07 판매완료 처리)."""
import streamlit as st

from core.common import BookError
from core.sale import MSG_CONFIRM, MSG_NONE_ON_SALE, books_on_sale, check_on_sale, done_message, mark_sold
from core.storage import save_books
from ui import flash, load_data, show_books, show_flash

st.title("판매 상태 변경")
df = load_data()
on_sale = books_on_sale(df)
pending = st.session_state.get("sale_pending")  # 확인을 기다리는 도서 ID

# 다른 창에서 먼저 처리해 고른 도서가 목록에서 빠졌으면, 이유를 메시지 자리에 남기고 선택을 비운다.
picked = st.session_state.get("sale_pick")
if picked and picked not in set(on_sale["book_id"]):
    try:
        check_on_sale(df, picked)
    except BookError as exc:
        flash("sale", f"{exc} ({picked})", kind="error")
    del st.session_state["sale_pick"]
    st.session_state.pop("sale_pending", None)
    pending = None

if on_sale.empty:
    show_flash("sale")
    st.info(MSG_NONE_ON_SALE)
    st.stop()

# ① 판매 대상 선택 ② 선택 도서 정보
titles = dict(zip(on_sale["book_id"], on_sale["title"]))
book_id = st.selectbox("판매 대상 도서 (판매중만 표시)", list(titles), format_func=lambda b: f"{b} · {titles[b]}",
                       key="sale_pick", disabled=pending is not None)
show_books(on_sale[on_sale["book_id"] == book_id])

# ③ 판매완료 처리 ④ 확인 단계
if st.button("판매완료 처리", type="primary", disabled=pending is not None):
    st.session_state["sale_pending"] = book_id
    st.rerun()

if pending is not None:
    with st.container(border=True):
        st.markdown(f"**{MSG_CONFIRM}**")
        c1, c2, _ = st.columns([1, 1, 4])
        ok = c1.button("확인", type="primary", width="stretch")
        cancel = c2.button("취소", width="stretch")
    if ok:
        st.session_state.pop("sale_pending")
        fresh = load_data()  # 저장 직전에 다시 읽어 판매중인지 확인한다
        try:
            save_books(mark_sold(fresh, pending))
        except BookError as exc:
            flash("sale", f"{exc} ({pending})", kind="error")
        else:
            title = fresh.loc[fresh["book_id"] == pending, "title"].iloc[0]
            flash("sale", done_message(pending, title))
            st.session_state.pop("sale_pick", None)
        st.rerun()
    if cancel:
        st.session_state.pop("sale_pending")
        st.rerun()

show_flash("sale")  # ⑤ 성공 메시지 ⑥ 오류 메시지: 화면설계서처럼 버튼 아래 메시지 자리에 보여 준다
