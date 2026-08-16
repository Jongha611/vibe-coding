#!/usr/bin/env python3
"""PreToolUse 훅: src 수정이 TDD 순서를 지키는지 검사한다.

src/vibe_coding/**/<name>.py 를 Write/Edit 할 때 세 단계로 본다.

  1. tests/ 에 test_<name>*.py 가 존재하는가
  2. 이번 편집이 새 public API 를 추가하는가 (AST diff)
     → 추가한다면 그 이름이 tests/ 에 이미 언급돼 있는가
  3. → 추가한다면 지금 실패 중인 테스트가 있는가 (Red)

새 API 를 추가하지 않는 편집(리팩토링·버그 수정)은 1번만 통과하면 된다.
TDD_GUARD=off 환경변수로 전체를 우회할 수 있다.
"""

import ast
import json
import re
import sys

from tdd_state import (
    PROJECT_ROOT,
    SRC_PKG,
    TESTS_DIR,
    guard_disabled,
    read_state,
    resolve,
)

# 재노출·설정용 파일은 테스트를 요구하지 않는다
EXEMPT_NAMES = {"__init__.py", "__main__.py", "conftest.py"}


def allow():
    """훅이 개입하지 않는다. 평소 권한 흐름을 그대로 탄다."""
    sys.exit(0)


def deny(reason):
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )
    sys.exit(0)


def needs_check(target):
    if target.suffix != ".py" or target.name in EXEMPT_NAMES:
        return False
    return target.is_relative_to(SRC_PKG)


def find_tests(stem):
    if not TESTS_DIR.is_dir():
        return []
    return sorted(TESTS_DIR.rglob(f"test_{stem}*.py"))


def prospective_content(tool_input, target):
    """편집 후의 파일 내용을 재구성한다. 판단 불가면 None."""
    if "content" in tool_input:  # Write
        return tool_input["content"]

    old = tool_input.get("old_string")
    new = tool_input.get("new_string")
    if old is None or new is None:
        return None

    try:
        current = target.read_text(encoding="utf-8")
    except OSError:
        return None

    if old not in current:
        return None
    if tool_input.get("replace_all"):
        return current.replace(old, new)
    return current.replace(old, new, 1)


def public_names(source):
    """모듈의 public 이름 집합. 구문 오류면 None."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None

    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            names.add(node.name)
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not sub.name.startswith("_"):
                        names.add(f"{node.name}.{sub.name}")
    return names


def unmentioned_in_tests(names):
    """tests/ 어디에도 등장하지 않는 이름들을 돌려준다."""
    if not TESTS_DIR.is_dir():
        return sorted(names)

    corpus = []
    for path in TESTS_DIR.rglob("*.py"):
        try:
            corpus.append(path.read_text(encoding="utf-8"))
        except OSError:
            continue
    blob = "\n".join(corpus)

    missing = []
    for name in sorted(names):
        bare = name.split(".")[-1]
        if not re.search(rf"\b{re.escape(bare)}\b", blob):
            missing.append(name)
    return missing


def main():
    if guard_disabled():
        allow()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        allow()

    tool_input = payload.get("tool_input") or {}
    raw_path = tool_input.get("file_path")
    if not raw_path:
        allow()

    target = resolve(raw_path)
    if not needs_check(target):
        allow()

    stem = target.stem

    # 1. 테스트 파일 존재
    if not find_tests(stem):
        deny(
            f"TDD 위반: {target.relative_to(PROJECT_ROOT)} 에 대응하는 테스트가 없다.\n"
            f"tests/test_{stem}.py 를 먼저 작성해 실패하는 테스트(Red)를 만든 뒤 "
            f"이 파일을 수정하라. write-unit-tests 스킬을 쓰면 된다.\n"
            f"탐색한 패턴: tests/**/test_{stem}*.py\n"
            f"의도적으로 건너뛰려면 TDD_GUARD=off 로 실행한다."
        )

    # 2. 새 public API 감지
    after = prospective_content(tool_input, target)
    if after is None:
        allow()  # 편집 결과를 재구성할 수 없으면 판단하지 않는다

    new_api = public_names(after)
    if new_api is None:
        allow()  # 편집 후 코드가 파싱되지 않으면 AST 판단을 포기한다

    try:
        before_api = public_names(target.read_text(encoding="utf-8")) or set()
    except OSError:
        before_api = set()  # 새 파일

    added = new_api - before_api
    if not added:
        allow()  # 리팩토링·버그 수정: 1번만 통과하면 된다

    added_label = ", ".join(sorted(added))

    missing = unmentioned_in_tests(added)
    if missing:
        deny(
            f"TDD 위반: 새 public API {', '.join(missing)} 가 tests/ 어디에도 없다.\n"
            f"이 동작을 검증하는 테스트를 tests/test_{stem}.py 에 먼저 추가해 "
            f"실패시킨 뒤 구현하라. write-unit-tests 스킬을 쓰면 된다.\n"
            f"이번 편집이 추가하는 이름: {added_label}\n"
            f"의도적으로 건너뛰려면 TDD_GUARD=off 로 실행한다."
        )

    # 3. Red 확인
    state = read_state()
    if state is None:
        deny(
            f"TDD 위반: pytest 실행 기록이 없어 Red 를 확인할 수 없다 ({added_label} 추가).\n"
            f"tests/test_{stem}.py 를 저장하면 PostToolUse 훅이 pytest 를 돌려 "
            f"상태를 기록한다. 그 뒤 다시 시도하라.\n"
            f"의도적으로 건너뛰려면 TDD_GUARD=off 로 실행한다."
        )

    if not state.get("failing"):
        deny(
            f"TDD 위반: {added_label} 를 추가하려는데 실패 중인 테스트가 없다 "
            f"(직전 pytest 통과).\n"
            f"이 동작을 검증하는 테스트를 먼저 추가해 Red 를 만든 뒤 구현하라.\n"
            f"의도적으로 건너뛰려면 TDD_GUARD=off 로 실행한다."
        )

    allow()


if __name__ == "__main__":
    main()
