# main.py
import time
import signal
import shutil
import itertools
from rich.console import Console
from rich.live import Live
from rich.text import Text
import pyfiglet
from config import CONFIG
import re
import random

console = Console()
running = True

def handle_exit(signum, frame):
    global running
    running = False

signal.signal(signal.SIGINT, handle_exit)

def get_terminal_size():
    return shutil.get_terminal_size((80, 24))

def generate_banner_lines(message):
    return pyfiglet.figlet_format(message).splitlines()

import math

def breathing_brightness_gen(base_color, range_=0.5, steps=60):
    """Плавно меняет яркость HEX цвета: 0.5 → 1.0 → 0.5"""
    if not re.fullmatch(r"#([0-9a-fA-F]{6})", base_color):
        raise ValueError(f"Invalid HEX color format: {base_color}. Expected '#rrggbb'.")

    r0 = int(base_color[1:3], 16)
    g0 = int(base_color[3:5], 16)
    b0 = int(base_color[5:7], 16)

    def clamp(v): return max(0, min(255, int(v)))

    while True:
        for i in range(steps):
            factor = (math.sin(i / steps * 2 * math.pi) + 1) / 2  # 0→1→0
            brightness = 1 - range_ + range_ * 2 * factor  # 1±range_
            r = clamp(r0 * brightness)
            g = clamp(g0 * brightness)
            b = clamp(b0 * brightness)
            yield f"#{r:02x}{g:02x}{b:02x}"


def swaga_animation():
    import colorsys

    def rgb_color_gen(step=5):
        """Yield RGB hex colors cycling around the hue wheel."""
        h = 0.0
        while True:
            r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
            yield f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            h += step / 360
            if h >= 1:
                h -= 1

    message = CONFIG["message"]
    base_lines = generate_banner_lines(message)
    rgb_gen = rgb_color_gen(CONFIG.get("rgb_step", 5))

    scroll_width = len(base_lines[0]) + shutil.get_terminal_size().columns
    center_offset = scroll_width // 2

    with Live("", console=console, screen=True, refresh_per_second=1 / CONFIG["delay"]) as live:
        while running:
            paused = False
            for offset in range(scroll_width):
                if not running:
                    return

                term_width, term_height = get_terminal_size()
                banner_lines = []
                for line in base_lines:
                    padded = ' ' * term_width + line + ' ' * term_width
                    scroll_part = padded[offset:offset + term_width]
                    banner_lines.append(scroll_part)

                vertical_pad = max((term_height - len(banner_lines)) // 2, 0)
                frame = Text()
                frame.append("\n" * vertical_pad)

                # During pause, pulse RGB
                if not paused and offset == center_offset:
                    for _ in range(int(5 / CONFIG["delay"])):
                        if not running:
                            return
                        color = next(rgb_gen)
                        frame = Text("\n" * vertical_pad)
                        for line in base_lines:
                            frame.append(line.center(term_width) + "\n", style=color)
                        live.update(frame)
                        time.sleep(CONFIG["delay"])
                    paused = True
                    continue

                # Normal scrolling with RGB
                color = next(rgb_gen)
                for line in banner_lines:
                    frame.append(line.center(term_width) + "\n", style=color)

                live.update(frame)
                time.sleep(CONFIG["delay"])

            if not CONFIG["loop"]:
                break


def scroll_banner():
    banner_lines = generate_banner_lines(CONFIG["message"])
    scroll_width = len(banner_lines[0]) + shutil.get_terminal_size().columns

    with Live("", console=console, screen=True, refresh_per_second=1 / CONFIG["delay"]) as live:
        while running:
            for offset in range(scroll_width):
                if not running:
                    return

                term_width, term_height = get_terminal_size()
                dynamic_banner = []
                for line in banner_lines:
                    padded_line = ' ' * term_width + line + ' ' * term_width
                    scroll_part = padded_line[offset:offset + term_width]
                    dynamic_banner.append(scroll_part)

                vertical_pad = max((term_height - len(dynamic_banner)) // 2, 0)

                frame = Text()
                frame.append("\n" * vertical_pad)
                for line in dynamic_banner:
                    frame.append(line.center(term_width) + "\n", style=CONFIG["color"])

                live.update(frame)
                time.sleep(CONFIG["delay"])

            if not CONFIG["loop"]:
                break

def main():
    anim = CONFIG["animation"]
    if anim == "scroll":
        scroll_banner()
    elif anim == "swaga":
        swaga_animation()

    else:
        console.print(f"[red]Unknown animation type: {anim}[/red]")

if __name__ == "__main__":
    try:
        main()
    finally:
        console.clear()
