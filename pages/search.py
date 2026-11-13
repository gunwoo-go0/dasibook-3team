"""SCR-02 도서 검색 (F-02, SF-03 도서명 검색, SF-04 전체 목록, SF-05 검색 기준 선택)
+ AI 검색 도우미 (SF-12, 수업 추가사항).

앱을 켜면 이 화면이 먼저 열리고 전체 도서 목록을 보여 준다(IA: 도서 목록을 홈으로).
"""
import pandas as pd
import streamlit as st

from core.ai_search import MAX_BOOKS, describe, find_books
from core.search import MSG_NO_BOOKS, MSG_NO_RESULT, SEARCH_FIELDS, search_books
from llm import MAX_QUESTION, ChatError, get_reply
from ui import load_data, show_books

st.title("도서 검색")
df = load_data()

# ① 검색 기준 ② 검색어 ③ 검색 버튼
with st.form("search_form", border=False):
    c1, c2, c3 = st.columns([2, 5, 1.3], vertical_alignment="bottom")
    field = c1.selectbox("검색 기준", list(SEARCH_FIELDS), label_visibility="collapsed")
    keyword = c2.text_input("검색어", placeholder="검색어 입력", label_visibility="collapsed")
    if c3.form_submit_button("검색", type="primary", width="stretch"):
        st.session_state["search"] = (field, keyword.strip())

# ④ 결과 건수 ⑤ 결과 표 ⑥ 판매 상태 글자색 ⑦ 안내 메시지
query = st.session_state.get("search")
if df.empty:
    st.info(MSG_NO_BOOKS)
else:
    if query is None:  # 처음 열었을 때는 전체 목록(SF-04)
        result, label = df, f"전체 도서 {len(df)}권"
    else:
        result = search_books(df, query[1], SEARCH_FIELDS[query[0]])
        label = f"검색 결과 {len(result)}건"
    if result.empty:
        st.info(MSG_NO_RESULT)
    else:
        st.markdown(f"**{label}**")
        show_books(result)


# ---------------------------------------------------------------------------
# AI 검색 도우미 (SF-12, 추가): 질문으로 기존 검색을 실행하고, 찾은 도서만 근거로 답한다.
# ---------------------------------------------------------------------------
CHAT_HEIGHT = 270  # 대화 영역 높이(px)


def show_found(books: list[dict], total: int) -> None:
    """앱이 찾은 도서를 표로 보여 준다(모델이 만든 값이 아니다)."""
    if not books:
        st.caption("찾은 도서 없음")
        return
    more = f" (앞의 {MAX_BOOKS}권만 표시)" if total > MAX_BOOKS else ""
    st.markdown(f"**찾은 도서 {total}권**{more}")
    show_books(pd.DataFrame(books))


if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = []

with st.container(border=True):
    head, reset = st.columns([5, 1.4], vertical_alignment="center")
    head.subheader("AI 검색 도우미")
    if reset.button("대화 초기화", width="stretch"):
        st.session_state.ai_messages = []
    st.caption("검색으로 찾은 도서와 업무 규칙만 근거로 답합니다 · 수업용 가상 데이터")
    # 대화 영역 높이를 고정해 그 안에서 스크롤한다. 대화가 길어져도 입력칸이 화면 아래로 밀려나지 않는다.
    chat = st.container(height=CHAT_HEIGHT)
    if not st.session_state.ai_messages and not st.session_state.get("ai_question"):
        chat.caption("질문을 입력하면 여기에 답변과 찾은 도서가 나옵니다.")
    for message in st.session_state.ai_messages:
        with chat.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                show_found(message["books"], message["total"])
    notice = st.container()  # 오류 안내는 입력칸 바로 위에 띄운다
    question = st.chat_input("질문을 입력하세요 (예: 파이썬 입문 팔렸어? / C001 책 보여 줘)", max_chars=MAX_QUESTION,
                             key="ai_question")

if question:
    with chat.chat_message("user"):
        st.markdown(question)
    found, terms = find_books(df, question)  # 기존 검색(SF-03, SF-05) 실행
    try:
        with chat, st.spinner("답변을 생성하고 있습니다."):
            answer = get_reply(st.session_state.ai_messages, question, describe(found, terms))
    except ChatError as exc:
        notice.error(str(exc))
        notice.info("이번 질문과 실패한 응답은 대화 기록에 저장되지 않았습니다.")
    else:
        books = found.head(MAX_BOOKS).to_dict("records")
        with chat.chat_message("assistant"):
            st.markdown(answer)
            show_found(books, len(found))
        st.session_state.ai_messages.extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer, "books": books, "total": len(found)},
        ])
