from __future__ import annotations

import re
from typing import Any, Callable


def format_idr(amount: float) -> str:
    """Format angka ke string Rupiah dengan pemisah ribuan titik (misal Rp15.000)."""
    rounded = round(amount)
    sign = "-" if rounded < 0 else ""
    formatted = f"{abs(rounded):,}".replace(",", ".")
    return f"{sign}Rp{formatted}"


def next_prefixed_id(collection: list[dict[str, Any]], id_field: str, prefix: str) -> str:
    """Bangkitkan ID berurutan bebas bentrok (misal M07, P13) berbasis angka maksimum.

    Menghindari duplikasi ID setelah penghapusan record dibanding memakai len() + 1.
    """
    max_num = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)
    for item in collection:
        raw_id = str(item.get(id_field, "")).strip()
        match = pattern.match(raw_id)
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"{prefix}{max_num + 1:02d}"


def print_header(title: str) -> None:
    """Cetak banner judul yang seragam untuk setiap layar CLI."""
    border = "=" * 64
    print(f"\n{border}")
    print(f"  {title}")
    print(border)


def prompt_non_empty(label: str) -> str:
    """Minta input teks dan ulangi hingga user mengisi minimal satu karakter."""
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Input tidak boleh kosong. Silakan coba lagi.")


def prompt_int(label: str, min_value: int | None = None, max_value: int | None = None) -> int:
    """Minta input bilangan bulat dengan validasi batas bawah/atas opsional."""
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
    """Minta input angka desimal dengan validasi batas bawah/atas opsional."""
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
    """Loop menu CLI generik agar tiap aplikasi tidak mengulang logika navigasi."""
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
