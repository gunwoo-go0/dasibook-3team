# 다시책방 위탁판매 관리

다시책방 직원이 위탁 도서 등록부터 위탁자별 정산액 확인까지 한 화면에서 처리하는 Streamlit 앱이다.
4조 다시책방의 제안요청서(RFP)에 맞춰 3팀이 개발했고, 데이터는 모두 수업용 가상 데이터다.

## 주요 기능

| 메뉴 | 하는 일 | 기능 ID |
| --- | --- | --- |
| 위탁 도서 등록 | 도서 ID, 도서명, 위탁자 ID, 판매 가격, 수수료율을 검사한 뒤 판매중으로 저장 | F-01 (SF-01, SF-02) |
| 도서 검색 (첫 화면) | 전체 목록을 보여 주고, 도서명·도서 ID·위탁자 ID로 검색 | F-02 (SF-03~SF-05) |
| └ AI 검색 도우미 | 질문 속 도서 ID·위탁자 ID·도서명으로 기존 검색을 실행하고, 찾은 도서만 근거로 Qwen3.5 2B가 답함 | 추가 (SF-12) |
| 판매 상태 변경 | 판매중 도서를 골라 확인을 받은 뒤 판매완료로 바꿈 (되돌리기 없음) | F-03 (SF-06, SF-07) |
| 위탁자별 정산 | 위탁자의 판매완료 도서만 모아 권별 정산액과 총정산액 계산 | F-04 (SF-08~SF-10) |

- 정산액 = 판매 가격 × (100 − 수수료율) ÷ 100, 원 미만은 버리고 권별 값을 더한다.
- 모든 데이터는 `data/books.csv` 한 파일에 저장된다(SF-11). 별도 서버나 DB는 없다.
- AI 검색 도우미는 데이터를 읽기만 한다. 모델 서버가 꺼져 있어도 다른 메뉴는 그대로 쓸 수 있다.

## 개발 환경

- Windows 10/11, Python 3.11
- Streamlit 1.51.0, pandas 2.3.3 (버전은 `requirements.txt`)
- AI 검색 도우미: Ollama + `qwen3.5:2b-q4_K_M`

## 설치

PowerShell에서 이 폴더로 이동한 뒤 실행한다. 가상환경은 반드시 Python 3.11로 만든다. 다른 버전으로 만들면 pyarrow 설치 파일이 맞지 않아 `pip install` 중 pyarrow 빌드 오류가 날 수 있다.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

AI 검색 도우미를 쓰려면 Ollama를 설치하고 모델을 한 번 내려받는다.

```powershell
ollama pull qwen3.5:2b-q4_K_M
.\.venv\Scripts\python.exe smoke_test.py
```

`smoke_test.py`가 답변을 출력하면 모델 연결이 된 것이다. "Ollama 서버에 연결할 수 없습니다"가 나오면 별도 터미널에서 `ollama serve`를 실행한다.

## 실행

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

브라우저에서 도서 검색 화면이 먼저 열리고 전체 도서 목록이 나온다.

## 기본 사용 방법

1. **위탁 도서 등록**: 다섯 항목을 모두 넣고 [등록]을 누른다. 도서 ID는 `B001`, 위탁자 ID는 `C001` 형식이고 수수료율은 1~99 정수다.
2. **도서 검색**: 검색 기준(도서명·도서 ID·위탁자 ID)을 고르고 검색어를 넣어 [검색]을 누른다. 검색어를 비우면 전체 목록이 나온다.
3. **AI 검색 도우미**: 도서 검색 화면 아래 칸에 "파이썬 입문 아직 안 팔렸어?", "C001 책 보여 줘"처럼 묻는다. 찾은 도서는 답변 아래 표로 나온다.
4. **판매 상태 변경**: 판매중 도서를 고르고 [판매완료 처리] → [확인]을 누른다.
5. **위탁자별 정산**: 위탁자 ID를 고르고 [정산 조회]를 누른다.

## 데이터

`data/books.csv` (UTF-8, 엑셀에서 열어도 한글이 깨지지 않게 BOM 포함)

| 열 | 뜻 | 규칙 |
| --- | --- | --- |
| book_id | 도서 ID | B+숫자 3자리, 중복 불가 |
| title | 도서명 | 빈칸 불가 |
| consignor_id | 위탁자 ID | C+숫자 3자리 |
| price | 판매 가격 | 원 단위 정수, 0보다 큼 |
| status | 판매 상태 | 판매중 / 판매완료 |
| fee_rate | 수수료율 | 1~99 정수(%) |

예시 데이터(B001~B008)로 되돌리려면 `git checkout -- data/books.csv`를 실행한다.
앱이 실행 중일 때 엑셀로 `books.csv`를 열어 두면 저장이 막힌다. 이때 앱은 멈추지 않고 안내만 띄우며 기존 데이터는 그대로 남는다.

## 테스트

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

업무 로직(등록·검색·판매·정산·저장)과 AI 검색 도우미의 검색 연동, 모델 오류 안내를 확인한다. 모델 연결 시험에는 실제 Ollama 대신 테스트용 가짜 서버를 쓴다.

## 파일 구조

```text
app.py              시작 파일: 사이드바 메뉴 4개, 첫 화면은 도서 검색
app_pages/          화면 4개 (register, search + AI 검색 도우미, sale, settle)
core/               화면과 분리한 업무 로직 (저장, 등록, 검색, 판매, 정산, AI 검색 연동)
llm.py              Ollama 연결과 답변 생성
smoke_test.py       모델 연결 확인
support/            AI 검색 도우미가 근거로 쓰는 업무 규칙
data/books.csv      예시 가상 데이터
tests/              pytest 자동 테스트
ui.py               화면 공통 도우미 (도서 표, 메시지)
```

## 출처 및 라이선스

| 항목 | 출처 | 라이선스 |
| --- | --- | --- |
| 수업 예제 Qwen_Chatbot_2026_Lab | 오픈소스SW의 이해 8장 실습 자료. `llm.py`, `smoke_test.py`, 대화 화면 흐름의 바탕 | 수업 자료 |
| Streamlit 1.51.0 | https://github.com/streamlit/streamlit | Apache-2.0 |
| pandas 2.3.3 | https://github.com/pandas-dev/pandas | BSD-3-Clause |
| ollama (Python) 0.6.3 | https://github.com/ollama/ollama-python | MIT |
| python-dotenv 1.2.1 | https://github.com/theskumar/python-dotenv | BSD-3-Clause |
| httpx 0.28.1 | https://github.com/encode/httpx | BSD-3-Clause |
| pytest 9.2.0 (테스트용) | https://github.com/pytest-dev/pytest | MIT |
| Ollama | https://github.com/ollama/ollama | MIT |
| Qwen3.5 2B 모델 | https://huggingface.co/Qwen/Qwen3.5-2B | Apache-2.0 |
| 데이터 | 직접 만든 가상 데이터 (실제 개인정보 없음) | 해당 없음 |
| 이미지 | 사용하지 않음 | 해당 없음 |
