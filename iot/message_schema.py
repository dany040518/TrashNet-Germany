"""Build and validate version 1.0 smart-bin classification messages."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from typing import Dict, Optional, Union


SCHEMA_VERSION = "1.0"
MAX_PAYLOAD_BYTES = 400
MAX_ACTION_TIP_LENGTH = 24


@dataclass(frozen=True)
class StreamConfig:
    led_color: str
    led_pattern: str
    label_de: str
    label_en: str
    default_tip: Dict[str, str]


STREAM_CONFIG: Dict[str, StreamConfig] = {
    "GELBER_SACK": StreamConfig(
        led_color="#FFD700",
        led_pattern="SOLID",
        label_de="Gelber Sack",
        label_en="Yellow packaging",
        default_tip={
            "de": "Aludeckel entfernen.",
            "en": "Remove aluminum lids.",
        },
    ),
    "PAPIER": StreamConfig(
        led_color="#0055A4",
        led_pattern="SOLID",
        label_de="Papier",
        label_en="Paper & cardboard",
        default_tip={
            "de": "Sauber und trocken.",
            "en": "Keep clean and dry.",
        },
    ),
    "RESTMUELL": StreamConfig(
        led_color="#333333",
        led_pattern="SOLID",
        label_de="Restmüll",
        label_en="Residual waste",
        default_tip={
            "de": "Nicht recycelbar?",
            "en": "Non-recyclable waste.",
        },
    ),
    "BIOABFALL": StreamConfig(
        led_color="#8B4513",
        led_pattern="SOLID",
        label_de="Bioabfall",
        label_en="Organic waste",
        default_tip={
            "de": "Verpackung entfernen.",
            "en": "Remove packaging.",
        },
    ),
    "ALTGLAS": StreamConfig(
        led_color="#2E8B57",
        led_pattern="SOLID",
        label_de="Altglas",
        label_en="Glass recycling",
        default_tip={
            "de": "Farbtrennung prüfen.",
            "en": "Check glass color.",
        },
    ),
    "UNSURE": StreamConfig(
        led_color="#FFBF00",
        led_pattern="BLINK_SLOW",
        label_de="Unsicher",
        label_en="Unsure",
        default_tip={
            "de": "Bitte Hilfe fragen.",
            "en": "Please ask for help.",
        },
    ),
}

_CLASSIFICATION_CLASSES = frozenset(STREAM_CONFIG)
_BIN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
)
_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_MESSAGE_FIELDS = {
    "schema_version",
    "bin_id",
    "timestamp",
    "class",
    "confidence",
    "status",
    "led_color",
    "led_pattern",
    "ui_payload",
}


def _validate_confidence(value: object, field_name: str = "confidence") -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number from 0.0 to 1.0")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be from 0.0 to 1.0 inclusive")


def _validate_tip(tip: object, field_name: str) -> Dict[str, str]:
    if isinstance(tip, str):
        result = {"en": tip}
    elif isinstance(tip, dict) and set(tip) == {"de", "en"}:
        result = dict(tip)
    else:
        raise ValueError(
            f"{field_name} must be a string or an object with exactly 'de' and 'en'"
        )

    for language, text in result.items():
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{field_name}.{language} must be a non-empty string")
        if len(text) > MAX_ACTION_TIP_LENGTH:
            raise ValueError(
                f"{field_name}.{language} must be at most "
                f"{MAX_ACTION_TIP_LENGTH} characters"
            )
    return result


def build_classification_message(
    predicted_class: str,
    confidence: float,
    bin_id: str,
    threshold: float = 0.70,
    latency_ms: Optional[int] = None,
    custom_tip: Optional[Union[str, Dict[str, str]]] = None,
) -> dict:
    """Build a compact MQTT classification payload, routing low confidence to UNSURE."""
    if not isinstance(predicted_class, str) or predicted_class not in _CLASSIFICATION_CLASSES:
        raise ValueError(
            f"predicted_class must be one of {sorted(_CLASSIFICATION_CLASSES)}"
        )
    _validate_confidence(confidence)
    _validate_confidence(threshold, "threshold")
    if not isinstance(bin_id, str) or not _BIN_ID_RE.fullmatch(bin_id):
        raise ValueError("bin_id must be 1-32 ASCII letters, digits, '_' or '-'")
    if latency_ms is not None and (
        isinstance(latency_ms, bool)
        or not isinstance(latency_ms, int)
        or not 0 <= latency_ms <= 60000
    ):
        raise ValueError("latency_ms must be an integer from 0 to 60000 or None")

    selected_class = predicted_class
    if predicted_class != "UNSURE" and confidence < threshold:
        selected_class = "UNSURE"

    config = STREAM_CONFIG[selected_class]
    action_tip = dict(config.default_tip)
    if custom_tip is not None:
        replacement = _validate_tip(custom_tip, "custom_tip")
        if isinstance(custom_tip, str):
            action_tip["en"] = replacement["en"]
        else:
            action_tip = replacement

    message = {
        "schema_version": SCHEMA_VERSION,
        "bin_id": bin_id,
        "timestamp": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "class": selected_class,
        "confidence": float(confidence),
        "status": "UNSURE" if selected_class == "UNSURE" else "RESULT",
        "led_color": config.led_color,
        "led_pattern": config.led_pattern,
        "ui_payload": {
            "label_de": config.label_de,
            "label_en": config.label_en,
            "action_tip": action_tip,
        },
    }
    if latency_ms is not None:
        message["latency_ms"] = latency_ms

    validate_classification_message(message)
    return message


def validate_classification_message(payload: dict) -> bool:
    """Validate a version 1.0 classification payload or raise ValueError."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dictionary")

    if any(not isinstance(key, str) for key in payload):
        raise ValueError("payload field names must be strings")
    keys = set(payload)
    missing = _MESSAGE_FIELDS - keys
    if missing:
        raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
    extra = keys - _MESSAGE_FIELDS - {"latency_ms"}
    if extra:
        raise ValueError(f"unexpected fields: {', '.join(sorted(extra))}")

    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION!r}")

    bin_id = payload["bin_id"]
    if not isinstance(bin_id, str) or not _BIN_ID_RE.fullmatch(bin_id):
        raise ValueError("bin_id must be 1-32 ASCII letters, digits, '_' or '-'")

    timestamp = payload["timestamp"]
    if not isinstance(timestamp, str) or not _TIMESTAMP_RE.fullmatch(timestamp):
        raise ValueError("timestamp must be a UTC ISO-8601 date-time with milliseconds")
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("timestamp must be a valid UTC date-time") from exc
    if parsed_timestamp.utcoffset() != timezone.utc.utcoffset(parsed_timestamp):
        raise ValueError("timestamp must use UTC")

    selected_class = payload["class"]
    if not isinstance(selected_class, str) or selected_class not in _CLASSIFICATION_CLASSES:
        raise ValueError(f"class must be one of {sorted(_CLASSIFICATION_CLASSES)}")

    _validate_confidence(payload["confidence"])
    expected_status = "UNSURE" if selected_class == "UNSURE" else "RESULT"
    if payload["status"] != expected_status:
        raise ValueError(
            f"status must be {expected_status!r} for class {selected_class!r}"
        )

    config = STREAM_CONFIG[selected_class]
    led_color = payload["led_color"]
    if not isinstance(led_color, str) or not _COLOR_RE.fullmatch(led_color):
        raise ValueError("led_color must match hexadecimal format #RRGGBB")
    if led_color != config.led_color:
        raise ValueError(
            f"led_color must be {config.led_color} for class {selected_class}"
        )
    led_pattern = payload["led_pattern"]
    if not isinstance(led_pattern, str) or led_pattern not in {
        "SOLID",
        "BLINK_SLOW",
    }:
        raise ValueError("led_pattern must be 'SOLID' or 'BLINK_SLOW'")
    if led_pattern != config.led_pattern:
        raise ValueError(
            f"led_pattern must be {config.led_pattern} for class {selected_class}"
        )

    ui_payload = payload["ui_payload"]
    if not isinstance(ui_payload, dict):
        raise ValueError("ui_payload must be an object")
    if set(ui_payload) != {"label_de", "label_en", "action_tip"}:
        raise ValueError(
            "ui_payload must contain exactly label_de, label_en, and action_tip"
        )
    expected_labels = {
        "label_de": config.label_de,
        "label_en": config.label_en,
    }
    for field_name, expected in expected_labels.items():
        value = ui_payload[field_name]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"ui_payload.{field_name} must be a non-empty string")
        if value != expected:
            raise ValueError(
                f"ui_payload.{field_name} must be {expected!r} for class {selected_class}"
            )
        limit = 24 if field_name == "label_de" else 32
        if len(value) > limit:
            raise ValueError(f"ui_payload.{field_name} must be at most {limit} characters")

    action_tip = ui_payload["action_tip"]
    if not isinstance(action_tip, dict) or set(action_tip) != {"de", "en"}:
        raise ValueError("ui_payload.action_tip must contain exactly 'de' and 'en'")
    for language in ("de", "en"):
        tip = action_tip[language]
        if not isinstance(tip, str) or not tip.strip():
            raise ValueError(f"ui_payload.action_tip.{language} must be non-empty")
        if len(tip) > MAX_ACTION_TIP_LENGTH:
            raise ValueError(
                f"ui_payload.action_tip.{language} must be at most "
                f"{MAX_ACTION_TIP_LENGTH} characters"
            )

    if "latency_ms" in payload:
        latency_ms = payload["latency_ms"]
        if (
            isinstance(latency_ms, bool)
            or not isinstance(latency_ms, int)
            or not 0 <= latency_ms <= 60000
        ):
            raise ValueError("latency_ms must be an integer from 0 to 60000")

    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    if len(encoded) >= MAX_PAYLOAD_BYTES:
        raise ValueError(
            f"compact UTF-8 payload must be less than {MAX_PAYLOAD_BYTES} bytes "
            f"(got {len(encoded)})"
        )
    return True


if __name__ == "__main__":
    high_confidence = build_classification_message(
        "GELBER_SACK", 0.94, "bin-01", latency_ms=143
    )
    assert validate_classification_message(high_confidence)
    assert high_confidence["class"] == "GELBER_SACK"
    assert high_confidence["led_pattern"] == "SOLID"

    low_confidence = build_classification_message(
        "PAPIER", 0.52, "bin-01", latency_ms=151
    )
    assert validate_classification_message(low_confidence)
    assert low_confidence["class"] == "UNSURE"
    assert low_confidence["led_pattern"] == "BLINK_SLOW"

    invalid_message = dict(high_confidence)
    invalid_message["confidence"] = 1.2
    try:
        validate_classification_message(invalid_message)
    except ValueError as exc:
        print(f"Expected validation error: {exc}")
    else:
        raise AssertionError("invalid confidence should have failed validation")

    print("High-confidence, UNSURE fallback, and validation-failure checks passed.")
