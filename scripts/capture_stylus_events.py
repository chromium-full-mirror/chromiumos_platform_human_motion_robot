# Copyright 2024 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Handles capturing stylus events from DUTs to be used with HMR"""

import argparse
import math
import threading

import evdev  # pylint: disable=import-error


MM_PER_INCH = 25.4
# Ratio of screen height and width relative to its diagonal length, assuming
# it is a 16:9 screen.
SCREEN_SIZE_HEIGHT_RATIO_OF_DIAGONAL = math.sqrt(81 / 337)
SCREEN_SIZE_WIDTH_RATIO_OF_DIAGONAL = (
    SCREEN_SIZE_HEIGHT_RATIO_OF_DIAGONAL * 16 / 9
)

# All reference images used in the stylus drawing tests are scaled to be in mm
# and taken on a 13.3 inch screen.
REFERENCE_SCREEN_SIZE = 13.3


class StylusEvent:
    """Stylus Event captured from DUT"""

    def __init__(self, x, y, pressure, time):
        self.x = x
        self.y = y
        self.pressure = pressure
        self.time = time

    def scale(self, scale_factor_x, scale_factor_y):
        self.x *= scale_factor_x
        self.y *= scale_factor_y


def get_args():
    parser = argparse.ArgumentParser(
        description="Capture stylus events used for HMR"
    )
    parser.add_argument(
        "--output", type=str, default="output.csv", help="Output file location"
    )
    subparser = parser.add_subparsers(dest="subcommand")
    parser_drawing = subparser.add_parser(
        "scale-output-for-drawing-test",
        description="Automatically scales stylus drawing events so that they"
        "can be used in a stylus drawing test",
    )
    parser_drawing.add_argument(
        "--diagonal_screen_size",
        type=float,
        required=True,
        help="Diagonal screen size of DUT in inches",
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


def get_screen_dimensions_in_pixels(stylus):
    abs_infos = dict(stylus.capabilities().get(evdev.ecodes.EV_ABS))
    screen_width_pixels = abs_infos.get(evdev.ecodes.ABS_X).max
    screen_height_pixels = abs_infos.get(evdev.ecodes.ABS_Y).max
    return screen_height_pixels, screen_width_pixels


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
    events_are_in_pixels = isinstance(events[0].x, int) and isinstance(
        events[0].y, int
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("x,y,pressure,time\n")
        for event in events:
            if events_are_in_pixels:
                to_write = (
                    f"{event.x},{event.y},{event.pressure},{event.time:.6f},\n"
                )
            else:
                # The x, y values in reference images are rounded to 2 decimal
                # places.
                to_write = (
                    f"{event.x:.2f},{event.y:.2f},{event.pressure}"
                    f",{event.time:.6f},\n"
                )
            f.write(to_write)


def scale_data_for_drawing_test(
    stylus_events,
    screen_height_pixels,
    screen_width_pixels,
    diagonal_screen_size_inches,
):
    diagonal_screen_size_mm = diagonal_screen_size_inches * MM_PER_INCH
    screen_height_mm = (
        diagonal_screen_size_mm * SCREEN_SIZE_HEIGHT_RATIO_OF_DIAGONAL
    )
    screen_width_mm = (
        diagonal_screen_size_mm * SCREEN_SIZE_WIDTH_RATIO_OF_DIAGONAL
    )

    dut_screen_size_to_reference_image_screen_size_ratio = (
        diagonal_screen_size_inches / REFERENCE_SCREEN_SIZE
    )

    # Scales pixel values to mm, and scales them as though they were taken on
    # the same screen size as the reference image.
    x_scale_factor = (
        screen_width_mm
        / screen_width_pixels
        * dut_screen_size_to_reference_image_screen_size_ratio
    )
    y_scale_factor = (
        screen_height_mm
        / screen_height_pixels
        * dut_screen_size_to_reference_image_screen_size_ratio
    )
    for stylus_event in stylus_events:
        stylus_event.scale(x_scale_factor, y_scale_factor)


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

    if args.subcommand == "scale-output-for-drawing-test":
        (
            screen_height_pixels,
            screen_width_pixels,
        ) = get_screen_dimensions_in_pixels(stylus)

        print(
            "Scaling output data to mm and to the reference image screen size"
            f"({REFERENCE_SCREEN_SIZE})"
        )
        scale_data_for_drawing_test(
            stylus_events,
            screen_height_pixels,
            screen_width_pixels,
            args.diagonal_screen_size,
        )

    write_stylus_events_to_file(args.output, stylus_events)
    print(f"Captured {len(stylus_events)} stylus events")


if __name__ == "__main__":
    main()
