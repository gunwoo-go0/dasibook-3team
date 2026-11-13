"""llm.py: 모델에 보내는 내용과 오류 안내 (SF-12). 실제 Ollama 대신 테스트용 가짜 서버를 쓴다."""
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import llm
from llm import ChatError, get_reply


class FakeOllama(BaseHTTPRequestHandler):
    """/api/chat만 흉내 낸다. mode로 정상·모델 없음·지연·출력 한도·빈 답변·서버 오류를 고른다."""
    mode = "ok"
    last_request = None

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).last_request = body
        if self.mode == "slow":
            time.sleep(1.5)
        if self.mode == "missing":
            return self.reply(404, {"error": f"model '{body['model']}' not found"})
        if self.mode == "broken":
            return self.reply(500, {"error": "out of memory"})
        content = {"empty": "  ", "length": "잘린 답"}.get(self.mode, "B001 파이썬 입문은 판매중입니다.")
        self.reply(200, {"model": body["model"], "created_at": "2026-11-13T00:00:00Z",
                         "message": {"role": "assistant", "content": content},
                         "done": True, "done_reason": "length" if self.mode == "length" else "stop"})

    def reply(self, status, data):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


class QuietServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        pass  # 시간 초과 시험에서 끊긴 연결 오류는 무시한다


@pytest.fixture
def server(monkeypatch):
    httpd = QuietServer(("127.0.0.1", 0), FakeOllama)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    monkeypatch.setattr(llm, "BASE_URL", f"http://127.0.0.1:{httpd.server_port}")
    FakeOllama.mode, FakeOllama.last_request = "ok", None
    yield FakeOllama
    httpd.shutdown()


def test_정상_답변과_모델에_보내는_내용(server):
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"이전 {i}", "books": []}
               for i in range(8)]
    found = "검색 조건: 도서명 '파이썬 입문'\n찾은 도서 2권:\n- 도서 ID B001 | 도서명 파이썬 입문"
    assert get_reply(history, "  파이썬 입문 팔렸어? ", found) == "B001 파이썬 입문은 판매중입니다."

    sent = server.last_request
    assert sent["model"] == llm.MODEL and sent["stream"] is False and sent["think"] is False
    assert sent["options"] == {"temperature": 0, "num_ctx": 8192, "num_predict": 512}
    messages = sent["messages"]
    assert len(messages) == 1 + llm.MAX_HISTORY + 1  # 시스템 + 최근 대화 6개 + 질문
    assert messages[0]["role"] == "system"
    assert "업무 규칙:" in messages[0]["content"] and found in messages[0]["content"]
    assert [m["content"] for m in messages[1:-1]] == [f"이전 {i}" for i in range(2, 8)]
    assert all(set(m) == {"role", "content"} for m in messages)  # 표 같은 화면용 값은 보내지 않는다
    assert messages[-1] == {"role": "user", "content": "파이썬 입문 팔렸어?"}


@pytest.mark.parametrize("question", ["", "   ", "가" * 301])
def test_질문은_1자부터_300자까지(server, question):
    with pytest.raises(ChatError, match="질문은 1~300자로 입력하세요."):
        get_reply([], question)
    assert server.last_request is None  # 모델을 부르지 않는다


def test_모델이_없으면_내려받기_안내(server):
    server.mode = "missing"
    with pytest.raises(ChatError) as exc:
        get_reply([], "B001 있어?")
    assert str(exc.value) == f"{llm.MODEL} 모델이 없습니다. ollama pull로 내려받으세요."


def test_서버가_꺼져_있으면_연결_안내(monkeypatch):
    with socket.socket() as s:  # 비어 있는 포트를 하나 잡았다가 닫는다
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    monkeypatch.setattr(llm, "BASE_URL", f"http://127.0.0.1:{port}")
    with pytest.raises(ChatError, match="Ollama 서버에 연결할 수 없습니다. ollama serve 실행 여부를 확인하세요."):
        get_reply([], "B001 있어?")


def test_응답이_늦으면_시간_초과_안내(server, monkeypatch):
    server.mode = "slow"
    monkeypatch.setattr(llm, "TIMEOUT", 0.5)
    with pytest.raises(ChatError, match="모델 응답이 너무 오래 걸립니다. 질문을 짧게 줄여 다시 시도하세요."):
        get_reply([], "B001 있어?")


@pytest.mark.parametrize("mode, message", [
    ("length", "답변이 출력 한도에 도달했습니다."),
    ("empty", "빈 답변을 받았습니다."),
    ("broken", "모델 실행에 실패했습니다."),
])
def test_그_밖의_오류_안내(server, mode, message):
    server.mode = mode
    with pytest.raises(ChatError, match=message):
        get_reply([], "B001 있어?")
