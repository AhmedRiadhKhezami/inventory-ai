from src.metrics import wape, biais


def test_wape_exemple():
    assert round(wape([10, 0, 5, 5], [8, 1, 5, 7]), 2) == 0.25


def test_biais_exemple():
    assert round(biais([10, 0, 5, 5], [8, 1, 5, 7]), 2) == 0.05


def test_prevision_parfaite():
    assert wape([3, 0, 2], [3, 0, 2]) == 0
    assert biais([3, 0, 2], [3, 0, 2]) == 0