"""
Unit tests for Telemetry Validation and Anomaly Rejection.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.core.validation import (
    validate_telemetry_payload,
    check_payload_equivalence,
    ValidationError
)


def test_valid_telemetry_payload():
    valid_payload = {
        "observation_id": "OBS-001",
        "cycle_number": 1,
        "soh": 0.995,
        "voltage": 3.75,
        "current": 1.5,
        "temperature": 25.0,
        "capacity": 1.99,
        "recorded_at": "2026-08-15T10:00:00Z"
    }
    is_valid, msg = validate_telemetry_payload(valid_payload)
    assert is_valid is True
    assert msg is None


def test_missing_required_fields():
    # Missing cycle_number
    with pytest.raises(ValidationError) as exc:
        validate_telemetry_payload({"observation_id": "OBS-001", "soh": 0.99})
    assert exc.value.error_code == "MISSING_FIELD"

    # Missing soh
    with pytest.raises(ValidationError) as exc:
        validate_telemetry_payload({"observation_id": "OBS-001", "cycle_number": 5})
    assert exc.value.error_code == "MISSING_FIELD"


def test_invalid_cycle_number():
    with pytest.raises(ValidationError) as exc:
        validate_telemetry_payload({"observation_id": "OBS-001", "cycle_number": 0, "soh": 0.99})
    assert exc.value.error_code == "INVALID_CYCLE_NUMBER"

    with pytest.raises(ValidationError) as exc:
        validate_telemetry_payload({"observation_id": "OBS-001", "cycle_number": -5, "soh": 0.99})
    assert exc.value.error_code == "INVALID_CYCLE_NUMBER"


def test_non_finite_numeric_values():
    import math
    with pytest.raises(ValidationError) as exc:
        validate_telemetry_payload({"observation_id": "OBS-001", "cycle_number": 1, "soh": float("nan")})
    assert exc.value.error_code == "NON_FINITE_NUMERIC"

    with pytest.raises(ValidationError) as exc:
        validate_telemetry_payload({"observation_id": "OBS-001", "cycle_number": 1, "soh": float("inf")})
    assert exc.value.error_code == "NON_FINITE_NUMERIC"


def test_soh_out_of_range():
    # SOH below 0.0
    with pytest.raises(ValidationError) as exc:
        validate_telemetry_payload({"observation_id": "OBS-001", "cycle_number": 1, "soh": -0.1})
    assert exc.value.error_code == "SOH_OUT_OF_RANGE"

    # SOH above 1.2
    with pytest.raises(ValidationError) as exc:
        validate_telemetry_payload({"observation_id": "OBS-001", "cycle_number": 1, "soh": 1.45})
    assert exc.value.error_code == "SOH_OUT_OF_RANGE"


def test_impossible_future_timestamp():
    future_time = datetime.now(timezone.utc) + timedelta(days=2)
    with pytest.raises(ValidationError) as exc:
        validate_telemetry_payload({
            "observation_id": "OBS-001",
            "cycle_number": 1,
            "soh": 0.99,
            "recorded_at": future_time.isoformat()
        })
    assert exc.value.error_code == "IMPOSSIBLE_FUTURE_TIMESTAMP"


def test_payload_equivalence():
    p1 = {"cycle_number": 10, "soh": 0.95, "voltage": 3.70}
    p2 = {"cycle_number": 10, "soh": 0.95, "voltage": 3.700001}
    assert check_payload_equivalence(p1, p2) is True

    p3 = {"cycle_number": 10, "soh": 0.85, "voltage": 3.70}
    assert check_payload_equivalence(p1, p3) is False
