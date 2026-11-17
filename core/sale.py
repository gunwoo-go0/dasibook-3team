"""SF-06 판매 대상 선택, SF-07 판매완료 처리 (F-03 판매 상태 변경)."""
import pandas as pd

from core.common import ON_SALE, SOLD, BookError

# 화면설계서 SCR-03 메시지
MSG_DONE = "판매완료 처리되었습니다."
MSG_ALREADY = "이미 판매완료된 도서입니다."
MSG_NOT_FOUND = "존재하지 않는 도서입니다."
MSG_NONE_ON_SALE = "판매중인 도서가 없습니다."
MSG_CONFIRM = "판매완료로 변경할까요?"
# Issue #10: 등록 화면은 같은 도서 ID를 막지만, books.csv를 손으로 고치면 같은 ID가 두 줄 이상 생길 수 있다.
MSG_DUPLICATE = "같은 도서 ID가 books.csv에 {count}줄 있어 판매 처리를 하지 않았습니다. 중복된 줄을 정리한 뒤 다시 처리하세요."
MSG_DUPLICATE_LIST = "books.csv에 같은 도서 ID가 여러 줄 있습니다: {ids}. 이 도서는 중복을 정리하기 전까지 판매 처리할 수 없습니다."


def books_on_sale(df: pd.DataFrame) -> pd.DataFrame:
    """SF-06: 판매중 도서만 고를 수 있게 한다. 판매완료 도서는 목록에 나오지 않는다."""
    return df[df["status"] == ON_SALE]


def duplicate_ids(df: pd.DataFrame) -> list[str]:
    """books.csv에 두 줄 이상 있는 도서 ID 목록 (Issue #10)."""
    counts = df["book_id"].value_counts()
    return sorted(counts[counts > 1].index)


def check_on_sale(df: pd.DataFrame, book_id: str) -> None:
    """고른 도서가 지금도 판매중인지 확인한다. 아니면 이유를 BookError로 알린다.
    같은 도서 ID가 여러 줄이면 어느 책을 판 것인지 알 수 없으므로 처리하지 않는다(Issue #10)."""
    rows = df[df["book_id"] == book_id]
    if rows.empty:
        raise BookError(MSG_NOT_FOUND)
    if len(rows) > 1:
        raise BookError(MSG_DUPLICATE.format(count=len(rows)))
    status = rows.iloc[0]["status"]
    if status == SOLD:
        raise BookError(MSG_ALREADY)
    if status != ON_SALE:
        raise BookError(f"판매 상태가 '{status}'로 되어 있어 처리할 수 없습니다. books.csv를 확인하세요.")


def done_message(book_id: str, title: str) -> str:
    """처리한 도서를 붙인 완료 메시지. 처리 뒤 선택 상자가 다른 도서로 바뀌어도 무엇을 처리했는지 알 수 있다."""
    return f"{MSG_DONE} ({book_id} {title})"


def mark_sold(df: pd.DataFrame, book_id: str) -> pd.DataFrame:
    """SF-07: 저장 직전에 다시 읽은 표로 상태를 확인한 뒤 판매완료로 바꾼 새 표를 돌려준다.
    판매완료를 판매중으로 되돌리는 기능은 두지 않는다(개발팀 제안)."""
    check_on_sale(df, book_id)
    new = df.copy()
    new.loc[new["book_id"] == book_id, "status"] = SOLD
    return new
