"""SF-01 도서 정보 입력과 검사, SF-02 도서 등록 저장 (F-01 위탁 도서 등록)."""
import re

import pandas as pd

from core.common import COLUMNS, ON_SALE, BookError, to_int

BOOK_ID = re.compile(r"B\d{3}")       # 개발팀 제안: B와 숫자 3자리 (예: B001)
CONSIGNOR_ID = re.compile(r"C\d{3}")  # 개발팀 제안: C와 숫자 3자리 (예: C001)
FEE_MIN, FEE_MAX = 1, 99              # 질의응답 확정: 1부터 99까지의 정수(%)

# 화면설계서 SCR-01 메시지
MSG_DONE = "등록이 완료되었습니다."
MSG_REQUIRED = "필수 항목을 모두 입력해 주세요."
MSG_PRICE = "판매 가격은 0보다 커야 합니다."
MSG_FEE = "수수료율은 1~99 사이 정수여야 합니다."
MSG_DUPLICATE = "이미 등록된 도서 ID입니다."
# 화면설계서 메시지 목록에는 없어 개발팀이 더한 문구 (SF-01의 ID 형식 검사, Issue #5의 판매 가격 정수 검사)
MSG_PRICE_INT = "판매 가격은 원 단위 정수로 입력해 주세요."
MSG_BOOK_ID = "도서 ID는 B와 숫자 3자리로 입력해 주세요. (예: B013)"
MSG_CONSIGNOR_ID = "위탁자 ID는 C와 숫자 3자리로 입력해 주세요. (예: C001)"


def check_book(book_id, title, consignor_id, price, fee_rate) -> dict:
    """SF-01: 필수값 → 가격 → 수수료율 → ID 형식 순서로 검사한다.
    처음 걸린 이유 하나를 BookError로 알리고, 통과하면 정리한 값을 돌려준다."""
    book_id = str(book_id or "").strip().upper()
    title = str(title or "").strip()
    consignor_id = str(consignor_id or "").strip().upper()
    if not book_id or not title or not consignor_id or price in (None, "") or fee_rate in (None, ""):
        raise BookError(MSG_REQUIRED)

    price_num = to_int(price)
    if price_num is None:  # 8000.5처럼 원 단위 정수가 아니면 잘라서 저장하지 않고 알린다
        raise BookError(MSG_PRICE if _is_not_positive(price) else MSG_PRICE_INT)
    if price_num <= 0:
        raise BookError(MSG_PRICE)

    fee_num = to_int(fee_rate)
    if fee_num is None or not FEE_MIN <= fee_num <= FEE_MAX:
        raise BookError(MSG_FEE)

    if not BOOK_ID.fullmatch(book_id):
        raise BookError(MSG_BOOK_ID)
    if not CONSIGNOR_ID.fullmatch(consignor_id):
        raise BookError(MSG_CONSIGNOR_ID)

    return {"book_id": book_id, "title": title, "consignor_id": consignor_id,
            "price": price_num, "fee_rate": fee_num}


def _is_not_positive(value) -> bool:
    try:
        return float(str(value).replace(",", "")) <= 0
    except ValueError:
        return False


def add_book(df: pd.DataFrame, book: dict) -> pd.DataFrame:
    """SF-02: 도서 ID가 겹치지 않으면 판매중으로 추가한 새 표를 돌려준다(저장은 화면에서 한다)."""
    if (df["book_id"].str.upper() == book["book_id"]).any():
        raise BookError(MSG_DUPLICATE)
    row = {k: str(book[k]) for k in ("book_id", "title", "consignor_id", "price", "fee_rate")}
    row["status"] = ON_SALE  # 신규 도서는 항상 판매중
    new = pd.DataFrame([row], columns=COLUMNS).astype("object")
    return pd.concat([df, new], ignore_index=True)


def done_message(book: dict) -> str:
    return f"{MSG_DONE} ({book['book_id']})"
