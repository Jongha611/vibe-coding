# vibe-coding

바이브코딩 강의를 따라가되, 예제를 그대로 베끼지 않고 직접 손으로 실습한 기록이다.

파이썬 코드 자체보다 **Claude Code의 기능을 하나씩 붙여보는 것**이 목적이다. 그래서
`Calculator`·`Gugudan` 같은 예제는 일부러 작게 두고, 그 위에 서브에이전트·스킬·훅·
플러그인을 차례로 얹었다.

## 빠른 시작

```bash
uv sync                             # 의존성 설치 (Python 3.13)
uv run pytest                       # 테스트 39개
uv run python -m vibe_coding.stats  # 이번 달 커밋 통계 출력
```

## 실습한 Claude Code 기능

커밋 이력의 순서가 곧 학습 순서다.

| 기능 | 위치 | 무엇을 해봤나 |
|---|---|---|
| 서브에이전트 | `.claude/agents/` | `unit-test-writer`·`edge-case-test-writer`·`code-reviewer` 3개. 해피패스와 엣지케이스를 서로 다른 에이전트에 맡겨 나눠 작성 |
| 스킬 | `.claude/skills/write-unit-tests/` | 테스트 컨벤션(한국어 docstring, 평면 함수 구조, 엣지케이스 모듈당 5개 제한)을 문서로 고정해 매번 설명하지 않게 함 |
| 훅 | `.claude/hooks/` | `PreToolUse`로 테스트 없는 소스 편집을 거부하고, `PostToolUse`로 편집 직후 pytest를 돌려 Red/Green을 추적 |
| 플러그인 | `plugins/tdd-python/` | 위 훅과 스킬을 플러그인으로 묶고, `.claude-plugin/marketplace.json`으로 로컬 마켓플레이스까지 구성 |
| CLAUDE.md | [`CLAUDE.md`](CLAUDE.md) | 저장소 규칙을 Claude에게 상시 주입 |

## 연습용 코드

`src/` 레이아웃이며, 모든 클래스는 `from vibe_coding import ...` 한 줄로 꺼낼 수 있도록
서브패키지와 최상위 패키지에서 두 번 재노출한다.

| 클래스 | 위치 | 내용 |
|---|---|---|
| `Calculator` | `src/vibe_coding/calc/` | 사칙연산. 첫 테스트 실습 대상 |
| `Gugudan` | `src/vibe_coding/tt/` | 구구단. 스킬과 TDD 훅을 처음 적용해 만든 것 |
| `GitStats` | `src/vibe_coding/stats/` | `git log`를 읽어 이번 달 작성자별·요일별 커밋 수를 출력. 달이 바뀌면 저장된 상태 없이 저절로 0부터 다시 센다 |

## 구조

```
src/vibe_coding/     소스 (calc, tt, stats)
tests/               test_<모듈>.py + test_<모듈>_edge_cases.py
.claude/             에이전트·스킬·훅·설정
plugins/tdd-python/  훅과 스킬을 묶은 플러그인
```

## 알아둘 것

**TDD 훅이 켜져 있다.** `.claude/settings.json`이 훅 두 개를 걸어두기 때문에, Claude가
`src/` 아래를 편집하려면 ① 대응하는 테스트 파일이 있어야 한다. 여기에 더해 새 public
API를 추가하는 편집이라면 ② 그 이름이 테스트에 이미 등장하고 ③ 지금 실패 중인 테스트가
있어야 한다. 하나라도 어긋나면 편집이 거부된다 — 고장이 아니라 의도된 동작이다.
리팩토링·버그 수정은 ①만 지나면 된다. 끄려면 `TDD_GUARD=off`.

**항상 `uv run`을 쓴다.** `src/` 레이아웃이라 `vibe_coding` import는 `.venv`의 editable
설치를 거쳐야 해석된다. `.venv`를 활성화하지 않은 맨 `pytest`는 `ModuleNotFoundError`로
죽는데, 테스트가 깨진 게 아니라 실행 방법의 문제다.

**진입점이 두 개이고 서로 다른 함수다.** `uv run python main.py`와 `uv run vibe-coding`이
각각 다른 `main()`을 부른다. 자세한 내용은 [CLAUDE.md](CLAUDE.md)에 있다.

---

작성: 클로드  
검수: 클로드 쫄병 1호
