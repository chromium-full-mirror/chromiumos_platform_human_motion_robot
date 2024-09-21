# Copyright 2024 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Handles capturing stylus events from DUTs to be used with HMR"""

import argparse
import threading

import evdev  # pylint: disable=import-error


class StylusEvent:
    """Stylus Event captured from DUT"""

    def __init__(self, x, y, pressure, time):
        self.x = x
        self.y = y
        self.pressure = pressure
        self.time = time


def get_args():
    parser = argparse.ArgumentParser(
        description="Capture stylus events used for HMR"
    )
    parser.add_argument(
        "--output", type=str, default="output.csv", help="Output file location"
    )

    args = parser.parse_args()
    return args


def find_stylus():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

    for device in devices:
        capabilities = device.capabilities()
        keys = capabilities.get(evdev.ecodes.EV_KEY)
        if keys is None:
            continue
        if (
            evdev.ecodes.BTN_TOOL_PEN in keys
            and evdev.ecodes.BTN_STYLUS in keys
            and evdev.ecodes.BTN_STYLUS2 in keys
        ):
            return device
    raise RuntimeError("No stylus detected")


def wait_for_stop_capture(stop_capture):
    input("Press enter to stop capturing\n")
    stop_capture.set()
    # stylus.read_loop() yields until a new event is triggered, therefore an
    # additional touch is required to break from the loop.
    print("Touch the screen with the stylus to finish capture.")


def capture_stylus_events(stylus, stop_capture):
    stylus_events = []
    capturing = False
    most_recent_x = 0
    most_recent_y = 0
    most_recent_pressure = 0
    for event in stylus.read_loop():
        if stop_capture.is_set():
            return stylus_events
        if (
            event.type == evdev.ecodes.EV_KEY
            and event.code == evdev.ecodes.BTN_TOOL_PEN
        ):
            capturing = bool(event.value)
        elif event.type == evdev.ecodes.EV_ABS:
            if event.code == evdev.ecodes.ABS_X:
                most_recent_x = event.value
            elif event.code == evdev.ecodes.ABS_Y:
                most_recent_y = event.value
            elif event.code == evdev.ecodes.ABS_PRESSURE:
                most_recent_pressure = event.value
        elif event.type == evdev.ecodes.EV_SYN and capturing:
            stylus_event = StylusEvent(
                most_recent_x,
                most_recent_y,
                most_recent_pressure,
                event.timestamp(),
            )
            stylus_events.append(stylus_event)


def write_stylus_events_to_file(output_file, events):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("x,y,pressure,time\n")
        for event in events:
            to_write = (
                f"{event.x},{event.y},{event.pressure},{event.time:.6f},\n"
            )
            f.write(to_write)


def main():
    args = get_args()
    stylus = find_stylus()

    # The stylus event capture will stop when a user input is received.
    stop_capture = threading.Event()
    wait_for_stop_capture_thread = threading.Thread(
        target=wait_for_stop_capture, args=(stop_capture,)
    )
    wait_for_stop_capture_thread.start()

    stylus_events = capture_stylus_events(stylus, stop_capture)
    wait_for_stop_capture_thread.join()

    write_stylus_events_to_file(args.output, stylus_events)
    print(f"Captured {len(stylus_events)} stylus events")


if __name__ == "__main__":
    main()
