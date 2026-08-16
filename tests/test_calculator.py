from vibe_coding import Calculator
import pytest


# Calculator Tests 
def test_add():
    """더하기 테스트"""
    calc = Calculator()

    assert calc.add(2, 3) == 5

def test_subtract():
    """빼기 테스트"""
    calc = Calculator()

    assert calc.subtract(5, 3) == 2

def test_multiply():
    """곱하기 테스트"""
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

def test_reuse_same_instance():
    """같은 인스턴스로 여러 연산을 연속 수행하는 테스트"""
    calc = Calculator()

    assert calc.add(1, 2) == 3
    assert calc.subtract(10, 4) == 6
    assert calc.multiply(3, 3) == 9
    assert calc.divide(20, 4) == 5
