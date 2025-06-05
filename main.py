# main.py
import time
import signal
import shutil
from rich.console import Console
from rich.live import Live
from rich.text import Text
import pyfiglet
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
    ascii_art = pyfiglet.figlet_format(message)
    return ascii_art.splitlines()

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

if __name__ == "__main__":
    try:
        scroll_banner()
    finally:
        console.clear()
        console.print("[bold green]Exited gracefully.[/bold green]")

