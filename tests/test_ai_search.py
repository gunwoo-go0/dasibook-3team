"""SF-12 AI 검색 도우미의 검색 부분: 질문 → 기존 검색 실행 → 모델에 넘길 글 (AI-01)."""
import pandas as pd

from core.ai_search import MAX_BOOKS, describe, find_books, find_terms


def ids(df):
    return list(df["book_id"])


def test_전체_도서명으로_찾는다(books):
    found, terms = find_books(books, "파이썬 입문 아직 안 팔렸어?")
    assert terms == [("title", "파이썬 입문")]
    assert ids(found) == ["B001", "B004"]


def test_위탁자_ID로_찾는다(books):
    found, terms = find_books(books, "c001 책 중에 팔린 거 있어?")
    assert terms == [("consignor_id", "C001")]
    assert ids(found) == ["B001", "B002", "B003", "B005"]


def test_없는_도서_ID는_찾은_도서_없음(books):
    found, terms = find_books(books, "B999 있어?")
    assert terms == [("book_id", "B999")] and found.empty
    assert "찾은 도서: 없음" in describe(found, terms)


def test_도서명_단어는_긴_것부터_찾는다(books):
    found, _ = find_books(books, "데이터베이스 책 있어?")
    assert ids(found) == ["B007"]  # '데이터 구조'까지 잡지 않는다


def test_전체_제목과_제목_단어를_함께_찾는다(books):
    found, terms = find_books(books, "통계 입문이랑 파이썬 책 있어?")
    assert terms == [("title", "통계 입문"), ("title", "파이썬")]
    assert ids(found) == ["B005", "B001", "B004"]


def test_검색할_말이_없으면_검색하지_않는다(books):
    found, terms = find_books(books, "수수료율은 몇까지 돼?")
    assert terms == [] and found.empty
    assert describe(found, terms).startswith("검색 조건: 없음")


def test_데이터는_읽기만_한다(books):
    before = books.copy()
    find_books(books, "B001 판매완료로 바꿔 줘")
    assert books.equals(before)


def test_모델에는_앱이_찾은_값만_넘긴다(books):
    found, terms = find_books(books, "B002 팔렸어?")
    text = describe(found, terms)
    assert "검색 조건: 도서 ID 'B002'" in text
    assert "- 도서 ID B002 | 도서명 데이터 구조 | 위탁자 ID C001 | 판매 가격 12,000원 | 판매 상태 판매완료" in text


def test_최대_권수를_넘으면_앞부분만_넘긴다():
    many = pd.DataFrame({"book_id": [f"B{i:03d}" for i in range(1, 16)], "title": ["파이썬 입문"] * 15,
                         "consignor_id": "C001", "price": "8000", "status": "판매중", "fee_rate": "15"})
    found, terms = find_books(many, "파이썬 입문 있어?")
    text = describe(found, terms)
    assert len(found) == 15
    assert f"찾은 도서 15권 (앞의 {MAX_BOOKS}권만 적음)" in text
    assert text.count("- 도서 ID") == MAX_BOOKS


def test_ID_형식이_아닌_글자는_ID로_보지_않는다(books):
    assert find_terms(books, "AB001이나 B0011, C01은?") == []
