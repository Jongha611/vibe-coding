# fgvc_iron_scraps

사진을 올리면 고철 종류를 분석해 보여주는 웹페이지다. 저장소 전반 규칙(uv, TDD 훅,
테스트 컨벤션)은 루트 [`CLAUDE.md`](../../../CLAUDE.md)에 있다. 여기에는 이 폴더에서만
통하는 결정만 적는다.

## 왜 서버가 두 개인가

**허브는 진짜고, 더미 AI는 임시다.**

```
┌─ 허브 :8000 ────────────┐            ┌─ 더미 AI :9000 ──┐
│ GET  /            대문   │            │ POST /analyze    │
│ GET  /analyze     업로드 │            │ "사진 잘 받았어요!"│
│ POST /api/analyze  ──────│──httpx──>  │ (나중에 삭제)     │
└─────────────────────────┘            └──────────────────┘
        hub.py                            dummy_ai.py
```

진짜 고철 분석 AI API가 아직 없어서 그 자리에 더미를 세웠다. 더미를 허브 앱 안의
라우트로 넣지 않고 **별도 프로세스**로 분리한 이유는 두 가지다.

1. `hub.py`에 `mock`·`dummy` 같은 흔적이 남지 않는다. 허브는 나중에도 그대로 쓸 코드다.
2. 더미 서버를 꺼보는 것만으로 연결 실패(502) 경로를 실제로 확인할 수 있다.

`dummy_ai.py`를 고쳐서 허브의 동작을 바꾸려 하지 말 것. 더미는 진짜 API의 대역일 뿐이고,
허브 쪽 로직은 전부 `analyzer.py`에 있다.

## 사용법

### 서버 띄우기

터미널 두 개가 필요하다. 더미 AI를 먼저 띄운다.

```bash
# 터미널 1 — 더미 AI
uv run uvicorn vibe_coding.fgvc_iron_scraps.dummy_ai:app --port 9000 --reload

# 터미널 2 — 허브
uv run uvicorn vibe_coding.fgvc_iron_scraps.hub:app --port 8000 --reload
```

`--reload` 는 개발용이다. 두 서버 모두 `uv run` 없이 맨 `uvicorn` 으로 띄우면
`ModuleNotFoundError` 로 죽는다 — `src/` 레이아웃이라 그렇다.

### 브라우저에서

`http://127.0.0.1:8000` → 대문 → **"사진 분석하러 가기"** → 업로드 화면.

업로드 화면은 파일 선택 → 미리보기 → 분석하기 → 결과 순으로 흐른다. 전송 중에는 버튼이
"분석 중…" 으로 바뀌고 비활성화돼서 연타로 중복 요청이 나가지 않는다.

### curl 로

```bash
# 정상
curl -F "file=@scrap.png;type=image/png" http://127.0.0.1:8000/api/analyze
# {"message":"사진 잘 받았어요!","filename":"scrap.png","size":70}

# 이미지가 아닌 파일
curl -F "file=@memo.txt;type=text/plain" http://127.0.0.1:8000/api/analyze
# {"detail":"이미지 파일만 올릴 수 있어요"}
```

### 테스트

```bash
uv run pytest -q                      # 전체
uv run pytest tests/test_hub.py -q    # 허브만
```

**서버를 띄우지 않아도 된다.** 아래 [테스트](#테스트-1) 절 참고.

## `AI_API_URL`

허브가 사진을 넘길 상대 주소다. 기본값은 `ImageAnalyzer.DEFAULT_API_URL`
(`http://127.0.0.1:9000/analyze`) 이라 아무것도 설정하지 않으면 더미를 본다.

```bash
AI_API_URL=https://내부주소/analyze uv run uvicorn vibe_coding.fgvc_iron_scraps.hub:app
```

## 오류 매핑

예외를 종류별로 나누지 않고 `AnalyzeError(status, message)` 하나로 통일했다. 허브가 그걸
`HTTPException` 으로 바꿔 내보내므로 화면에는 FastAPI 기본 형태인 `{"detail": "..."}`
로 도착한다.

| 상황 | status | detail |
|---|---|---|
| `content_type` 이 `ALLOWED_TYPES` 에 없음 | 415 | 이미지 파일만 올릴 수 있어요 |
| `MAX_BYTES`(5MB) 초과 | 413 | 파일이 너무 큽니다 (5MB 이하) |
| `file` 필드 누락 | 422 | FastAPI 기본 검증 응답 (detail 이 문자열이 아니라 객체 배열) |
| AI 서버에 연결 실패 | 502 | 분석 서버에 연결할 수 없어요 |
| AI 응답이 10초(`TIMEOUT`) 안에 없음 | 504 | 분석 서버 응답이 느려요 |
| AI 응답이 200이 아님 | 502 | 분석 서버 오류 (…) |
| AI 응답이 JSON 이 아님 | 502 | 분석 서버 응답을 이해할 수 없어요 |

새 오류를 추가할 때도 예외 클래스를 늘리지 말고 `AnalyzeError` 에 status 를 담는다.

422 의 `detail` 만 문자열이 아니라 객체 배열이다. `analyze.html` 은 문자열이 아니면
"알 수 없는 오류가 발생했어요" 로 대체한다.

## 테스트

AI 서버도 허브 서버도 **띄우지 않고** 검증한다.

- `httpx.MockTransport` 로 AI 응답을 갈아끼운다 — 연결 실패·타임아웃까지 재현된다.
- `hub.create_app(analyzer=...)` 로 그 분석기를 주입한다.
- 라우트 함수를 `create_app()` 안에 둔 건 스타일이 아니라 `tdd_guard` 때문이다. 모듈
  최상위에 두면 새 public API 로 잡혀서 테스트에 라우트 이름을 억지로 적어야 한다.

| 파일 | 개수 | 무엇을 보나 |
|---|---|---|
| `tests/test_analyzer.py` | 11 | 타입·크기 검증, 5MB 경계, httpx 오류 → status 매핑 |
| `tests/test_hub.py` | 8 | 두 화면 서빙, 200/415/413/422/502/504 |
| `tests/test_dummy_ai.py` | 3 | 더미 응답 형식 |

## 결과 (2026-08-28 기준)

`uv run pytest` — **67개 전부 통과** (기존 45 + 이번 22).

두 서버를 실제로 띄우고 curl 로 확인한 것:

| 확인 | 결과 |
|---|---|
| `GET /` | 200, `text/html`, "사진 분석하러 가기" 버튼 존재 |
| `GET /analyze` | 200, `text/html` |
| PNG 업로드 | 200 `{"message":"사진 잘 받았어요!","filename":"scrap.png","size":70}` |
| `.txt` 업로드 | 415 `이미지 파일만 올릴 수 있어요` |
| 6MB 파일 업로드 | 413 `파일이 너무 큽니다 (5MB 이하)` |
| `file` 필드 누락 | 422 (FastAPI 기본 배열 형태) |
| **더미 AI 를 끄고 업로드** | 502 `분석 서버에 연결할 수 없어요` |

마지막 항목이 프로세스를 분리한 덕에 가능해진 검증이다.

**아직 확인하지 않은 것** — 브라우저를 실제로 열어 클릭해본 적은 없다. curl 과 pytest
까지다. 화면 쪽에서 다음 세 가지는 코드로만 담보돼 있다.

- 다크모드 실제 렌더링 (`prefers-color-scheme` 분기는 두 파일 모두에 있음)
- 모바일 폭에서 가로 스크롤 없음 (`max-width: 100%`, `box-sizing: border-box`)
- `fetch` 자체가 실패할 때의 화면. `analyze.html` 은 `try/catch` 가 아니라
  `.then(onOk, onErr)` 2인자 형태로 잡는다 — `catch` 로 grep 하면 안 나오니 주의.

## 알려진 단순화

- 허브가 업로드 파일을 **전부 메모리로 읽은 뒤에** 크기를 검사한다. 5MB 제한 정도라
  문제되지 않지만, 아주 큰 파일이 올라오면 그만큼 메모리를 쓴다. 스트리밍 검사로 바꾸려면
  `hub.py` 의 `api_analyze` 를 손봐야 한다.
- `content_type` 은 브라우저가 보낸 값을 그대로 믿는다. 파일 내용(매직 넘버)은 보지 않는다.
  `curl -F "file=@memo.txt;type=image/png"` 는 통과한다.
- 허브에 인증·레이트리밋·업로드 파일 보존이 없다. 로컬 개발용이다.

## 인수인계

### 진짜 API 가 생기면

1. `AI_API_URL` 을 진짜 주소로 바꾼다. **허브 코드는 손대지 않는다.**
2. 응답 스키마가 확정되면 `static/analyze.html` 의 결과 표시부만 고친다.
   지금은 `message` 를 그대로 띄우고 `filename`·`size` 를 부가 정보로 보여준다.
   **화면에 "사진 잘 받았어요!" 를 하드코딩하지 않았으므로** 서버 문구만 바뀌면 화면은
   그대로 따라간다.
3. `dummy_ai.py` 와 `tests/test_dummy_ai.py` 를 지운다. 그 외에는 지울 것이 없다.

진짜 API 의 요청 형식이 `file` 필드 multipart 가 아니라면 고칠 곳은
`analyzer.py` 의 `_request` 한 곳이다.

### 화면을 고칠 때

`.claude/agents/web-ui-writer.md` 에이전트가 이 화면들의 규칙(단일 HTML, 외부 요청 금지,
라이트/다크 CSS 변수, 한국어 문구)을 들고 있다. 화면을 크게 손볼 때는 그 에이전트에
맡기면 컨벤션이 유지된다.

### 남은 것 / 주의

- **브라우저 실기동 검증이 안 돼 있다.** 위 "아직 확인하지 않은 것" 세 가지를 실제로
  열어보는 게 다음 차례다.
- `starlette` 이 `httpx` 기반 `TestClient` 를 deprecated 로 경고한다
  (`install httpx2`). 지금은 경고일 뿐 테스트는 통과한다. 나중에 `httpx2` 로 옮길 때
  `tests/test_hub.py`·`tests/test_dummy_ai.py` 의 `TestClient` 사용부가 영향을 받는다.
- `ImageAnalyzer` 는 저장소 컨벤션대로 `from vibe_coding import ImageAnalyzer` 로도
  꺼낼 수 있게 두 번 재노출돼 있다. 새 클래스를 추가하면 두 `__init__.py` 를 모두 고쳐야
  한다.
- `hub.py`·`dummy_ai.py` 의 `create_app` 은 이름이 같다. import 할 때 모듈 경로까지
  적어야 헷갈리지 않는다.
