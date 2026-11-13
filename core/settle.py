"""SF-08 정산 대상 조회, SF-09 정산액 계산, SF-10 정산 결과 값 (F-04 위탁자별 정산액 계산)."""
from dataclasses import dataclass, field

import pandas as pd

from core.common import SOLD, to_int

MSG_NO_SALES = "판매완료 내역이 없습니다."  # 화면설계서 SCR-04 메시지


@dataclass
class Settlement:
    consignor_id: str
    items: list[dict] = field(default_factory=list)   # 권별: book_id, title, price, fee_rate, payout
    skipped: list[str] = field(default_factory=list)  # CSV 값이 잘못돼 계산에서 뺀 도서 ID

    @property
    def total(self) -> int:
        return sum(i["payout"] for i in self.items)

    @property
    def count(self) -> int:
        return len(self.items)


def consignors(df: pd.DataFrame) -> list[str]:
    """등록된 위탁자 ID 목록. 직접 입력할 때 생기는 오타를 막으려고 목록에서 고르게 한다."""
    return sorted(x for x in df["consignor_id"].unique() if x)


def payout(price: int, fee_rate: int) -> int:
    """SF-09: 판매 가격 × (100 − 수수료율) ÷ 100. 정수 연산이라 소수 오차가 없고 원 미만은 버려진다."""
    return price * (100 - fee_rate) // 100


def settle(df: pd.DataFrame, consignor_id: str) -> Settlement:
    """SF-08: 고른 위탁자의 판매완료 도서만 모은다. 판매 가격과 수수료율은 등록된 권별 값을 쓴다."""
    result = Settlement(consignor_id)
    rows = df[(df["consignor_id"] == consignor_id) & (df["status"] == SOLD)]
    for _, r in rows.iterrows():
        price, fee = to_int(r["price"]), to_int(r["fee_rate"])
        if price is None or price <= 0 or fee is None or not 1 <= fee <= 99:
            result.skipped.append(r["book_id"])
            continue
        result.items.append({"book_id": r["book_id"], "title": r["title"], "price": price,
                             "fee_rate": fee, "payout": payout(price, fee)})
    return result
