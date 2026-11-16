from __future__ import annotations

from typing import Callable


def format_idr(amount: float) -> str:
    """Format a numeric value into Indonesian Rupiah currency string.

    Grouping thousands with dots matches local Indonesian financial display
    conventions across canteen, library fine, and personal finance apps.
    """
    rounded = round(amount)
    sign = "-" if rounded < 0 else ""
    formatted = f"{abs(rounded):,}".replace(",", ".")
    return f"{sign}Rp{formatted}"


def print_header(title: str) -> None:
    """Render a consistent section banner for terminal readability."""
    border = "=" * 64
    print(f"\n{border}")
    print(f"  {title}")
    print(border)


def prompt_non_empty(label: str) -> str:
    """Prompt the user until a non-empty string is entered."""
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Input tidak boleh kosong. Silakan coba lagi.")


def prompt_int(label: str, min_value: int | None = None, max_value: int | None = None) -> int:
    """Prompt the user for an integer within optional inclusive bounds."""
    while True:
        raw = input(f"{label}: ").strip()
        try:
            parsed = int(raw)
        except ValueError:
            print("Masukkan angka bulat yang valid.")
            continue
        if min_value is not None and parsed < min_value:
            print(f"Nilai minimal adalah {min_value}.")
            continue
        if max_value is not None and parsed > max_value:
            print(f"Nilai maksimal adalah {max_value}.")
            continue
        return parsed


def prompt_float(label: str, min_value: float | None = None, max_value: float | None = None) -> float:
    """Prompt the user for a floating-point number within optional bounds."""
    while True:
        raw = input(f"{label}: ").strip()
        try:
            parsed = float(raw)
        except ValueError:
            print("Masukkan angka yang valid.")
            continue
        if min_value is not None and parsed < min_value:
            print(f"Nilai minimal adalah {min_value}.")
            continue
        if max_value is not None and parsed > max_value:
            print(f"Nilai maksimal adalah {max_value}.")
            continue
        return parsed


def run_menu_loop(title: str, options: list[tuple[str, Callable[[], bool]]]) -> None:
    """Drive a reusable CLI menu loop until a handler returns False to exit.

    Centralizing menu dispatch eliminates boilerplate loops and bounds checking
    across all five interactive applications.
    """
    while True:
        print_header(title)
        for idx, (label, _) in enumerate(options, start=1):
            print(f"  {idx}. {label}")
        print("  0. Kembali / Keluar")
        choice = prompt_int("Pilih menu", min_value=0, max_value=len(options))
        if choice == 0:
            return
        _, handler = options[choice - 1]
        should_continue = handler()
        if not should_continue:
            return
