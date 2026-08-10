from vibe_coding import Calculator
import pytest


################### #
# Calculator Tests 
################### #
def test_add():
    """더하기 테스트"""
    calc = Calculator()

    assert calc.add(2, 3) == 5
    calc = Calculator()

    assert calc.multiply(4, 3) == 12

def test_divide():
    """나누기 테스트"""
    calc = Calculator()

    assert calc.divide(10, 2) == 5

def test_divide_by_zero():
    """0으로 나누기 테스트"""
    calc = Calculator()

    with pytest.raises(ZeroDivisionError):
        calc.divide(10, 0)
