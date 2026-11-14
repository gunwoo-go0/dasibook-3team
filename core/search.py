"""SF-03 도서명 검색, SF-04 전체 도서 목록, SF-05 검색 기준 선택 (F-02 도서 검색).

AI 검색 도우미(SF-12, core/ai_search.py)도 이 함수를 그대로 불러 쓴다.
"""
import pandas as pd

# SF-05 검색 기준 (기본값은 도서명). 발주팀이 도서명만 원하면 나머지 두 줄을 지운다.
SEARCH_FIELDS = {"도서명": "title", "도서 ID": "book_id", "위탁자 ID": "consignor_id"}

MSG_NO_RESULT = "검색 결과가 없습니다."
MSG_NO_BOOKS = "등록된 도서가 없습니다."


def search_books(df: pd.DataFrame, keyword: str, field: str = "title") -> pd.DataFrame:
    """검색어가 들어 있는 도서를 모두 찾는다. 앞뒤 공백은 무시하고 영문 대소문자는 구분하지 않는다.
    검색어가 비면 전체 목록을 돌려준다(SF-04)."""
    keyword = (keyword or "").strip()
    if not keyword:
        return df.copy()
    hit = df[field].str.casefold().str.contains(keyword.casefold(), regex=False)
    return df[hit].copy()
