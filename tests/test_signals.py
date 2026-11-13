"""
AlphaWatch AI — Quantitative Signal Generation Tests
ASTRAQUANT X 2026

Verifies:
  - PROFILES dictionary structure and default thresholds.
  - generate_signal behavior across Conservative, Moderate, and Aggressive profiles.
  - Exact threshold boundary conditions:
      * Exactly on buy threshold -> BUY
      * Exactly below buy threshold -> HOLD
      * Exactly above sell threshold -> HOLD
      * Exactly on sell threshold -> SELL
      * Extreme probabilities: 0.0 -> SELL, 1.0 -> BUY
  - Validation errors for out-of-range probabilities (<0 or >1) and unknown profiles.
  - Threshold configurability (loaded dynamically from config dict).
"""

import pytest
from src.signals import PROFILES, generate_signal


def test_profiles_configuration():
    """Verify default PROFILES thresholds per specification."""
    # Conservative: BUY 0.65 / SELL 0.35, max position 10%, stop-loss 3%
    assert PROFILES["Conservative"]["buy_threshold"] == 0.65
    assert PROFILES["Conservative"]["sell_threshold"] == 0.35
    assert PROFILES["Conservative"]["max_position_pct"] == 10.0
    assert PROFILES["Conservative"]["stop_loss_pct"] == 3.0

    # Moderate: BUY 0.60 / SELL 0.40, max position 20%, stop-loss 5%
    assert PROFILES["Moderate"]["buy_threshold"] == 0.60
    assert PROFILES["Moderate"]["sell_threshold"] == 0.40
    assert PROFILES["Moderate"]["max_position_pct"] == 20.0
    assert PROFILES["Moderate"]["stop_loss_pct"] == 5.0

    # Aggressive: BUY 0.55 / SELL 0.45, max position 30%, stop-loss 8%
    assert PROFILES["Aggressive"]["buy_threshold"] == 0.55
    assert PROFILES["Aggressive"]["sell_threshold"] == 0.45
    assert PROFILES["Aggressive"]["max_position_pct"] == 30.0
    assert PROFILES["Aggressive"]["stop_loss_pct"] == 8.0


def test_threshold_edge_cases():
    """
    Test exact threshold edge cases for all three profiles.

    Hand-calculated boundary logic:
    Moderate profile:
      buy_threshold = 0.60, sell_threshold = 0.40
      prob = 0.6000 -> BUY  (prob >= 0.60)
      prob = 0.5999 -> HOLD (0.40 < prob < 0.60)
      prob = 0.5000 -> HOLD (neutral)
      prob = 0.4001 -> HOLD (0.40 < prob < 0.60)
      prob = 0.4000 -> SELL (prob <= 0.40)
      prob = 1.0000 -> BUY  (upper bound)
      prob = 0.0000 -> SELL (lower bound)
    """
    # Moderate Profile
    assert generate_signal(0.60, "Moderate")["signal"] == "BUY"
    assert generate_signal(0.5999, "Moderate")["signal"] == "HOLD"
    assert generate_signal(0.50, "Moderate")["signal"] == "HOLD"
    assert generate_signal(0.4001, "Moderate")["signal"] == "HOLD"
    assert generate_signal(0.40, "Moderate")["signal"] == "SELL"
    assert generate_signal(1.0, "Moderate")["signal"] == "BUY"
    assert generate_signal(0.0, "Moderate")["signal"] == "SELL"

    # Conservative Profile (0.65 / 0.35)
    assert generate_signal(0.65, "Conservative")["signal"] == "BUY"
    assert generate_signal(0.6499, "Conservative")["signal"] == "HOLD"
    assert generate_signal(0.3501, "Conservative")["signal"] == "HOLD"
    assert generate_signal(0.35, "Conservative")["signal"] == "SELL"

    # Aggressive Profile (0.55 / 0.45)
    assert generate_signal(0.55, "Aggressive")["signal"] == "BUY"
    assert generate_signal(0.5499, "Aggressive")["signal"] == "HOLD"
    assert generate_signal(0.4501, "Aggressive")["signal"] == "HOLD"
    assert generate_signal(0.45, "Aggressive")["signal"] == "SELL"


def test_return_fields_and_types():
    """Verify returned dictionary structure, types, and model version."""
    res = generate_signal(0.72, "Moderate", model_version="2.1.0", as_of="2026-11-13")
    assert res["signal"] == "BUY"
    assert res["probability_up"] == 0.72
    assert res["profile"] == "Moderate"
    assert res["timestamp"] == "2026-11-13"
    assert res["model_version"] == "2.1.0"


def test_invalid_probability_raises():
    """Probabilities outside [0.0, 1.0] must raise ValueError."""
    with pytest.raises(ValueError, match="Probability must be between 0.0 and 1.0"):
        generate_signal(-0.01, "Moderate")

    with pytest.raises(ValueError, match="Probability must be between 0.0 and 1.0"):
        generate_signal(1.01, "Moderate")

    with pytest.raises(ValueError):
        generate_signal("0.5", "Moderate")  # non-numeric type rejected


def test_unknown_profile_raises():
    """Unknown profile names must raise ValueError."""
    with pytest.raises(ValueError, match="Unknown investor profile"):
        generate_signal(0.60, "UltraAggressive")


def test_configurable_thresholds():
    """Verify that changing PROFILES configuration dynamically changes signal outcomes."""
    orig_buy = PROFILES["Moderate"]["buy_threshold"]
    try:
        # Reconfigure buy threshold to 0.75
        PROFILES["Moderate"]["buy_threshold"] = 0.75
        # 0.70 would have been a BUY under 0.60, but is now a HOLD under 0.75
        assert generate_signal(0.70, "Moderate")["signal"] == "HOLD"
        assert generate_signal(0.75, "Moderate")["signal"] == "BUY"
    finally:
        PROFILES["Moderate"]["buy_threshold"] = orig_buy
