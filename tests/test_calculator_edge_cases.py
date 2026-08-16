from vibe_coding import Calculator
import pytest


# Calculator Edge Case Tests
def test_add_type_error_int_and_str():
    """정수와 문자열을 더하면 타입 에러가 발생하는 테스트"""
    calc = Calculator()

    with pytest.raises(TypeError):
        calc.add(1, "a")

def test_add_with_strings():
    """문자열을 더하면 연결로 동작하는 테스트"""
    calc = Calculator()

    assert calc.add("a", "b") == "ab"

def test_multiply_with_list():
    """리스트에 정수를 곱하면 반복으로 동작하는 테스트"""
    calc = Calculator()

    assert calc.multiply([1, 2], 3) == [1, 2, 1, 2, 1, 2]

def test_add_float_precision():
    """부동소수점 덧셈에서 오차가 발생하는 테스트"""
    calc = Calculator()

    assert calc.add(0.1, 0.2) != 0.3
    assert calc.add(0.1, 0.2) == pytest.approx(0.3)

def test_divide_returns_float_for_exact_division():
    """나누어 떨어지는 경우에도 나눗셈 결과가 float형인 테스트"""
    calc = Calculator()

    result = calc.divide(6, 3)

    assert result == 2.0
    assert isinstance(result, float)

def test_multiply_list_with_negative_count():
    """리스트에 음수를 곱하면 에러 없이 빈 리스트가 되는 테스트"""
    calc = Calculator()

    assert calc.multiply([1, 2], -1) == []

def test_subtract_type_error_int_and_str():
    """정수와 문자열을 빼면 타입 에러가 발생하는 테스트"""
    calc = Calculator()

    with pytest.raises(TypeError):
        calc.subtract(1, "a")

def test_subtract_with_sets():
    """집합을 빼면 차집합으로 동작하는 테스트"""
    calc = Calculator()

    assert calc.subtract({1, 2, 3}, {2, 3}) == {1}

def test_subtract_float_precision():
    """부동소수점 뺄셈에서 오차가 발생하는 테스트"""
    calc = Calculator()

    assert calc.subtract(0.3, 0.1) != 0.2
    assert calc.subtract(0.3, 0.1) == pytest.approx(0.2)
