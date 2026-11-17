"""공통 상수와 오류: 모든 기능이 같이 쓰는 값."""
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "books.csv"

# books.csv 열 이름(코드용)과 화면에 보여 줄 이름
COLUMNS = ["book_id", "title", "consignor_id", "price", "status", "fee_rate"]
LABELS = {
    "book_id": "도서 ID",
    "title": "도서명",
    "consignor_id": "위탁자 ID",
    "price": "판매 가격",
    "status": "판매 상태",
    "fee_rate": "수수료율",
}

ON_SALE = "판매중"
SOLD = "판매완료"


class BookError(Exception):
    """화면에 그대로 보여 줄 안내 문구. 앱은 멈추지 않고 이 문구만 표시한다."""


def to_int(value) -> int | None:
    """입력값이나 CSV 글자를 정수로 바꾼다. 12.5처럼 정수가 아니면 None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    text = str(value).replace(",", "").strip()
    sign = text[0] if text and text[0] in "+-" else ""
    digits = text[len(sign):]
    if digits.isascii() and digits.isdigit():
        return int(sign + digits)
    return None


def won(amount: int | Decimal) -> str:
    """금액을 '12,345원'처럼 쓴다. 정산액처럼 원 미만이 있으면 소수점 아래도 보여 준다(Issue #14: '10,493.25원')."""
    value = Decimal(amount)
    if value == value.to_integral_value():
        return f"{int(value):,}원"
    return f"{value:,.2f}".rstrip("0") + "원"
