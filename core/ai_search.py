"""SF-12 AI 검색 도우미의 검색 부분 (수업 추가사항: 기존 기능과 연동).

질문에서 도서 ID(B001), 위탁자 ID(C001), 도서명을 찾아 기존 검색 함수 search_books()
(SF-03 도서명, SF-05 도서 ID·위탁자 ID)를 그대로 실행한다. 모델은 여기서 찾은 도서만 근거로 답한다.
데이터는 읽기만 하고 바꾸지 않는다.
"""
import re

import pandas as pd

from core.common import to_int, won
from core.search import search_books

BOOK_ID_IN_TEXT = re.compile(r"(?<![A-Za-z0-9])[Bb]\d{3}(?!\d)")
CONSIGNOR_ID_IN_TEXT = re.compile(r"(?<![A-Za-z0-9])[Cc]\d{3}(?!\d)")
MAX_BOOKS = 10  # 모델에 넘기고 화면에 보여 줄 최대 권수
MIN_WORD = 2    # 도서명 단어로 찾을 때 최소 글자 수
FIELD_NAMES = {"book_id": "도서 ID", "consignor_id": "위탁자 ID", "title": "도서명"}


def find_terms(df: pd.DataFrame, question: str) -> list[tuple[str, str]]:
    """질문에서 (검색 기준, 검색어) 목록을 찾는다.
    도서명은 등록된 전체 제목을 먼저 찾고, 남은 부분에서 제목에 쓰인 단어를 찾는다."""
    terms = [("book_id", m.upper()) for m in BOOK_ID_IN_TEXT.findall(question)]
    terms += [("consignor_id", m.upper()) for m in CONSIGNOR_ID_IN_TEXT.findall(question)]

    rest = CONSIGNOR_ID_IN_TEXT.sub(" ", BOOK_ID_IN_TEXT.sub(" ", question)).casefold()
    titles = {t.strip() for t in df["title"] if len(t.strip()) >= MIN_WORD}
    words = {w for t in titles for w in t.split() if len(w) >= MIN_WORD}
    for kind in (titles, words):  # 긴 것부터 찾고, 찾은 부분은 지워 같은 글자를 두 번 쓰지 않는다
        for text in sorted(kind, key=len, reverse=True):
            if text.casefold() in rest:
                terms.append(("title", text))
                rest = rest.replace(text.casefold(), " ")
    return list(dict.fromkeys(terms))


def find_books(df: pd.DataFrame, question: str) -> tuple[pd.DataFrame, list[tuple[str, str]]]:
    """찾은 검색 조건마다 기존 검색 기능을 실행하고 결과를 합친다(같은 도서는 한 번만)."""
    terms = find_terms(df, question)
    parts = []
    for field, keyword in terms:
        found = search_books(df, keyword, field)  # 기존 검색 기능(SF-03, SF-05) 그대로
        if field != "title":
            found = found[found[field].str.upper() == keyword]  # ID는 정확히 같은 것만
        parts.append(found)
    if not parts:
        return df.iloc[0:0].copy(), terms
    return pd.concat(parts).drop_duplicates(subset="book_id"), terms


def describe(found: pd.DataFrame, terms: list[tuple[str, str]]) -> str:
    """모델에 넘길 검색 결과 글. 앱이 찾은 값만 적는다."""
    if not terms:
        return ("검색 조건: 없음 (질문에서 도서 ID, 위탁자 ID, 도서명을 찾지 못해 검색하지 않았습니다)\n"
                "찾은 도서: 없음")
    cond = ", ".join(f"{FIELD_NAMES[f]} '{k}'" for f, k in terms)
    lines = [f"검색 조건: {cond}"]
    if found.empty:
        lines.append("찾은 도서: 없음 (검색 결과가 없습니다)")
        return "\n".join(lines)
    head = f"찾은 도서 {len(found)}권"
    if len(found) > MAX_BOOKS:
        head += f" (앞의 {MAX_BOOKS}권만 적음)"
    lines.append(head + ":")
    for _, r in found.head(MAX_BOOKS).iterrows():
        price = to_int(r["price"])
        lines.append(f"- 도서 ID {r['book_id']} | 도서명 {r['title']} | 위탁자 ID {r['consignor_id']} | "
                     f"판매 가격 {won(price) if price is not None else r['price']} | 판매 상태 {r['status']}")
    return "\n".join(lines)
