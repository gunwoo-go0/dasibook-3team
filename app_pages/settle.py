"""SCR-04 위탁자별 정산 (F-04, SF-08 정산 대상 조회, SF-09 정산액 계산, SF-10 정산 결과 표시)."""
import pandas as pd
import streamlit as st

from core.common import won
from core.search import MSG_NO_BOOKS
from core.settle import MSG_NO_SALES, consignors, settle
from ui import load_data

st.title("위탁자별 정산액 계산")
df = load_data()
ids = consignors(df)
if not ids:
    st.info(MSG_NO_BOOKS)
    st.stop()

# ① 위탁자 ID ② 정산 조회 버튼
with st.form("settle_form", border=False):
    c1, c2 = st.columns([3, 1.3], vertical_alignment="bottom")
    consignor_id = c1.selectbox("위탁자 ID", ids)
    submitted = c2.form_submit_button("정산 조회", type="primary", width="stretch")

if submitted:
    result = settle(df, consignor_id)
    if result.skipped:
        st.warning(f"값이 잘못돼 계산에서 뺀 도서가 있습니다: {', '.join(result.skipped)}. books.csv를 확인하세요.")
    if result.count == 0:
        st.info(MSG_NO_SALES)  # ⑥ 안내 메시지
    else:
        # ③ 정산 내역 표 ④ 판매완료 권수 ⑤ 총정산액
        table = pd.DataFrame([{
            "도서 ID": i["book_id"], "도서명": i["title"], "판매 가격": won(i["price"]),
            "수수료율": f"{i['fee_rate']}%", "정산액": won(i["payout"]),
        } for i in result.items])
        st.dataframe(table, hide_index=True)
        with st.container(border=True):
            left, right = st.columns(2, vertical_alignment="center")
            left.markdown(f"**판매완료 {result.count}권**")
            right.metric("총정산액", won(result.total))
