"""테스트 공통 준비: 프로젝트 폴더를 import 경로에 넣고, 예시 데이터(data/books.csv)를 표로 읽어 준다."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.storage import load_books  # noqa: E402


@pytest.fixture
def books():
    """예시 데이터 B001~B008 (파일은 읽기만 한다)."""
    return load_books(ROOT / "data" / "books.csv")
