from vibe_coding import GitStats
from datetime import datetime


# GitStats Edge Case Tests
def test_parse_empty_log():
    """커밋이 하나도 없어 로그가 빈 문자열일 때 테스트"""
    gitstats = GitStats()

    assert gitstats.parse("") == []

def test_parse_skips_broken_line():
    """구분자가 빠진 줄은 건너뛰고 정상 줄만 남기는 테스트"""
    gitstats = GitStats()
    log = (
        "형식이 깨진 줄\n"
        "aaa111|Jongha611|2026-08-24T10:00:00+09:00"
    )

    commits = gitstats.parse(log)

    assert len(commits) == 1
    assert commits[0]["hash"] == "aaa111"

def test_by_author_with_no_commits():
    """커밋이 없으면 작성자 집계가 빈 dict 인 테스트"""
    gitstats = GitStats()

    assert gitstats.by_author([]) == {}

def test_by_weekday_with_no_commits():
    """커밋이 없어도 요일 일곱 칸이 0으로 남는 테스트"""
    gitstats = GitStats()

    counts = gitstats.by_weekday([])

    assert counts == {"월": 0, "화": 0, "수": 0, "목": 0, "금": 0, "토": 0, "일": 0}

def test_run_without_commits(monkeypatch, capsys):
    """이번 달 커밋이 없으면 빈 집계 대신 안내만 출력하는 테스트"""
    gitstats = GitStats()
    monkeypatch.setattr(GitStats, "collect", lambda self: "")
    monkeypatch.setattr(GitStats, "month_start", lambda self: datetime(2026, 9, 1))

    gitstats.run()

    out = capsys.readouterr().out
    assert "2026년 9월" in out
    assert "아직 커밋이 없다" in out
    assert "요일별" not in out
