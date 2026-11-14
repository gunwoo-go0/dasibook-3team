from llm import ChatError, get_reply

if __name__ == "__main__":
    try:
        print(get_reply([], "수수료율은 몇 퍼센트까지 정할 수 있나요?"))
    except ChatError as exc:
        print(f"연결 확인 실패: {exc}")
        raise SystemExit(1)
