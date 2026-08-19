from vibe_coding import Gugudan
import pytest


# Gugudan Edge Case Tests
def test_table_below_min_dan():
    """1보다 작은 단을 요청하면 에러가 발생하는 테스트"""
    gugudan = Gugudan()

    with pytest.raises(ValueError):
        gugudan.table(0)

def test_table_above_max_dan():
    """9보다 큰 단을 요청하면 에러가 발생하는 테스트"""
    gugudan = Gugudan()

    with pytest.raises(ValueError):
        gugudan.table(10)

def test_tables_start_greater_than_end():
    """시작 단이 끝 단보다 크면 에러가 발생하는 테스트"""
    gugudan = Gugudan()

    with pytest.raises(ValueError):
        gugudan.tables(5, 3)

def test_run_with_non_numeric_input(monkeypatch, capsys):
    """숫자가 아닌 입력에도 예외 없이 오류 메시지만 출력하는 테스트"""
    gugudan = Gugudan()
    answers = iter(["둘", "3"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    gugudan.run()

    assert "입력 오류" in capsys.readouterr().out

def test_run_with_out_of_range_input(monkeypatch, capsys):
    """범위를 벗어난 단을 입력해도 예외 없이 오류 메시지만 출력하는 테스트"""
    gugudan = Gugudan()
    answers = iter(["0", "9"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    gugudan.run()

    assert "입력 오류" in capsys.readouterr().out
