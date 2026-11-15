"""Validation rules for confidence-based classification fallbacks."""

from typing import Any

from iot.message_schema import validate_classification_message


DEFAULT_CONFIDENCE_THRESHOLD = 0.70


def validate_fallback_policy(
    payload: dict, threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> bool:
    """Validate the message schema and require low-confidence results to be UNSURE.

    An UNSURE result is also valid above the confidence threshold when the
    classifier's top-two class margin is ambiguous.
    """
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be a finite number from 0.0 to 1.0")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be from 0.0 to 1.0 inclusive")

    validate_classification_message(payload)
    if payload["class"] != "UNSURE" and payload["confidence"] < threshold:
        raise ValueError(
            "class must be 'UNSURE' when confidence is below "
            f"the {threshold:.2f} fallback threshold"
        )
    return True
