import pytest
from addition import additionner

def test_additionner():
    assert additionner(2, 3) == 5
    assert additionner(-1, 1) == 0
    assert additionner(0, 0) == 0
    assert additionner(-5, -5) == -10
    assert additionner(100, 200) == 300
