"""Tests de la compuerta de contraste del entregable 3."""
import pytest
from scripts.check_contrast_b3 import contrast_ratio, check_palette


def test_w3c_reference_examples():
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0)


def test_text_contrast_failure_is_detectable():
    assert contrast_ratio("#898781", "#ffffff") < 4.5


def test_palette_v3_wcg_aa():
    assert check_palette() == []
