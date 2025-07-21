import pytest
from addition import additionner

def test_additionner():
    assert additionner(3, 5) == 8  # Test avec des entiers
    assert additionner(-1, 1) == 0  # Test avec des entiers négatifs et positifs
    assert additionner(0, 0) == 0  # Test avec des zéros
    assert additionner(2.5, 0.5) == 3.0  # Test avec des flottants
    assert additionner(-2.5, -0.5) == -3.0  # Test avec des flottants négatifs