from __future__ import annotations

import argparse
import ast
from pathlib import Path

import fungsio_lib
from apps import (
    kasir_kantin,
    keuangan_pribadi,
    nilai_mahasiswa,
    perpustakaan_mini,
    presensi_kelas,
    print_header,
    prompt_int,
)

# Daftar 5 aplikasi CLI yang terdaftar di portal utama.
APP_REGISTRY = [
    ("kasir_kantin", "Kasir Kantin (Menu, Keranjang, Total Belanja)", kasir_kantin),
    ("presensi_kelas", "Presensi Kelas (Kehadiran & Rekap Mahasiswa)", presensi_kelas),
    ("perpustakaan_mini", "Perpustakaan Mini (Katalog, Peminjaman, Denda)", perpustakaan_mini),
    ("keuangan_pribadi", "Keuangan Pribadi (Pemasukan, Pengeluaran, Kategori)", keuangan_pribadi),
    ("nilai_mahasiswa", "Nilai Mahasiswa (Komponen Nilai, Nilai Akhir, Peringkat)", nilai_mahasiswa),
]


# Pindai AST tiap file apps/*.py untuk memetakan fungsi fungsio_lib mana saja yang dipanggil.
def inspect_library_usage() -> dict[str, set[str]]:
    """Audit pemanggilan 10 fungsi fungsio_lib di tiap file apps/ lewat AST."""
    apps_dir = Path(__file__).resolve().parent / "apps"
    lib_functions = set(fungsio_lib.__all__)
    usage: dict[str, set[str]] = {fn_name: set() for fn_name in lib_functions}

    for module_key, _, _ in APP_REGISTRY:
        source_path = apps_dir / f"{module_key}.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                called_name = None
                if isinstance(node.func, ast.Name):
                    called_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    called_name = node.func.attr
                if called_name in usage:
                    usage[called_name].add(module_key)
    return usage


# Cetak tabel audit pemakaian 10 fungsi library di 5 aplikasi dari hasil AST.
def print_usage_matrix() -> None:
    """Cetak tabel verifikasi pemakaian 10 fungsi library di 5 aplikasi."""
    print_header("VERIFIKASI MATRIKS PEMAKAIAN 10 FUNGSI DI 5 APLIKASI")
    usage = inspect_library_usage()
    short_headers = ["Kasir", "Presensi", "Perpus", "Keuangan", "Nilai"]
    app_keys = [key for key, _, _ in APP_REGISTRY]

    header_row = f"  {'No':<3} | {'Fungsi Library':<24} | " + " | ".join(f"{h:^8}" for h in short_headers) + " | Total"
    print(header_row)
    print("  " + "-" * (len(header_row) - 2))

    for idx, fn_name in enumerate(fungsio_lib.__all__, start=1):
        used_apps = usage[fn_name]
        marks = " | ".join(f"{'YES' if k in used_apps else '-':^8}" for k in app_keys)
        print(f"  {idx:<3} | {fn_name:<24} | {marks} | {len(used_apps)} App")


# Jalankan demo otomatis 5 aplikasi secara berurutan lalu tampilkan matriks audit AST.
def run_all_demos() -> None:
    """Jalankan demo otomatis ke-5 aplikasi lalu tampilkan matriks pemakaian fungsi."""
    for _, _, module in APP_REGISTRY:
        module.run_demo()
    print_usage_matrix()


# Portal menu utama CLI untuk memilih dan menjalankan salah satu dari 5 aplikasi.
def run_interactive_launcher() -> None:
    """Tampilkan portal menu interaktif untuk memilih satu dari 5 aplikasi CLI."""
    while True:
        print_header("PORTAL UTAMA: 1 LIBRARY (10 FUNGSI) & 5 APLIKASI CLI")
        for idx, (_, label, _) in enumerate(APP_REGISTRY, start=1):
            print(f"  {idx}. {label}")
        print("  0. Keluar")

        choice = prompt_int("Pilih menu", min_value=0, max_value=len(APP_REGISTRY))
        if choice == 0:
            print("Terima kasih telah menggunakan Fungsio CLI.")
            return
        _, _, selected_module = APP_REGISTRY[choice - 1]
        selected_module.run_cli()


# Titik masuk program: jalankan --demo bila diminta argumen CLI, selain itu buka portal interaktif.
def main() -> None:
    """Entrypoint CLI: jalankan --demo untuk demo otomatis atau menu interaktif."""
    parser = argparse.ArgumentParser(
        description="Launcher untuk Library Fungsional (10 Fungsi) & 5 Aplikasi CLI"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Jalankan demo otomatis seluruh 5 aplikasi beserta matriks verifikasi fungsi.",
    )
    args = parser.parse_args()
    if args.demo:
        run_all_demos()
    else:
        run_interactive_launcher()


if __name__ == "__main__":
    main()
