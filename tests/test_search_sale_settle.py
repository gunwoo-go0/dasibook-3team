"""SF-03~SF-05 검색, SF-06·SF-07 판매 처리, SF-08~SF-10 정산 (F-02 ~ F-04)."""
import pytest

from core.common import SOLD, BookError
from core.sale import MSG_ALREADY, MSG_NOT_FOUND, books_on_sale, mark_sold
from core.search import search_books
from core.settle import consignors, payout, settle


def ids(df):
    return list(df["book_id"])


# --- 도서 검색 -------------------------------------------------------------
def test_도서명_일부로_찾는다(books):
    assert ids(search_books(books, "파이썬")) == ["B001", "B004"]


def test_검색어_앞뒤_공백은_무시한다(books):
    assert ids(search_books(books, "  파이썬 ")) == ["B001", "B004"]


def test_검색어를_비우면_전체_목록(books):
    assert len(search_books(books, "  ")) == 8


def test_결과가_없으면_빈_표(books):
    assert search_books(books, "없는 책").empty


def test_검색_기준_위탁자_ID와_도서_ID(books):
    assert ids(search_books(books, "C002", "consignor_id")) == ["B004", "B006", "B008"]
    assert ids(search_books(books, "b003", "book_id")) == ["B003"]


# --- 판매 상태 변경 ---------------------------------------------------------
def test_판매중_도서만_고를_수_있다(books):
    assert ids(books_on_sale(books)) == ["B001", "B003", "B004", "B007"]


def test_판매완료_처리(books):
    new = mark_sold(books, "B003")
    assert new.loc[new["book_id"] == "B003", "status"].item() == SOLD
    assert books.loc[books["book_id"] == "B003", "status"].item() == "판매중"  # 원래 표는 그대로


@pytest.mark.parametrize("book_id, message", [("B002", MSG_ALREADY), ("B999", MSG_NOT_FOUND)])
def test_판매완료_도서와_없는_도서는_처리하지_않는다(books, book_id, message):
    with pytest.raises(BookError) as exc:
        mark_sold(books, book_id)
    assert str(exc.value) == message


# --- 위탁자별 정산 ----------------------------------------------------------
def test_정산액은_원_미만을_버린다():
    assert payout(9990, 15) == 8491  # 8,491.5원 → 8,491원
    assert payout(12000, 15) == 10200


def test_C001_정산(books):
    result = settle(books, "C001")
    assert [(i["book_id"], i["payout"]) for i in result.items] == [("B002", 10200), ("B005", 5600)]
    assert (result.count, result.total) == (2, 15800)


def test_C002_정산(books):
    result = settle(books, "C002")
    assert [(i["book_id"], i["payout"]) for i in result.items] == [("B006", 9900), ("B008", 8491)]
    assert result.total == 18391


def test_판매완료가_없으면_내역_없음(books):
    assert settle(books, "C003").count == 0


def test_위탁자_목록(books):
    assert consignors(books) == ["C001", "C002", "C003"]


def test_CSV_값이_잘못된_도서는_정산에서_빼고_알린다(books):
    broken = books.copy()
    broken.loc[broken["book_id"] == "B005", "fee_rate"] = "12.5"
    result = settle(broken, "C001")
    assert result.skipped == ["B005"] and result.total == 10200
