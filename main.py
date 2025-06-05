# main.py
import time
import signal
import shutil
import itertools
import pyfiglet
import re
import random
import math

from rich.console import Console
from rich.live import Live
from rich.text import Text
from config import CONFIG

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

def compute_vertical_padding(content_height, terminal_height, align="center"):
    """Вычисляет вертикальный отступ"""
    if align == "top":
        return 0
    elif align == "bottom":
        return max(0, terminal_height - content_height)
    else:
        return max(0, (terminal_height - content_height) // 2)

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
            factor = (math.sin(i / steps * 2 * math.pi) + 1) / 2
            brightness = 1 - range_ + range_ * 2 * factor
            r = clamp(r0 * brightness)
            g = clamp(g0 * brightness)
            b = clamp(b0 * brightness)
            yield f"#{r:02x}{g:02x}{b:02x}"

def obo_animation():
    message = CONFIG["message"]
    delay = CONFIG["delay"]
    term_width, term_height = get_terminal_size()
    letter_spacing = 2

    base_color = CONFIG.get("color", "#ffaa00")
    breath_steps = CONFIG.get("breath_steps", 80)
    breath_cycles = CONFIG.get("breath_cycles", 3)
    total_frames = breath_steps * breath_cycles

    while running:
        with Live("", console=console, screen=True, refresh_per_second=1 / delay) as live:
            fixed_ascii = None

            for i, char in enumerate(message):
                flying_ascii = pyfiglet.figlet_format(char).splitlines()
                flying_height = len(flying_ascii)

                if i > 0:
                    fixed_ascii = pyfiglet.figlet_format(message[:i]).splitlines()
                    fixed_width = max(len(line) for line in fixed_ascii)
                else:
                    fixed_ascii = []
                    fixed_width = 0

                start_x = term_width
                stop_x = fixed_width + letter_spacing

                # vertical alignment based on flying + fixed block height
                content_height = max(len(fixed_ascii), flying_height)
                vertical_pad = compute_vertical_padding(content_height, term_height, CONFIG.get("vertical_align", "center"))

                while start_x > stop_x:
                    if not running:
                        return

                    frame = Text("\n" * vertical_pad)
                    for row in range(content_height):
                        line = ""
                        if row < len(fixed_ascii):
                            line += fixed_ascii[row]
                        else:
                            line += " " * stop_x

                        if row < len(flying_ascii):
                            fly_line = flying_ascii[row]
                            padded = " " * max(0, start_x - len(line)) + fly_line
                            line += padded

                        frame.append(line[:term_width].ljust(term_width) + "\n", style=base_color)

                    live.update(frame)
                    time.sleep(delay)
                    start_x -= 1

            # breathing phase
            full = pyfiglet.figlet_format(message).splitlines()
            breath_gen = breathing_brightness_gen(base_color, range_=0.4, steps=breath_steps)
            vertical_pad = compute_vertical_padding(len(full), term_height, CONFIG.get("vertical_align", "center"))

            for _ in range(total_frames):
                if not running:
                    return
                color = next(breath_gen)
                frame = Text("\n" * vertical_pad)
                for line in full:
                    frame.append(line[:term_width].ljust(term_width) + "\n", style=color)
                live.update(frame)
                time.sleep(delay * 3)

        if not CONFIG.get("loop", False):
            break

def main():
    anim = CONFIG["animation"]
    if anim == "obo":
        obo_animation()
    elif anim == "swaga":
        swaga_animation()
    elif anim == "scroll":
        scroll_banner()
    else:
        console.print(f"[red]Unknown animation type: {anim}[/red]")

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

                vertical_pad = compute_vertical_padding(len(dynamic_banner), term_height, CONFIG.get("vertical_align", "center"))

                frame = Text("\n" * vertical_pad)
                for line in dynamic_banner:
                    frame.append(line.center(term_width) + "\n", style=CONFIG["color"])

                live.update(frame)
                time.sleep(CONFIG["delay"])

            if not CONFIG["loop"]:
                break

def swaga_animation():
    import colorsys

    def rgb_color_gen(step=5):
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

                vertical_pad = compute_vertical_padding(len(banner_lines), term_height, CONFIG.get("vertical_align", "center"))
                frame = Text("\n" * vertical_pad)

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

                color = next(rgb_gen)
                for line in banner_lines:
                    frame.append(line.center(term_width) + "\n", style=color)

                live.update(frame)
                time.sleep(CONFIG["delay"])

            if not CONFIG["loop"]:
                break

if __name__ == "__main__":
    try:
        main()
    finally:
        console.clear()
