# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 명령어

[uv](https://docs.astral.sh/uv/)로 관리하는 Python 3.13 프로젝트다. `src/` 레이아웃이라 `vibe_coding` import는 `.venv`에 editable로 설치된 `vibe_coding.pth`를 통해서만 해석된다. `.venv`가 활성화되지 않은 상태의 맨 `pytest`는 실패하므로 항상 `uv run …`을 사용한다.

```bash
uv sync                                           # 의존성 설치
uv run pytest                                     # 전체 테스트 실행
uv run pytest tests/test_calculator.py::test_add  # 단일 테스트 실행
uv run pytest -q -k divide                        # 이름으로 필터링해 실행
```

`pytest`는 dev dependency group이 아니라 `[project] dependencies`에 선언돼 있어서 `uv sync`만으로 테스트 실행 준비가 끝난다.

린터나 포매터는 설정돼 있지 않다. 포매팅이 자동으로 강제된다고 설명하지 말 것.

## 두 개의 진입점 — 서로 다른 함수다

`main()`이 서로 무관한 두 위치에 정의돼 있고, 콘솔 스크립트는 저장소 루트의 것을 실행하지 **않는다**.

| 명령어 | 실행되는 코드 | 출력 |
|---|---|---|
| `uv run python main.py` | 루트 `main.py` | `Hello from vibe-coding!` |
| `uv run vibe-coding` | `vibe_coding:main` (`[project.scripts]`) | `vibe-coding = vibe_coding:main` |

루트 `main.py`는 `src/` 밖에 있어 설치되는 패키지에 포함되지 않으며, `vibe-coding` 명령에서 도달할 수 없다. CLI 동작을 바꿀 때는 둘 중 어느 쪽을 의도한 것인지 먼저 확인한다.

## 아키텍처

`uv_build` 백엔드가 빌드하는 `src/` 레이아웃이다. `Calculator`는 최상위 패키지에서 바로 import할 수 있도록 두 번 재노출된다.

```
src/vibe_coding/calc/calculator.py   Calculator 정의
src/vibe_coding/calc/__init__.py     재노출
src/vibe_coding/__init__.py          다시 재노출  ->  from vibe_coding import Calculator
```

`tests/test_calculator.py`가 이 평탄한 경로에 의존한다. **새 모듈을 추가하면 두 `__init__.py`와 각각의 `__all__`을 모두 거쳐 노출시켜야** 기존 코드가 기대하는 방식으로 접근할 수 있다.

## 컨벤션

- 테스트 docstring은 한국어로 작성한다 (예: `"""더하기 테스트"""`). 새 테스트도 이 방식을 따른다.
- 예상되는 예외는 `test_divide_by_zero`처럼 `pytest.raises`로 검증한다.
- `Calculator` 메서드에는 타입 힌트가 없다. 개별 메서드에만 추가하지 말고, 기존 스타일을 그대로 두거나 클래스 전체를 의도적으로 한 번에 전환한다.
