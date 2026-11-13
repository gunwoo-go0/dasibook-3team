"""SF-11 저장과 불러오기 (NF-01, NF-03)."""
import os

import pytest

from core.common import COLUMNS, BookError
from core.storage import load_books, save_books


def test_없는_파일이나_빈_파일은_빈_목록(tmp_path):
    assert load_books(tmp_path / "none.csv").empty
    (tmp_path / "empty.csv").write_text("", encoding="utf-8")
    assert load_books(tmp_path / "empty.csv").empty


def test_저장하고_다시_읽으면_그대로(tmp_path, books):
    path = tmp_path / "books.csv"
    save_books(books, path)
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")  # 엑셀 한글용 BOM
    assert load_books(path).equals(books)


def test_열이_빠진_파일은_이유를_알린다(tmp_path):
    path = tmp_path / "books.csv"
    path.write_text("book_id,title\nB001,파이썬 입문\n", encoding="utf-8")
    with pytest.raises(BookError, match="필요한 열이 없습니다"):
        load_books(path)


def test_저장에_실패해도_기존_파일은_그대로(tmp_path, books, monkeypatch):
    path = tmp_path / "books.csv"
    save_books(books, path)
    before = path.read_bytes()

    def locked(*args, **kwargs):  # 엑셀이 파일을 잡고 있을 때와 같은 오류
        raise PermissionError("locked")

    monkeypatch.setattr(os, "replace", locked)
    with pytest.raises(BookError, match="저장하지 못했습니다"):
        save_books(books.iloc[:1], path)
    assert path.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["books.csv"]  # 임시 파일도 남지 않는다


def test_임시_파일을_못_만들어도_안내만_한다(tmp_path, books, monkeypatch):
    import tempfile

    def denied(*args, **kwargs):  # 쓰기 권한이 없는 폴더
        raise PermissionError("denied")

    monkeypatch.setattr(tempfile, "mkstemp", denied)
    with pytest.raises(BookError, match="저장하지 못했습니다"):
        save_books(books, tmp_path / "books.csv")


def test_예시_데이터는_열이_모두_있다(books):
    assert list(books.columns) == COLUMNS and len(books) == 8
