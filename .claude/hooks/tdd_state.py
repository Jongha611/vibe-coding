"""
# TDD 훅 두 개가 공유하는 경로와 Red 상태 파일 입출력 모듈. #

tdd_pytest.py 가 pytest 를 돌린 뒤 상태를 쓰고, tdd_guard.py 가 그걸 읽어
"지금 실패 중인 테스트가 있는가"(Red)를 판단한다.
"""


import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
SRC_PKG = SRC_DIR / "vibe_coding"
TESTS_DIR = PROJECT_ROOT / "tests"
STATE_FILE = PROJECT_ROOT / ".claude" / ".tdd-state.json"

OFF_VALUES = {"off", "0", "false", "no"}


def guard_disabled():
    return os.environ.get("TDD_GUARD", "").lower() in OFF_VALUES


def resolve(raw_path):
    """훅 페이로드의 file_path 를 프로젝트 기준 절대 경로로 정규화한다."""
    target = Path(raw_path)
    if not target.is_absolute():
        target = PROJECT_ROOT / target
    return target.resolve()


def write_state(returncode, failing, trigger):
    payload = {
        "returncode": returncode,
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
    """{'returncode': int, 'failing': [nodeid], 'trigger': str} 또는 None."""
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
