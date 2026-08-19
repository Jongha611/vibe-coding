# tdd-python

파이썬 프로젝트에 TDD 순서를 강제하는 Claude Code 플러그인이다. 훅 두 개와 스킬 하나로
이루어진다.

## 무엇을 하는가

### PreToolUse — 테스트 선행 확인 (`tdd_guard.py`)

소스 파일을 Write/Edit 할 때 세 단계로 본다.

1. 대응하는 테스트 파일(`tests/test_<name>*.py`)이 존재하는가
2. 이번 편집이 **새 public API** 를 추가하는가 (편집 후 내용을 AST 로 비교) →
   추가한다면 그 이름이 테스트 어딘가에 이미 언급돼 있는가
3. → 추가한다면 지금 **실패 중인 테스트가 있는가** (Red)

하나라도 어긋나면 편집을 `deny` 하고 무엇을 먼저 하라는지 알려준다. 새 API 를 추가하지
않는 편집(리팩토링·버그 수정)은 1번만 통과하면 된다.

재노출·설정 파일(`__init__.py`, `__main__.py`, `conftest.py`, `setup.py`)과 테스트
디렉터리 자신은 검사 대상이 아니다.

### PostToolUse — 테스트 실행과 Red/Green 기록 (`tdd_pytest.py`)

소스나 테스트가 바뀌면 테스트를 돌리고, 실패를 **무엇을 고쳤느냐에 따라 다르게** 다룬다.

| 편집한 곳 | 테스트 실패 시 |
|---|---|
| 테스트 | 정상(Red). 차단하지 않고 "이제 구현하면 된다"고 알린다 |
| 소스 | 구현이 틀렸다는 뜻. `decision: block` 으로 되돌린다 |

결과는 `<프로젝트>/.claude/.tdd-state.json` 에 남고, 다음 편집에서 guard 가 이 파일을
읽어 Red 여부를 판단한다. 이 파일은 `.gitignore` 에 넣는 것을 권한다.

### 스킬 — `tdd-python:write-unit-tests`

저장소의 기존 테스트에서 실행 명령·파일 배치·import 깊이·docstring 언어·검증 스타일을
먼저 뽑아낸 뒤, 그 컨벤션에 맞춰 테스트를 쓴다. 엣지케이스는 모듈당 5개로 제한하고,
버그를 발견하면 소스를 고치는 대신 보고한다.

## 설치

```bash
/plugin marketplace add <이 저장소 경로 또는 GitHub repo>
/plugin install tdd-python@jongha-local
```

## 설정

프로젝트마다 다른 값은 환경변수로 받는다. 전부 선택 사항이며, 기본값은 uv + `src/`
레이아웃 기준이다.

| 환경변수 | 기본값 | 뜻 |
|---|---|---|
| `TDD_SRC_DIR` | `src` | 감시할 소스 루트 (프로젝트 기준 상대경로) |
| `TDD_TESTS_DIR` | `tests` | 테스트 루트 |
| `TDD_TEST_CMD` | `uv run pytest -q -rfE` | 테스트 명령 |
| `TDD_TEST_TIMEOUT` | `110` | 테스트 타임아웃(초) |
| `TDD_GUARD` | (없음) | `off`/`0`/`false`/`no` 면 훅 전체를 우회 |

`.claude/settings.json` 의 `env` 블록에 넣으면 프로젝트 단위로 적용된다.

```json
{
  "env": {
    "TDD_SRC_DIR": "myapp",
    "TDD_TEST_CMD": "poetry run pytest -q -rfE"
  }
}
```

`TDD_TEST_CMD` 를 바꿀 때 **실패 요약 옵션(`-rfE`)을 빼지 않는 편이 좋다.** 실패한
테스트 이름을 그 출력에서 파싱하기 때문이다. 빼더라도 Red 판정 자체는 종료 코드로 하므로
동작은 하고, 실패 목록만 비게 된다.

## 아는 한계

- `matcher` 는 `Write|Edit` 다. 다른 편집 도구로 소스를 바꾸면 검사를 우회한다.
- guard 2단계는 편집 후 내용을 재구성해 AST 로 본다. 재구성이 불가능하거나 결과가
  파싱되지 않으면 판단을 포기하고 통과시킨다 (막는 쪽이 아니라 통과하는 쪽으로 실패한다).
- "테스트에 이름이 언급됐는가" 는 단어 단위 정규식 검색이다. 우연히 같은 이름이 다른
  맥락에 있으면 통과한다.
- 테스트 실행은 매 편집마다 전체 스위트를 돌린다. 스위트가 느린 프로젝트에는
  `TDD_TEST_CMD` 로 범위를 좁히거나 `TDD_TEST_TIMEOUT` 을 늘려야 한다.
