"""SF-11 데이터 저장과 불러오기: data/books.csv를 읽고 쓴다."""
import os
import tempfile
from pathlib import Path

import pandas as pd

from core.common import COLUMNS, DATA_FILE, BookError

ENCODING = "utf-8-sig"  # 엑셀로 열어도 한글이 깨지지 않게


def empty_books() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object") for c in COLUMNS})


def load_books(path: Path = DATA_FILE) -> pd.DataFrame:
    """화면을 열 때마다, 그리고 저장 직전에 다시 읽는다. 파일이 없거나 비어 있으면 빈 목록으로 시작한다.
    값은 모두 글자로 읽어, 손으로 잘못 고친 칸이 있어도 다시 저장할 때 원래 글자가 그대로 남는다."""
    if not path.exists() or path.stat().st_size == 0:
        return empty_books()
    try:
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding=ENCODING)
    except pd.errors.EmptyDataError:
        return empty_books()
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise BookError(f"{path.name} 파일 형식을 확인하세요. 쉼표나 따옴표가 깨졌을 수 있습니다.") from exc
    except OSError as exc:
        raise BookError(f"{path.name} 파일을 읽지 못했습니다. 다른 프로그램에서 열려 있는지 확인하세요.") from exc
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise BookError(f"{path.name}에 필요한 열이 없습니다: {', '.join(missing)}")
    df = df[COLUMNS].astype("object")
    for c in COLUMNS:
        df[c] = df[c].str.strip()
    return df.reset_index(drop=True)


def save_books(df: pd.DataFrame, path: Path = DATA_FILE) -> None:
    """임시 파일에 먼저 쓴 뒤 바꿔 끼운다. 저장 중 문제가 생겨도 기존 파일은 그대로 남는다."""
    tmp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".books-", suffix=".tmp")
        with os.fdopen(fd, "w", encoding=ENCODING, newline="") as f:
            df[COLUMNS].to_csv(f, index=False, lineterminator="\n")
        os.replace(tmp, path)
    except OSError as exc:
        if tmp:
            Path(tmp).unlink(missing_ok=True)
        raise BookError(
            f"{path.name}에 저장하지 못했습니다. 엑셀 등 다른 프로그램에서 파일을 열어 두었다면 닫고 다시 시도하세요."
        ) from exc
