#!/usr/bin/env python3
"""Render smart-bin classification events as a hardware-free LED panel."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import re
import sys
import time
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iot.fallback_policy import (  # noqa: E402
    DEFAULT_CONFIDENCE_THRESHOLD,
    validate_fallback_policy,
)
from iot.message_schema import (  # noqa: E402
    STREAM_CONFIG,
    build_classification_message,
)


BLINK_INTERVAL_SECONDS = 0.35
DEFAULT_BIN_ID = "hof-dorm-01"
BIN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")


def _ansi_color(hex_color: str, symbol: str) -> str:
    red, green, blue = (
        int(hex_color[index : index + 2], 16) for index in (1, 3, 5)
    )
    return f"\033[38;2;{red};{green};{blue}m{symbol}\033[0m"


def render_terminal(
    payload: dict, blink_on: bool = True, scenario: Optional[str] = None
) -> None:
    """Print the six-channel panel using ANSI true-color indicators."""
    selected = payload["class"]
    if scenario:
        print(f"\n--- {scenario} ---")

    ui_payload = payload["ui_payload"]
    tips = ui_payload["action_tip"]
    latency = payload.get("latency_ms", "n/a")
    print(
        f"Result: {ui_payload['label_de']} / {ui_payload['label_en']} "
        f"({selected}) | confidence={payload['confidence']:.2f} | "
        f"latency={latency} ms"
    )
    print(f"Separation tip: DE: {tips['de']} | EN: {tips['en']}")
    print("LED panel:")

    for waste_class, config in STREAM_CONFIG.items():
        active = waste_class == selected
        blinking = active and config.led_pattern == "BLINK_SLOW"
        lit = active and (not blinking or blink_on)
        symbol = "●" if lit else "○"
        indicator = _ansi_color(config.led_color, symbol)
        if not active:
            status = "[OFF]"
        elif blinking:
            phase = "ON" if blink_on else "OFF"
            status = f"[BLINK_SLOW] phase={phase}"
        else:
            status = "[ON - SOLID]"
        print(
            f"  {indicator} {waste_class:12} "
            f"{config.label_de:14} / {config.label_en:20} {status}"
        )


class TkLedPanel:
    """Small optional Tkinter panel; all updates are made on the main thread."""

    def __init__(self) -> None:
        if sys.platform != "win32" and not os.environ.get("DISPLAY"):
            raise RuntimeError("Tkinter GUI needs a graphical display (DISPLAY).")
        try:
            import tkinter as tk
        except ImportError as exc:
            raise RuntimeError("Tkinter is unavailable in this Python installation.") from exc

        self._tk = tk
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            raise RuntimeError(f"Could not initialize Tkinter: {exc}") from exc
        self.root.title("Smart German Waste Classifier — LED Simulator")
        self.root.resizable(False, False)
        self.summary = tk.StringVar(value="Waiting for classification…")
        tk.Label(
            self.root, textvariable=self.summary, justify="left", padx=12, pady=10
        ).pack(anchor="w")
        self._indicators = {}

        for waste_class, config in STREAM_CONFIG.items():
            row = tk.Frame(self.root, padx=12, pady=3)
            row.pack(fill="x")
            canvas = tk.Canvas(row, width=30, height=30, highlightthickness=0)
            canvas.pack(side="left")
            dot = canvas.create_oval(
                5, 5, 25, 25, fill="#202020", outline=config.led_color, width=2
            )
            text = (
                f"{config.label_de} / {config.label_en} "
                f"({waste_class}, {config.led_color})"
            )
            tk.Label(row, text=text, anchor="w", width=48).pack(side="left")
            self._indicators[waste_class] = (canvas, dot, config)

    def render(self, payload: dict, blink_on: bool = True) -> None:
        selected = payload["class"]
        ui_payload = payload["ui_payload"]
        tips = ui_payload["action_tip"]
        latency = payload.get("latency_ms", "n/a")
        self.summary.set(
            f"{ui_payload['label_de']} / {ui_payload['label_en']} "
            f"({selected})  confidence={payload['confidence']:.2f}  "
            f"latency={latency} ms\n"
            f"DE: {tips['de']}   EN: {tips['en']}"
        )
        for waste_class, (canvas, dot, config) in self._indicators.items():
            active = waste_class == selected
            lit = active and (
                config.led_pattern != "BLINK_SLOW" or blink_on
            )
            canvas.itemconfigure(
                dot,
                fill=config.led_color if lit else "#202020",
                outline=config.led_color,
            )
        self.root.update_idletasks()
        self.root.update()


def _render_payload(payload: dict, gui: Optional[TkLedPanel], scenario: str) -> None:
    blinking = payload["led_pattern"] == "BLINK_SLOW"
    frames = (True, False, True, False) if blinking else (True,)
    for index, blink_on in enumerate(frames):
        if gui:
            if index == 0:
                gui.summary.set(f"{scenario}\n{gui.summary.get()}")
            gui.render(payload, blink_on)
        else:
            render_terminal(payload, blink_on=blink_on, scenario=scenario if index == 0 else None)
        if blinking and index + 1 < len(frames):
            time.sleep(BLINK_INTERVAL_SECONDS)


def run_demo(gui: Optional[TkLedPanel] = None) -> int:
    scenarios = (
        (
            "Clean yogurt cup — GELBER_SACK",
            "Clean yogurt packaging; aluminum lid removed.",
            "GELBER_SACK",
            0.94,
            128,
        ),
        (
            "Clean paper — PAPIER",
            "Paper is clean and dry.",
            "PAPIER",
            0.92,
            116,
        ),
        (
            "Greasy pizza box — UNSURE (ambiguous class margin)",
            "Top class margin is ambiguous; ask the user to check.",
            "UNSURE",
            0.76,
            141,
        ),
        (
            "Blurry object — UNSURE (low confidence)",
            "The top class is below the 0.70 confidence threshold.",
            "RESTMUELL",
            0.38,
            153,
        ),
    )

    for title, rationale, predicted_class, confidence, latency_ms in scenarios:
        payload = build_classification_message(
            predicted_class=predicted_class,
            confidence=confidence,
            bin_id=DEFAULT_BIN_ID,
            threshold=DEFAULT_CONFIDENCE_THRESHOLD,
            latency_ms=latency_ms,
        )
        validate_fallback_policy(payload)
        _render_payload(payload, gui, f"{title}\n{rationale}")

    if gui:
        gui.summary.set(f"Demo complete\n{gui.summary.get()}")
        gui.root.update_idletasks()
        gui.root.update()
        gui.root.mainloop()
    return 0


def _valid_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be from 1 to 65535")
    return port


def run_mqtt(
    broker: str, port: int, bin_id: str, gui: Optional[TkLedPanel] = None
) -> int:
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        print(
            "MQTT mode requires paho-mqtt; install the project requirements first.",
            file=sys.stderr,
        )
        return 2

    topic = f"smartbin/{bin_id}/classification"
    incoming: queue.Queue[dict] = queue.Queue()

    callback_api = getattr(mqtt, "CallbackAPIVersion", None)
    if callback_api is not None:
        client = mqtt.Client(callback_api.VERSION2)
    else:
        client = mqtt.Client()

    def on_connect(client, userdata, flags, reason_code, properties=None) -> None:
        code = getattr(reason_code, "value", reason_code)
        if code != 0:
            print(f"MQTT broker rejected connection (code {code}).", file=sys.stderr)
            return
        result, _message_id = client.subscribe(topic, qos=1)
        if result != mqtt.MQTT_ERR_SUCCESS:
            print(f"Could not subscribe to {topic} (code {result}).", file=sys.stderr)
            return
        print(f"Listening on {topic} at {broker}:{port}; press Ctrl+C to stop.")

    def on_message(client, userdata, message) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            validate_fallback_policy(payload)
            if payload["bin_id"] != bin_id:
                raise ValueError(
                    f"message bin_id {payload['bin_id']!r} does not match {bin_id!r}"
                )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            print(
                f"Rejected MQTT message on {message.topic}: {exc}",
                file=sys.stderr,
            )
            return
        incoming.put(payload)

    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(broker, port, keepalive=60)
    except OSError as exc:
        print(
            f"Cannot connect to MQTT broker at {broker}:{port}: {exc}. "
            "Start Mosquitto or use --mode demo.",
            file=sys.stderr,
        )
        return 1

    try:
        client.loop_start()
        print(f"Connecting to {broker}:{port} and subscribing to {topic}…")
        if gui:
            def poll_messages() -> None:
                try:
                    payload = incoming.get_nowait()
                except queue.Empty:
                    pass
                else:
                    _render_payload(payload, gui, f"MQTT event on {topic}")
                if gui.root.winfo_exists():
                    gui.root.after(100, poll_messages)

            gui.root.after(100, poll_messages)
            gui.root.mainloop()
        else:
            while True:
                payload = incoming.get()
                _render_payload(payload, None, f"MQTT event on {topic}")
    except KeyboardInterrupt:
        print("\nStopping LED simulator.")
    finally:
        client.disconnect()
        client.loop_stop()
    return 0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulate the six smart-bin LED channels without hardware."
    )
    parser.add_argument(
        "--mode",
        choices=("demo", "mqtt"),
        default="demo",
        help="offline four-scenario demo or live MQTT subscriber (default: demo)",
    )
    parser.add_argument("--broker", default="localhost", help="MQTT broker hostname")
    parser.add_argument("--port", type=_valid_port, default=1883, help="MQTT port")
    parser.add_argument("--bin-id", default=DEFAULT_BIN_ID, help="smart-bin identifier")
    parser.add_argument(
        "--gui", action="store_true", help="also display the panel in Tkinter"
    )
    args = parser.parse_args(argv)
    if not BIN_ID_PATTERN.fullmatch(args.bin_id):
        parser.error("--bin-id must be 1-32 ASCII letters, digits, '_' or '-'")
    return args


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    gui = None
    if args.gui:
        try:
            gui = TkLedPanel()
        except RuntimeError as exc:
            print(f"Cannot open LED simulator GUI: {exc}", file=sys.stderr)
            return 2
    if args.mode == "demo":
        return run_demo(gui)
    return run_mqtt(args.broker, args.port, args.bin_id, gui)


if __name__ == "__main__":
    raise SystemExit(main())
