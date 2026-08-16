"""
Telemetry Validation and Anomaly Detection Module.
Enforces strict physical and integrity constraints on incoming battery measurements.
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from app.config import settings


class ValidationError(Exception):
    """Custom exception raised when telemetry validation fails."""
    def __init__(self, message: str, field: Optional[str] = None, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.message = message
        self.field = field
        self.error_code = error_code


class ConflictError(Exception):
    """Raised when an observation ID is reused with conflicting payload."""
    def __init__(self, message: str, observation_id: str):
        super().__init__(message)
        self.message = message
        self.observation_id = observation_id
        self.error_code = "IDENTIFIER_COLLISION"


def _is_finite_number(val: Any) -> bool:
    """Checks if a value is a valid, finite number (not NaN, not Inf)."""
    if val is None:
        return True  # Optional fields handled separately
    if not isinstance(val, (int, float)):
        return False
    return not (math.isnan(val) or math.isinf(val))


def validate_telemetry_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates an incoming telemetry observation payload against physical and schema rules.
    Returns (is_valid, error_message).
    Raises ValidationError if invalid.
    """
    # 1. Required fields
    required_fields = ["observation_id", "cycle_number", "soh"]
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValidationError(f"Missing required field: '{field}'", field=field, error_code="MISSING_FIELD")

    # 2. Cycle number validation
    cycle = data["cycle_number"]
    if not isinstance(cycle, int) or cycle <= 0:
        raise ValidationError(
            f"Invalid cycle_number '{cycle}'. Must be a positive integer > 0.",
            field="cycle_number",
            error_code="INVALID_CYCLE_NUMBER"
        )

    # 3. Non-finite numeric checks
    numeric_fields = ["voltage", "current", "temperature", "capacity", "soh"]
    for field in numeric_fields:
        if field in data and data[field] is not None:
            val = data[field]
            if not _is_finite_number(val):
                raise ValidationError(
                    f"Non-finite numeric value detected for '{field}': {val}",
                    field=field,
                    error_code="NON_FINITE_NUMERIC"
                )

    # 4. SOH range check
    soh = data["soh"]
    if soh < settings.SOH_MIN or soh > settings.SOH_MAX:
        raise ValidationError(
            f"SOH value {soh:.4f} is outside the valid configured range [{settings.SOH_MIN}, {settings.SOH_MAX}].",
            field="soh",
            error_code="SOH_OUT_OF_RANGE"
        )

    # 5. Timestamp validation
    if "recorded_at" in data and data["recorded_at"] is not None:
        recorded_at = data["recorded_at"]
        if isinstance(recorded_at, str):
            try:
                # Handle ISO 8601 strings
                dt = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
            except ValueError:
                raise ValidationError(
                    f"Malformed timestamp for 'recorded_at': '{recorded_at}'",
                    field="recorded_at",
                    error_code="INVALID_TIMESTAMP_FORMAT"
                )
        elif isinstance(recorded_at, datetime):
            dt = recorded_at
        else:
            raise ValidationError("Invalid type for 'recorded_at'. Expected ISO string or datetime.", field="recorded_at")

        # Future timestamp check (allow 5 minute clock drift tolerance)
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if (dt - now).total_seconds() > 300:
            raise ValidationError(
                f"Impossible future timestamp 'recorded_at': {dt.isoformat()}",
                field="recorded_at",
                error_code="IMPOSSIBLE_FUTURE_TIMESTAMP"
            )

    # 6. Physical sensor range checks (if present)
    if "voltage" in data and data["voltage"] is not None:
        v = data["voltage"]
        if v < settings.VOLTAGE_MIN or v > settings.VOLTAGE_MAX:
            raise ValidationError(
                f"Voltage {v}V is outside physical limits [{settings.VOLTAGE_MIN}, {settings.VOLTAGE_MAX}]V.",
                field="voltage",
                error_code="VOLTAGE_OUT_OF_RANGE"
            )

    if "temperature" in data and data["temperature"] is not None:
        temp = data["temperature"]
        if temp < settings.TEMPERATURE_MIN or temp > settings.TEMPERATURE_MAX:
            raise ValidationError(
                f"Temperature {temp}°C is outside physical limits [{settings.TEMPERATURE_MIN}, {settings.TEMPERATURE_MAX}]°C.",
                field="temperature",
                error_code="TEMPERATURE_OUT_OF_RANGE"
            )

    return True, None


def check_payload_equivalence(existing_obs: Dict[str, Any], new_obs: Dict[str, Any]) -> bool:
    """
    Checks if two payloads for the same observation ID have identical measurement content.
    Used to distinguish idempotent duplicate submissions from conflicting collisions.
    """
    keys = ["cycle_number", "soh", "voltage", "current", "temperature", "capacity"]
    for k in keys:
        v1 = existing_obs.get(k)
        v2 = new_obs.get(k)
        if v1 is None and v2 is None:
            continue
        if v1 is None or v2 is None:
            return False
        if isinstance(v1, float) or isinstance(v2, float):
            if not math.isclose(float(v1), float(v2), rel_tol=1e-5, abs_tol=1e-5):
                return False
        else:
            if v1 != v2:
                return False
    return True
