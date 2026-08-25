from vibe_coding import GitStats
import subprocess
from datetime import datetime


# GitStats Tests
def test_parse():
    """로그 한 줄을 해시·작성자·날짜로 나누는 테스트"""
    gitstats = GitStats()
    log = (
        "aaa111|Jongha611|2026-08-24T10:00:00+09:00\n"
        "bbb222|Somebody|2026-08-25T14:30:00+09:00"
    )

    commits = gitstats.parse(log)

    assert len(commits) == 2
    assert commits[0]["hash"] == "aaa111"
    assert commits[0]["author"] == "Jongha611"
    assert commits[1]["date"].year == 2026

def test_by_author():
    """작성자별 커밋 수를 많은 순으로 세는 테스트"""
    gitstats = GitStats()
    log = (
        "aaa111|Jongha611|2026-08-24T10:00:00+09:00\n"
        "bbb222|Jongha611|2026-08-25T14:30:00+09:00\n"
        "ccc333|Somebody|2026-08-26T09:15:00+09:00"
    )

    counts = gitstats.by_author(gitstats.parse(log))

    assert counts == {"Jongha611": 2, "Somebody": 1}
    assert list(counts)[0] == "Jongha611"

def test_by_weekday():
    """요일별 커밋 수를 월~일 순서로 세는 테스트"""
    gitstats = GitStats()
    log = (
        "aaa111|Jongha611|2026-08-24T10:00:00+09:00\n"
        "bbb222|Jongha611|2026-08-25T14:30:00+09:00\n"
        "ccc333|Somebody|2026-08-26T09:15:00+09:00"
    )

    counts = gitstats.by_weekday(gitstats.parse(log))

    assert counts == {"월": 1, "화": 1, "수": 1, "목": 0, "금": 0, "토": 0, "일": 0}
    assert list(counts) == ["월", "화", "수", "목", "금", "토", "일"]

def test_collect(monkeypatch):
    """git log 를 실행해 출력을 그대로 돌려주는 테스트"""
    gitstats = GitStats()
    commands = []

    class FakeResult:
        stdout = "aaa111|Jongha611|2026-08-24T10:00:00+09:00"

    def fake_run(command, **kwargs):
        commands.append(command)
        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)

    log = gitstats.collect()

    assert log == "aaa111|Jongha611|2026-08-24T10:00:00+09:00"
    assert commands[0][0] == "git"
    assert commands[0][1] == "log"

def test_run_prints_stats(monkeypatch, capsys):
    """수집한 로그로 작성자별·요일별 통계를 출력하는 테스트"""
    gitstats = GitStats()
    log = (
        "aaa111|Jongha611|2026-08-24T10:00:00+09:00\n"
        "bbb222|Jongha611|2026-08-25T14:30:00+09:00\n"
        "ccc333|Somebody|2026-08-26T09:15:00+09:00"
    )
    monkeypatch.setattr(GitStats, "collect", lambda self: log)

    gitstats.run()

    out = capsys.readouterr().out
    assert "Jongha611: 2" in out
    assert "월: 1" in out

def test_month_start():
    """주어진 시각에서 그 달 1일 0시를 구하는 테스트"""
    gitstats = GitStats()

    start = gitstats.month_start(datetime(2026, 8, 26, 14, 30, 5))

    assert start == datetime(2026, 8, 1, 0, 0, 0)

def test_collect_limits_to_this_month(monkeypatch):
    """이번 달 커밋만 가져오도록 --since 를 붙이는 테스트"""
    gitstats = GitStats()
    commands = []

    class FakeResult:
        stdout = ""

    def fake_run(command, **kwargs):
        commands.append(command)
        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(GitStats, "month_start", lambda self: datetime(2026, 8, 1))

    gitstats.collect()

    assert "--since=2026-08-01" in commands[0]

def test_run_prints_month_header(monkeypatch, capsys):
    """어느 달의 통계인지 머리글에 드러내는 테스트"""
    gitstats = GitStats()
    log = "aaa111|Jongha611|2026-08-24T10:00:00+09:00"
    monkeypatch.setattr(GitStats, "collect", lambda self: log)
    monkeypatch.setattr(GitStats, "month_start", lambda self: datetime(2026, 8, 1))

    gitstats.run()

    assert "2026년 8월" in capsys.readouterr().out
