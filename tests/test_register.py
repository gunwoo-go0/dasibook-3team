"""SF-01 입력 검사, SF-02 등록 (F-01-1 ~ F-01-3)."""
import pytest

from core.common import ON_SALE, BookError
from core.register import (MSG_BOOK_ID, MSG_CONSIGNOR_ID, MSG_DUPLICATE, MSG_FEE, MSG_PRICE, MSG_PRICE_INT, MSG_REQUIRED,
                           add_book, check_book, done_message)

GOOD = dict(book_id="B013", title="자료구조 연습", consignor_id="C004", price=10000, fee_rate=10.0)


def check(**changes):
    return check_book(**{**GOOD, **changes})


def test_정상_입력은_정리된_값을_돌려준다():
    assert check(book_id=" b013 ", consignor_id="c004") == {
        "book_id": "B013", "title": "자료구조 연습", "consignor_id": "C004", "price": 10000, "fee_rate": 10}


@pytest.mark.parametrize("changes", [dict(book_id=""), dict(title="  "), dict(consignor_id=""),
                                     dict(price=None), dict(fee_rate=None)])
def test_빈_항목이_있으면_필수_안내(changes):
    with pytest.raises(BookError, match=MSG_REQUIRED):
        check(**changes)


@pytest.mark.parametrize("price", [0, -1000])
def test_판매_가격은_0보다_커야_한다(price):
    with pytest.raises(BookError, match=MSG_PRICE):
        check(price=price)


@pytest.mark.parametrize("price, message", [(8000.5, MSG_PRICE_INT), ("12,000.7", MSG_PRICE_INT),
                                            (-5.5, MSG_PRICE), (10000.0, None)])
def test_판매_가격은_원_단위_정수(price, message):  # Issue #5
    if message is None:
        assert check(price=price)["price"] == 10000
    else:
        with pytest.raises(BookError) as exc:
            check(price=price)
        assert str(exc.value) == message


@pytest.mark.parametrize("fee", [0, 100, 12.5, -5])
def test_수수료율은_1부터_99까지_정수(fee):
    with pytest.raises(BookError) as exc:
        check(fee_rate=fee)
    assert str(exc.value) == MSG_FEE


@pytest.mark.parametrize("fee", [1, 99, 15.0])
def test_수수료율_경계값은_통과(fee):
    assert check(fee_rate=fee)["fee_rate"] == int(fee)


@pytest.mark.parametrize("book_id", ["B13", "B0013", "X001", "B01A"])
def test_도서_ID_형식(book_id):
    with pytest.raises(BookError) as exc:
        check(book_id=book_id)
    assert str(exc.value) == MSG_BOOK_ID


def test_위탁자_ID_형식():
    with pytest.raises(BookError) as exc:
        check(consignor_id="C04")
    assert str(exc.value) == MSG_CONSIGNOR_ID


def test_검사_순서는_필수값_가격_수수료율_ID형식():
    with pytest.raises(BookError) as exc:
        check(title="", price=0, fee_rate=100, book_id="X")
    assert str(exc.value) == MSG_REQUIRED
    with pytest.raises(BookError) as exc:
        check(price=0, fee_rate=100, book_id="X")
    assert str(exc.value) == MSG_PRICE
    with pytest.raises(BookError) as exc:
        check(fee_rate=100, book_id="X")
    assert str(exc.value) == MSG_FEE


def test_등록하면_판매중으로_추가된다(books):
    new = add_book(books, check())
    assert len(new) == len(books) + 1
    assert new.iloc[-1].to_dict() == {"book_id": "B013", "title": "자료구조 연습", "consignor_id": "C004",
                                      "price": "10000", "status": ON_SALE, "fee_rate": "10"}
    assert done_message(check()) == "등록이 완료되었습니다. (B013)"


def test_이미_있는_도서_ID는_등록하지_않는다(books):
    with pytest.raises(BookError, match=MSG_DUPLICATE):
        add_book(books, check(book_id="b001"))
