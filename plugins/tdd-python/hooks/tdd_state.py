"""TDD 훅 두 개가 공유하는 설정·경로·Red 상태 파일 입출력.

tdd_pytest.py 가 테스트를 돌린 뒤 상태를 쓰고, tdd_guard.py 가 그걸 읽어
"지금 실패 중인 테스트가 있는가"(Red)를 판단한다.

프로젝트마다 달라지는 값은 전부 환경변수로 받는다. 기본값은 uv + src 레이아웃이다.

  TDD_SRC_DIR       감시할 소스 루트, 프로젝트 기준 상대경로 (기본 "src")
  TDD_TESTS_DIR     테스트 루트, 프로젝트 기준 상대경로 (기본 "tests")
  TDD_TEST_CMD      테스트 명령 (기본 "uv run pytest -q -rfE")
  TDD_TEST_TIMEOUT  테스트 타임아웃 초 (기본 "110")
  TDD_GUARD=off     훅 전체 우회
"""

import json
import os
import shlex
from pathlib import Path

DEFAULT_SRC_DIR = "src"
DEFAULT_TESTS_DIR = "tests"
DEFAULT_TEST_CMD = "uv run pytest -q -rfE"
DEFAULT_TIMEOUT = 110

OFF_VALUES = {"off", "0", "false", "no"}


def _root():
    """훅이 붙은 프로젝트의 루트. Claude Code 가 넘겨주는 값을 우선한다."""
    raw = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(raw).resolve() if raw else Path.cwd().resolve()


def _under_root(env_name, default):
    return (_root() / os.environ.get(env_name, default)).resolve()


PROJECT_ROOT = _root()
SRC_DIR = _under_root("TDD_SRC_DIR", DEFAULT_SRC_DIR)
TESTS_DIR = _under_root("TDD_TESTS_DIR", DEFAULT_TESTS_DIR)
STATE_FILE = PROJECT_ROOT / ".claude" / ".tdd-state.json"


def runner_command():
    """테스트 명령을 argv 리스트로. 실패 요약(-rfE)은 기본 명령에 이미 들어 있다."""
    return shlex.split(os.environ.get("TDD_TEST_CMD") or DEFAULT_TEST_CMD)


def runner_timeout():
    try:
        return int(os.environ.get("TDD_TEST_TIMEOUT", DEFAULT_TIMEOUT))
    except ValueError:
        return DEFAULT_TIMEOUT


def guard_disabled():
    return os.environ.get("TDD_GUARD", "").lower() in OFF_VALUES


def resolve(raw_path):
    """훅 페이로드의 file_path 를 프로젝트 기준 절대 경로로 정규화한다."""
    target = Path(raw_path)
    if not target.is_absolute():
        target = PROJECT_ROOT / target
    return target.resolve()


def relative(target):
    """보고용 경로. 프로젝트 밖이면 절대경로 그대로 쓴다."""
    try:
        return target.relative_to(PROJECT_ROOT)
    except ValueError:
        return target


def write_state(returncode, red, failing, trigger):
    payload = {
        "returncode": returncode,
        "red": red,
        "failing": failing,
        "trigger": str(trigger),
    }
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass  # 상태 기록 실패가 편집을 막아서는 안 된다


def read_state():
    """{'returncode': int, 'red': bool, 'failing': [nodeid], 'trigger': str} 또는 None."""
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def is_red(state):
    """Red 판정. 예전 형식(red 키 없음)도 failing 목록으로 읽어준다."""
    if state is None:
        return False
    if "red" in state:
        return bool(state["red"])
    return bool(state.get("failing"))
