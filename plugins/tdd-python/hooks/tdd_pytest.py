#!/usr/bin/env python3
"""PostToolUse 훅: 소스나 테스트 변경 후 테스트를 돌리고 결과를 기록한다.

실패를 어떻게 다룰지는 무엇을 고쳤느냐에 달렸다.

  테스트 변경 -> 실패는 정상이다(Red). 차단하지 않고 Red 확정만 알린다.
  소스  변경 -> 실패는 구현이 틀렸다는 뜻이다. decision=block 으로 되돌린다.

어느 쪽이든 결과를 <프로젝트>/.claude/.tdd-state.json 에 남겨 tdd_guard.py 가
"지금 Red 인가"를 판단할 수 있게 한다.

TDD_GUARD=off 환경변수로 우회할 수 있다.
"""

import json
import os
import re
import shutil
import subprocess
import sys

from tdd_state import (
    PROJECT_ROOT,
    SRC_DIR,
    TESTS_DIR,
    guard_disabled,
    relative,
    resolve,
    runner_command,
    runner_timeout,
    write_state,
)

# pytest 종료 코드 5 = 수집된 테스트 없음
NO_TESTS_COLLECTED = 5

MAX_OUTPUT_CHARS = 4000

# 훅은 로그인 셸을 안 타는 경우가 있어 흔한 설치 위치를 PATH 에 얹는다
EXTRA_PATHS = ("/opt/homebrew/bin", "/usr/local/bin", "~/.local/bin")

FAILURE_LINE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)", re.MULTILINE)


def quiet():
    """조용히 종료한다. 훅이 아무 말도 하지 않는다."""
    sys.exit(0)


def block(reason):
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    sys.exit(0)


def notify(message, context):
    """차단하지 않고 사용자에게 알리고 모델에 맥락을 넣는다."""
    print(
        json.dumps(
            {
                "systemMessage": message,
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": context,
                },
            },
            ensure_ascii=False,
        )
    )
    sys.exit(0)


def augmented_env():
    env = os.environ.copy()
    parts = [p for p in env.get("PATH", "").split(os.pathsep) if p]
    for extra in EXTRA_PATHS:
        expanded = os.path.expanduser(extra)
        if expanded not in parts:
            parts.append(expanded)
    env["PATH"] = os.pathsep.join(parts)
    return env


def classify(target):
    """편집 대상이 테스트인지 소스인지. 감시 대상이 아니면 None."""
    if target.suffix != ".py":
        return None
    if target.is_relative_to(TESTS_DIR):
        return "tests"
    if target.is_relative_to(SRC_DIR):
        return "src"
    return None


def truncate(output):
    output = output.strip()
    if len(output) > MAX_OUTPUT_CHARS:
        return "…(생략)\n" + output[-MAX_OUTPUT_CHARS:]
    return output


def main():
    if guard_disabled():
        quiet()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        quiet()

    raw_path = (payload.get("tool_response") or {}).get("filePath") or (
        payload.get("tool_input") or {}
    ).get("file_path")
    if not raw_path:
        quiet()

    target = resolve(raw_path)
    origin = classify(target)
    if origin is None:
        quiet()

    argv = runner_command()
    if not argv:
        block("TDD: TDD_TEST_CMD 가 비어 있어 테스트를 실행하지 못했다.")

    env = augmented_env()
    executable = shutil.which(argv[0], path=env["PATH"])
    if executable is None:
        block(
            f"TDD: 테스트 명령 '{argv[0]}' 을 PATH 에서 찾을 수 없다. "
            f"설치 상태를 확인하거나 TDD_TEST_CMD 로 다른 명령을 지정하라."
        )

    timeout = runner_timeout()
    try:
        result = subprocess.run(
            [executable, *argv[1:]],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        block(f"TDD: 테스트가 {timeout}초 안에 끝나지 않았다. 무한 루프를 의심하라.")

    output = result.stdout + result.stderr
    failing = FAILURE_LINE.findall(output)
    rel = relative(target)
    green = result.returncode in (0, NO_TESTS_COLLECTED)

    write_state(result.returncode, not green, failing, rel)

    if green:
        if origin == "tests":
            notify(
                f"TDD: {rel} 저장 후 테스트 전부 통과 — Red 가 아니다.",
                f"테스트가 전부 통과했다. 방금 쓴 테스트가 실패하지 않았으므로 "
                f"아직 구현할 것이 없거나, 테스트가 새 동작을 검증하지 못하고 있다. "
                f"새 기능을 만드는 중이라면 실패하는 테스트를 먼저 만들어라.",
            )
        quiet()

    if origin == "tests":
        label = f"{len(failing)}개 실패" if failing else "실패 확인"
        notify(
            f"TDD: Red 확인 — {label}. 이제 구현하면 된다.",
            f"의도한 Red 상태다. 실패 중인 테스트: "
            f"{', '.join(failing) or '(목록 파싱 불가 — 종료 코드로 판정했다)'}\n"
            f"이제 소스를 구현해 통과시켜라. 테스트를 통과시키려고 "
            f"테스트 자체를 약화시키지 마라.",
        )

    block(
        f"TDD: `{' '.join(argv)}` 가 실패했다 "
        f"(exit {result.returncode}). Green 이 될 때까지 고쳐라.\n\n{truncate(output)}"
    )


if __name__ == "__main__":
    main()
