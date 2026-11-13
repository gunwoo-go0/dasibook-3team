import streamlit as st

st.set_page_config(page_title="다시책방 위탁판매 관리", page_icon="📚")

# IA: 업무 흐름 순서(등록 → 검색 → 판매 처리 → 정산)로 사이드바 메뉴 4개, 첫 화면은 도서 검색(전체 목록)
# 화면 파일은 app_pages/에 둔다. 폴더 이름이 pages/이면 Streamlit이 옛 방식(파일 이름 메뉴)으로 먼저 열 수 있다.
pages = {
    "다시책방 위탁판매 관리": [
        st.Page("app_pages/register.py", title="위탁 도서 등록"),
        st.Page("app_pages/search.py", title="도서 검색", default=True),
        st.Page("app_pages/sale.py", title="판매 상태 변경"),
        st.Page("app_pages/settle.py", title="위탁자별 정산"),
    ]
}
page = st.navigation(pages)

# 다른 메뉴에서 도서 검색으로 돌아오면 검색 조건을 비워, 등록·판매 결과가 반영된 전체 목록부터 보여 준다.
if st.session_state.get("current_page") != page.title:
    st.session_state["current_page"] = page.title
    st.session_state.pop("search", None)

page.run()
