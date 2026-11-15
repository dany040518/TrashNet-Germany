# ADR 002: Hardware Simulation Approach

- **Status:** Accepted
- **Date:** 2026-11-15
- **Author:** Danna Sanchez (DM)
- **Related Tickets:** EDM-37, EDM-38, EDM-39, EDM-40, EDM-41

## 1. Context and Constraints

The project does not yet have access to a Raspberry Pi or LED strips. Physical equipment must be requested from the Hochschule Hof laboratory, so hardware availability cannot block development or evaluation. The smart-bin demonstrator is intended to operate offline in student-residence basements (*Müllraum*), and the assessment requires a fully reproducible workflow from a clean Git clone on Ubuntu or JupyterHub without external hardware.

The simulator must consume the official version 1.0 classification JSON envelope, validate the schema and fallback behavior, and subscribe to `smartbin/{bin_id}/classification`. It must present the five German waste streams and the amber `UNSURE` indicator, including bilingual labels and separation guidance, while preserving a direct migration path to a physical MQTT subscriber.

## 2. Options Evaluated

### Option A: Python LED Simulator (CLI ANSI Visual Panel + Optional Tkinter GUI)

Implement `iot/led_simulator.py` as a Python subscriber and visual actuator. Its standalone demo mode uses the repository's message builder and validators and runs without a broker, external hardware, or additional packages. The terminal panel uses ANSI true-color indicators; an optional Tkinter view displays the same six states when a graphical display is available. MQTT mode uses `paho-mqtt` to subscribe to the classification topic when a local broker is available.

This option gives evaluators a reproducible demo from a fresh clone while exercising the same JSON contract used by the rest of the system. The GUI is optional, not a runtime dependency for the CLI or demo.

### Option B: Wokwi Virtual ESP32 Simulator

Wokwi can model an ESP32 and NeoPixel strip in a browser or VS Code and provides a useful embedded-development path. Connecting the virtual device to the project's local MQTT broker requires the Wokwi IoT Gateway, whose networking setup requires internet access. This adds an external service and configuration burden, weakens offline operation, and makes automated evaluation less predictable.

### Option C: Physical Raspberry Pi + GPIO LEDs (University Lab Hardware)

A Raspberry Pi with GPIO-driven LEDs is representative of the final physical demonstrator. However, the equipment must first be requested from the university laboratory, and access cannot be guaranteed for every developer or evaluator. It is suitable as an optional Sprint 4/5 demonstration, but not as a blocking development or acceptance dependency.

## 3. Weighted Decision Matrix

Scores use a 1–5 scale, with 5 best satisfying the criterion. Weighted points are `weight × score`; the sum is divided by 100 for a score out of 5.

![ADR-002 Hardware Simulation Comparison](images/adr_hardware_simulation.png)

| Decision criterion | Weight | Option A: Python | A points | Option B: Wokwi | B points | Option C: Physical Pi | C points |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Zero Hardware Dependency | 30% | 5 | 150 | 5 | 150 | 1 | 30 |
| Fresh-Clone Reproducibility | 25% | 5 | 125 | 2 | 50 | 2 | 50 |
| Offline Execution | 20% | 5 | 100 | 1 | 20 | 1 | 20 |
| Visual Demo Clarity | 15% | 4.6 | 69 | 5 | 75 | 5 | 75 |
| Migration Path to Real Hardware | 10% | 4.5 | 45 | 4 | 40 | 5 | 50 |
| **Total** | **100%** |  | **489 / 100 = 4.89 / 5.0** |  | **335 / 100 = 3.35 / 5.0** |  | **225 / 100 = 2.25 / 5.0** |

Option A wins because it is hardware-independent, works offline, and needs no broker for the clean-clone demo. Its small deductions reflect that a terminal panel is less immersive than a graphical or physical strip and that the eventual GPIO integration needs a separate adapter.

## 4. Decision and Tiered Rollout Strategy

**Select Option A, the Python LED Simulator, as the official reproducible actuator.** It uses the official JSON envelope (`class`, `confidence`, `timestamp`, `led_color`, `led_pattern`, `bin_id`, and `ui_payload`) and validates each message with `iot/message_schema.py` and `iot/fallback_policy.py`. MQTT mode subscribes to `smartbin/{bin_id}/classification`; standalone demo mode exercises the same message path without a running broker.

- **Tier 1 — Primary (Sprints 2–6):** `iot/led_simulator.py` is the supported software actuator. Run `python3 iot/led_simulator.py --mode demo` for an offline, hardware-free demonstration. Use `--mode mqtt` to connect it to the local Mosquitto broker; the optional `--gui` flag opens a Tkinter panel when a graphical display is available.
- **Tier 2 — Optional stretch goal (Sprint 4/5):** If a Raspberry Pi and LED strip are approved by the Hochschule Hof laboratory, add a parallel MQTT subscriber/actuator. It must not change the ML code or version 1.0 JSON schema, and it must not make physical hardware a prerequisite for the reproducible simulator.

## 5. Consequences and Validation

- A clean clone can demonstrate all five stream colors and the blinking amber `UNSURE` fallback with Python's standard library; no Raspberry Pi, LED strip, GUI, or broker is needed for demo mode.
- MQTT mode requires `paho-mqtt` and a reachable local broker. If Mosquitto is unavailable, the simulator reports the connection failure instead of appearing to run.
- The simulator validates messages before display and rejects confidence/class combinations that violate the low-confidence fallback policy.
- The terminal is the baseline visual interface. Tkinter is an optional presentation layer and is only enabled when requested in a graphical environment.
- A later physical subscriber can consume the same classification event in parallel, preserving separation between ML decisions and hardware-specific actuation.
