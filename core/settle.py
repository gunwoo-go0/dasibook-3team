"""SF-08 정산 대상 조회, SF-09 정산액 계산, SF-10 정산 결과 값 (F-04 위탁자별 정산액 계산)."""
from dataclasses import dataclass, field
from decimal import Decimal

import pandas as pd

from core.common import SOLD, to_int, won

MSG_NO_SALES = "판매완료 내역이 없습니다."  # 화면설계서 SCR-04 메시지
MSG_ROUNDING = "정산액 = 판매 가격 × (100 − 수수료율) ÷ 100, 원 미만도 버리지 않고 소수점까지 표시합니다."  # Issue #14
TABLE_COLUMNS = ["도서 ID", "도서명", "판매 가격", "수수료율", "정산액"]


@dataclass
class Settlement:
    consignor_id: str
    items: list[dict] = field(default_factory=list)   # 권별: book_id, title, price, fee_rate, payout
    skipped: list[str] = field(default_factory=list)  # CSV 값이 잘못돼 계산에서 뺀 도서 ID

    @property
    def total(self) -> Decimal:
        return sum((i["payout"] for i in self.items), Decimal(0))

    @property
    def count(self) -> int:
        return len(self.items)


def consignors(df: pd.DataFrame) -> list[str]:
    """등록된 위탁자 ID 목록. 직접 입력할 때 생기는 오타를 막으려고 목록에서 고르게 한다."""
    return sorted(x for x in df["consignor_id"].unique() if x)


def payout(price: int, fee_rate: int) -> Decimal:
    """SF-09: 판매 가격 × (100 − 수수료율) ÷ 100. 원 미만도 버리지 않는다(Issue #14, 12,345원·15% → 10,493.25원).
    판매 가격과 수수료율이 정수라 결과는 소수 둘째 자리에서 끝나고, Decimal로 계산해 오차 없이 그대로 더한다."""
    return Decimal(price * (100 - fee_rate)) / 100


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


def settlement_table(result: Settlement) -> pd.DataFrame:
    """SF-10 정산 내역 표. 화면과 CSV가 같은 값을 쓰도록 한 곳에서 만든다."""
    return pd.DataFrame([[i["book_id"], i["title"], won(i["price"]), f"{i['fee_rate']}%", won(i["payout"])]
                         for i in result.items], columns=TABLE_COLUMNS)


def settlement_csv(result: Settlement) -> bytes:
    """조회한 위탁자 한 명의 정산 내역 CSV (Issue #13). 화면 표 아래에 총정산액 줄을 붙인다.
    엑셀로 열어도 한글이 깨지지 않게 books.csv와 같은 utf-8-sig로 만든다."""
    total = pd.DataFrame([["총정산액", f"판매완료 {result.count}권", "", "", won(result.total)]], columns=TABLE_COLUMNS)
    table = pd.concat([settlement_table(result), total], ignore_index=True)
    return table.to_csv(index=False, lineterminator="\n").encode("utf-8-sig")
