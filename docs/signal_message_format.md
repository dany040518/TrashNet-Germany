# Classification Signal Message Format

## 1. Overview and Transport Context

The classification signal is the versioned, compact application payload published by the edge inference service to the local MQTT topic `smartbin/{bin_id}/classification` at QoS 1, as selected in [ADR 001](adr_001_communication_protocol.md). The LED actuation adapter, bilingual kiosk, and telemetry/feedback consumers subscribe independently. QoS 1 is at-least-once, so consumers must tolerate duplicate deliveries.

The serialized UTF-8 JSON payload is limited to **less than 400 bytes** to keep local publish-to-subscriber delivery within the architecture's `< 20 ms` transport allocation. Producers must serialize compactly (no insignificant whitespace); the Python builder enforces the byte limit. `latency_ms`, when available, records elapsed edge processing time from capture start through classification-message publication; it is not the final LED/UI response latency.

The classification payload has a fixed schema version (`1.0`) and carries the German waste class, confidence, display text, and actuator instruction. Supported classes are `GELBER_SACK`, `PAPIER`, `RESTMUELL`, `BIOABFALL`, `ALTGLAS`, and `UNSURE`. A separate feedback event is published on `smartbin/{bin_id}/feedback`; it is not a classification message and is not validated by the classification JSON Schema in this document.

The Python builder's `custom_tip` may be a string (replacing the English tip while retaining the configured German tip) or an object containing both `de` and `en` strings.

## 2. Field Specification

All classification fields except `latency_ms` are required. Unknown fields are rejected in schema version 1.0.

| Field | Type | Required | Constraints / range | Description |
| --- | --- | --- | --- | --- |
| `schema_version` | String | Yes | Constant `1.0` | Version of this payload contract. |
| `bin_id` | String | Yes | 1–32 ASCII letters/digits, `_`, or `-`; first character alphanumeric | Stable identifier used in the MQTT topic and payload. |
| `timestamp` | String | Yes | UTC RFC 3339 date-time ending in `Z`, millisecond precision | Classification event creation time. |
| `class` | String | Yes | `GELBER_SACK`, `PAPIER`, `RESTMUELL`, `BIOABFALL`, `ALTGLAS`, or `UNSURE` | Accepted stream or low-confidence fallback. |
| `confidence` | Number | Yes | Finite value from `0.0` through `1.0`, inclusive | Model confidence for the selected stream; for `UNSURE`, the best candidate's confidence before fallback. |
| `status` | String | Yes | `RESULT` or `UNSURE`; must agree with `class` | Downstream state for UI and actuator handling. |
| `led_color` | String | Yes | `#RRGGBB`; must match the class mapping | Hexadecimal color for the bin indicator. |
| `led_pattern` | String | Yes | `SOLID` or `BLINK_SLOW`; must match the class mapping | LED behavior requested by the signal. |
| `ui_payload` | Object | Yes | Exactly `label_de`, `label_en`, and `action_tip` | Bilingual kiosk content associated with this result. |
| `ui_payload.label_de` | String | Yes | Non-empty; at most 24 characters | German stream name or uncertainty guidance label. |
| `ui_payload.label_en` | String | Yes | Non-empty; at most 32 characters | English stream name or uncertainty guidance label. |
| `ui_payload.action_tip` | Object | Yes | Exactly `de` and `en`; each non-empty and at most 24 characters | Short German and English preparation/disposal instructions. |
| `latency_ms` | Integer | No | `0`–`60000` | Elapsed edge processing time through publication; omit when unavailable. |

`status` is `RESULT` for one of the five recognized streams and `UNSURE` for the fallback class. `UNSURE` uses the blinking amber indicator. The default confidence threshold is `0.70`; threshold calibration is owned by task 2.2.4 and may change independently of this schema.

## 3. Waste Stream, LED, and Bilingual UI Mapping

| `class` | `led_color` | `led_pattern` | `status` | `label_de` | `label_en` | Default action tip (DE / EN) |
| --- | --- | --- | --- | --- | --- | --- |
| `GELBER_SACK` | `#FFD700` | `SOLID` | `RESULT` | Gelber Sack | Yellow packaging | Aludeckel entfernen. / Peel off aluminum lid. |
| `PAPIER` | `#0055A4` | `SOLID` | `RESULT` | Papier | Paper & cardboard | Sauber und trocken. / Keep clean and dry. |
| `RESTMUELL` | `#333333` | `SOLID` | `RESULT` | Restmüll | Residual waste | Nicht recycelbar? / Non-recyclable waste. |
| `BIOABFALL` | `#8B4513` | `SOLID` | `RESULT` | Bioabfall | Organic waste | Verpackung entfernen. / Remove packaging. |
| `ALTGLAS` | `#2E8B57` | `SOLID` | `RESULT` | Altglas | Glass recycling | Farbtrennung prüfen. / Check glass color. |
| `UNSURE` | `#FFBF00` | `BLINK_SLOW` | `UNSURE` | Unsicher | Unsure | Bitte nochmals prüfen. / Please check again. |

The green Altglas indicator is a stream-level cue and does not imply that municipal white/green/brown glass sorting is unnecessary. Pfand is not a seventh classifier class; a Pfand-specific blink requires a separately supported rule or detector.

## 4. Concrete JSON Payload Examples

### Case A — High-confidence classification

Published to `smartbin/bin-01/classification` at QoS 1:

```json
{
  "schema_version": "1.0",
  "bin_id": "bin-01",
  "timestamp": "2026-11-15T21:24:28.319Z",
  "class": "GELBER_SACK",
  "confidence": 0.94,
  "status": "RESULT",
  "led_color": "#FFD700",
  "led_pattern": "SOLID",
  "ui_payload": {
    "label_de": "Gelber Sack",
    "label_en": "Yellow packaging",
    "action_tip": {
      "de": "Aludeckel entfernen.",
      "en": "Peel off aluminum lid."
    }
  },
  "latency_ms": 143
}
```

### Case B — Low-confidence fallback

If the best model candidate is below the configured threshold, publish `UNSURE`; do not publish its candidate as an accepted stream. Here the best-candidate confidence is `0.52`:

```json
{
  "schema_version": "1.0",
  "bin_id": "bin-01",
  "timestamp": "2026-11-15T21:24:28.501Z",
  "class": "UNSURE",
  "confidence": 0.52,
  "status": "UNSURE",
  "led_color": "#FFBF00",
  "led_pattern": "BLINK_SLOW",
  "ui_payload": {
    "label_de": "Unsicher",
    "label_en": "Unsure",
    "action_tip": {
      "de": "Bitte nochmals prüfen.",
      "en": "Please check again."
    }
  },
  "latency_ms": 151
}
```

### Case C — Student feedback for Active Learning

Feedback is a separate QoS 1 event on `smartbin/bin-01/feedback`. `classification_timestamp` references the timestamp of the classification being reviewed; `bin_id` scopes that reference. The feedback intake must associate the response with the original signal before using it for human review:

```json
{
  "schema_version": "1.0",
  "bin_id": "bin-01",
  "timestamp": "2026-11-15T21:24:35.042Z",
  "classification_timestamp": "2026-11-15T21:24:28.319Z",
  "feedback": {
    "was_accurate": false,
    "corrected_class": "PAPIER",
    "ui_language": "en"
  }
}
```

The feedback envelope is illustrative and distinct from the classification schema. Do not include student identity or raw image data in feedback messages. A correction is a review signal; it must not trigger automatic model retraining.

## 5. UI/UX and Downstream Integration Notes

- The kiosk subscribes to the classification topic and renders `label_de`, `label_en`, and both localized `action_tip` strings. It should provide the accuracy question in the selected UI language and publish the response to the feedback topic.
- The LED actuation adapter maps `led_color` and `led_pattern` to the physical controller. The `UNSURE` signal always uses amber `BLINK_SLOW`; adapters must not infer a different stream from low confidence.
- Task **2.3.4 (UI feasibility review)** should verify text fit, accessibility, localization, and the result/feedback interaction on the selected display. Tips are deliberately short to fit the payload budget.
- Task **2.2.4 (confidence threshold calibration)** owns the operating threshold and should review false-positive risk versus fallback rate. The signal format communicates the chosen output; it does not calibrate or reinterpret confidence.
- QoS 1 can deliver duplicates. UI feedback and downstream consumers should handle repeated messages safely; classification payloads are not retained, so stale actuation commands are not replayed after reconnect.
- The contract is validated by `iot/schemas/classification_signal.schema.json` and the standard-library validator in `iot/message_schema.py`. Schema version 1.0 rejects additional classification fields; incompatible changes require a versioned contract update.
