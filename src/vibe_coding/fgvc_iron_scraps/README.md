# 철스크랩 위험물 분류 — 웹 & 허브 뼈대

기존에 개발한 **철스크랩 위험물 분류 모델과 시각화 함수들을 API로 사용하기 위한**
웹 프런트 + 허브 서버의 뼈대다. 딱 뼈대까지가 이 폴더의 범위다.

지금은 그 모델이 아직 붙어 있지 않다. 모델이 앉을 자리에는 사진을 받으면 "사진 잘
받았어요!" 만 돌려주는 **더미 AI 서버**가 대신 서 있다. 그래서 이 저장소만 가지고도
업로드 → 전달 → 결과 표시 → 오류 처리까지 전 구간을 눌러볼 수 있다.

모델이 준비되면 환경변수 하나(`AI_API_URL`)를 바꾸고 더미를 지우면 된다. 허브 코드는
그대로 둔다.

## 사용법

### 서버 띄우기

터미널 두 개가 필요하다. 더미 AI를 먼저 띄운다.

```bash
# 터미널 1 — 더미 AI (모델 자리)
uv run uvicorn vibe_coding.fgvc_iron_scraps.dummy_ai:app --port 9000 --reload

# 터미널 2 — 허브
uv run uvicorn vibe_coding.fgvc_iron_scraps.hub:app --port 8000 --reload
```

`uv run` 없이 맨 `uvicorn` 으로 띄우면 `ModuleNotFoundError` 로 죽는다. `src/`
레이아웃이라 import 가 `.venv` 의 editable 설치를 거쳐야 해석된다.

### 브라우저에서

`http://127.0.0.1:8000` → 대문 → **"사진 분석하러 가기"** → 업로드 화면.

업로드 화면은 파일 선택 → 미리보기 → 분석하기 → 결과 순으로 흐른다. 전송 중에는
버튼이 "분석 중…" 으로 바뀌며 비활성화된다.

### curl 로

```bash
curl -F "file=@scrap.png;type=image/png" http://127.0.0.1:8000/api/analyze
# {"message":"사진 잘 받았어요!","filename":"scrap.png","size":70}

curl -F "file=@memo.txt;type=text/plain" http://127.0.0.1:8000/api/analyze
# {"detail":"이미지 파일만 올릴 수 있어요"}
```

### 테스트

```bash
uv run pytest -q
```

**서버를 띄우지 않아도 된다.** `httpx.MockTransport` 로 AI 응답을 갈아끼우고
`hub.create_app(analyzer=...)` 로 주입하기 때문에, 연결 실패와 타임아웃까지 서버 없이
재현한다.

## 설계 구조

```
브라우저
   │  ① 사진 업로드 (multipart/form-data, 필드명 file)
   ▼
┌─ 허브 :8000 ─────────────────────────┐
│  hub.py       라우팅, 오류를 HTTP 상태로 변환 │
│  analyzer.py  검증(타입·5MB) + AI API 호출    │
│  static/      대문·업로드 화면 (단일 HTML)    │
└───────────────┬──────────────────────┘
                │  ② AI_API_URL 로 전달 (httpx)
                ▼
┌─ AI API :9000 ───────────────────────┐
│  지금 : dummy_ai.py — 더미            │
│  나중 : 철스크랩 위험물 분류 모델      │
│         + 시각화 함수                 │
└──────────────────────────────────────┘
```

### 왜 프로세스를 둘로 나눴나

더미를 허브 앱 안의 라우트로 넣는 게 더 간단했지만 그러지 않았다.

1. **허브에 임시 코드가 섞이지 않는다.** `hub.py` 에는 `mock`·`dummy` 라는 단어조차
   없다. 허브는 모델이 붙은 뒤에도 그대로 쓸 코드다.
2. **바깥과 통신하는 코드를 지금 검증할 수 있다.** 더미 서버를 끄는 것만으로 연결
   실패(502) 경로가 실제로 재현된다. 모델을 붙이는 시점에 처음 쓰는 코드가 아니게 된다.

### 파일

| 파일 | 역할 |
|---|---|
| `hub.py` | FastAPI 허브. `GET /`, `GET /analyze`, `POST /api/analyze` |
| `analyzer.py` | `ImageAnalyzer` — 사진 검증 후 AI API 호출. `AnalyzeError` 로 오류를 status 와 함께 던진다 |
| `dummy_ai.py` | 모델 자리를 대신하는 더미 서버. **모델이 붙으면 삭제** |
| `static/index.html` | 대문 |
| `static/analyze.html` | 업로드·결과 화면 |
| `CLAUDE.md` | 오류 매핑, 테스트 전략, 인수인계 등 상세 |

화면 두 개는 빌드 도구도 프레임워크도 CDN도 쓰지 않는다. HTML 한 파일에 CSS·JS 가
인라인으로 들어 있고, 허브가 `FileResponse` 로 그대로 내려준다.

### 응답 규약

성공(200)은 AI API 의 JSON 을 그대로 통과시킨다. 지금은 더미가 주는
`{"message", "filename", "size"}` 다. **화면은 `message` 를 그대로 띄울 뿐 문구를
하드코딩하지 않는다** — 모델이 붙어 응답이 바뀌면 화면이 따라간다.

실패는 FastAPI 기본 형태인 `{"detail": "..."}` 로 통일했다.

| status | 언제 |
|---|---|
| 415 | 이미지가 아닌 파일 |
| 413 | 5MB 초과 |
| 422 | `file` 필드 누락 |
| 502 | AI API 연결 실패 / 200 아님 / JSON 아님 |
| 504 | AI API 응답이 10초 안에 없음 |

예외 클래스를 종류별로 늘리지 않고 `AnalyzeError(status, message)` 하나로 통일했다.

## 지금 하지 않는 것

뼈대의 범위를 분명히 해두기 위해 적는다.

- **모델 추론이 없다.** 위험물 분류도 시각화도 아직 이 저장소에 없다.
- 인증·레이트리밋·업로드 파일 보존이 없다. 로컬 개발용이다.
- `content_type` 은 브라우저가 보낸 값을 그대로 믿는다. 파일 내용은 보지 않는다.
- 업로드 파일을 전부 메모리로 읽은 뒤 크기를 검사한다. 5MB 제한이라 문제되지 않는 선택이다.

## 모델을 붙일 때

1. `AI_API_URL` 을 모델 서버 주소로 바꾼다. 허브 코드는 손대지 않는다.
2. 요청 형식이 `file` 필드 multipart 가 아니라면 `analyzer.py` 의 `_request` 한 곳만 고친다.
3. 응답 스키마가 확정되면 `static/analyze.html` 의 결과 표시부를 그에 맞게 고친다.
4. `dummy_ai.py` 와 `tests/test_dummy_ai.py` 를 지운다.

---

작성: 클로드  
검수: 클로드 쫄병 1호  
컨펌: jongha
