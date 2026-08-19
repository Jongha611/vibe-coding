from vibe_coding import Gugudan


# Gugudan Tests
def test_line():
    """한 줄 곱셈 문자열 테스트"""
    gugudan = Gugudan()

    assert gugudan.line(3, 4) == "3 x 4 = 12"

def test_table():
    """한 단 전체를 만드는 테스트"""
    gugudan = Gugudan()

    table = gugudan.table(2)

    assert len(table) == 9
    assert table[0] == "2 x 1 = 2"
    assert table[8] == "2 x 9 = 18"

def test_tables():
    """시작 단부터 끝 단까지 여러 단을 만드는 테스트"""
    gugudan = Gugudan()

    tables = gugudan.tables(2, 4)

    assert len(tables) == 3
    assert tables[0][0] == "2 x 1 = 2"
    assert tables[2][8] == "4 x 9 = 36"

def test_tables_single_dan():
    """시작 단과 끝 단이 같으면 한 단만 만드는 테스트"""
    gugudan = Gugudan()

    tables = gugudan.tables(7, 7)

    assert len(tables) == 1
    assert tables[0][0] == "7 x 1 = 7"

def test_run_prints_tables(monkeypatch, capsys):
    """터미널에서 숫자 두 개를 입력받아 구구단을 출력하는 테스트"""
    gugudan = Gugudan()
    answers = iter(["2", "3"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    gugudan.run()

    out = capsys.readouterr().out
    assert "2 x 1 = 2" in out
    assert "3 x 9 = 27" in out
