from __future__ import annotations

from typing import Any, Callable


# Ubah angka nominal menjadi format Rupiah (contoh: 15000 -> "Rp15.000").
def format_idr(amount: float) -> str:
    """Format angka ke string Rupiah dengan pemisah ribuan titik (misal Rp15.000)."""
    rounded = round(amount)
    sign = "-" if rounded < 0 else ""
    formatted = f"{abs(rounded):,}".replace(",", ".")
    return f"{sign}Rp{formatted}"


# Buat ID urut baru (misal M07/P13) berdasarkan nomor maksimum agar aman setelah ada data dihapus.
def next_prefixed_id(collection: list[dict[str, Any]], id_field: str, prefix: str) -> str:
    """Bangkitkan ID berurutan bebas bentrok (misal M07, P13) berbasis angka maksimum."""
    max_num = max(
        (
            int(s[len(prefix):])
            for item in collection
            if (s := str(item.get(id_field, "")).strip()).lower().startswith(prefix.lower())
            and s[len(prefix):].isdigit()
        ),
        default=0,
    )
    return f"{prefix}{max_num + 1:02d}"


# Tampilkan header pemisah judul layar di terminal.
def print_header(title: str) -> None:
    """Cetak banner judul yang seragam untuk setiap layar CLI."""
    border = "=" * 64
    print(f"\n{border}")
    print(f"  {title}")
    print(border)


# Minta input string dari user dan tolak input kosong.
def prompt_non_empty(label: str) -> str:
    """Minta input teks dan ulangi hingga user mengisi minimal satu karakter."""
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print("Input tidak boleh kosong. Silakan coba lagi.")


# Helper internal untuk membaca input angka (int/float) beserta validasi batas min-max.
def _prompt_num(
    label: str,
    cast: Callable[[str], Any],
    err_msg: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> Any:
    """Helper input numerik bersama untuk int dan float dengan validasi rentang."""
    while True:
        raw = input(f"{label}: ").strip()
        try:
            parsed = cast(raw)
        except ValueError:
            print(err_msg)
            continue
        if min_value is not None and parsed < min_value:
            print(f"Nilai minimal adalah {min_value}.")
            continue
        if max_value is not None and parsed > max_value:
            print(f"Nilai maksimal adalah {max_value}.")
            continue
        return parsed


# Minta input bilangan bulat valid dengan batas opsional.
def prompt_int(label: str, min_value: int | None = None, max_value: int | None = None) -> int:
    """Minta input bilangan bulat dengan validasi batas bawah/atas opsional."""
    return int(_prompt_num(label, int, "Masukkan angka bulat yang valid.", min_value, max_value))


# Minta input bilangan desimal valid dengan batas opsional.
def prompt_float(label: str, min_value: float | None = None, max_value: float | None = None) -> float:
    """Minta input angka desimal dengan validasi batas bawah/atas opsional."""
    return float(_prompt_num(label, float, "Masukkan angka yang valid.", min_value, max_value))


# Jalankan loop menu interaktif umum untuk setiap aplikasi hingga user memilih 0.
def run_menu_loop(title: str, options: list[tuple[str, Callable[[], None]]]) -> None:
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
        handler()
