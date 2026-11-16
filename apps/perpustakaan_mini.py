from __future__ import annotations

from typing import Any

from apps import format_idr, print_header, prompt_int, prompt_non_empty, run_menu_loop
from fungsio_lib import (
    add_record,
    calculate_summary_stats,
    filter_by_field,
    group_by_field,
    remove_by_id,
    search_by_keyword,
    sum_by_field,
    transform_records,
    update_by_id,
)

# Batas pinjam bebas denda 7 hari; keterlambatan dikenakan Rp2.000/hari.
BATAS_PINJAM_HARI = 7
DENDA_PER_HARI = 2000.0

INITIAL_CATALOG: list[dict[str, Any]] = [
    {"id_buku": "B01", "judul": "Clean Code", "penulis": "Robert C. Martin", "kategori": "Teknologi", "tersedia": True},
    {"id_buku": "B02", "judul": "Structure and Interpretation of Computer Programs", "penulis": "Abelson & Sussman", "kategori": "Teknologi", "tersedia": False},
    {"id_buku": "B03", "judul": "Atomic Habits", "penulis": "James Clear", "kategori": "Pengembangan Diri", "tersedia": True},
    {"id_buku": "B04", "judul": "Filosofi Teras", "penulis": "Henry Manampiring", "kategori": "Filsafat", "tersedia": False},
    {"id_buku": "B05", "judul": "Laskar Pelangi", "penulis": "Andrea Hirata", "kategori": "Fiksi", "tersedia": True},
]

INITIAL_LOANS: list[dict[str, Any]] = [
    {"id_pinjam": "L01", "id_buku": "B02", "judul": "Structure and Interpretation of Computer Programs", "peminjam": "Raka", "durasi_hari": 10, "status": "Dipinjam"},
    {"id_pinjam": "L02", "id_buku": "B04", "judul": "Filosofi Teras", "peminjam": "Sinta", "durasi_hari": 12, "status": "Dipinjam"},
    {"id_pinjam": "L03", "id_buku": "B05", "judul": "Laskar Pelangi", "peminjam": "Taufik", "durasi_hari": 5, "status": "Dikembalikan"},
]


def borrow_book(
    catalog: list[dict[str, Any]],
    loans: list[dict[str, Any]],
    id_buku: str,
    peminjam: str,
    durasi_hari: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Catat peminjaman buku baru dan tandai stok buku tidak tersedia."""
    if durasi_hari <= 0:
        raise ValueError("Durasi pinjam minimal 1 hari")

    found_books = filter_by_field(catalog, "id_buku", id_buku)
    if not found_books:
        raise ValueError(f"Buku '{id_buku}' tidak ditemukan dalam katalog")

    book = found_books[0]
    if not book["tersedia"]:
        raise ValueError(f"Buku '{book['judul']}' sedang dipinjam")

    next_loan_id = f"L{len(loans) + 1:02d}"
    new_loan = {
        "id_pinjam": next_loan_id,
        "id_buku": book["id_buku"],
        "judul": book["judul"],
        "peminjam": peminjam.strip(),
        "durasi_hari": durasi_hari,
        "status": "Dipinjam",
    }
    # Tambah transaksi pinjam via add_record, lalu kunci status katalog via update_by_id.
    updated_loans = add_record(loans, new_loan)
    updated_catalog = update_by_id(catalog, "id_buku", id_buku, {"tersedia": False})
    return updated_catalog, updated_loans


def return_book(
    catalog: list[dict[str, Any]],
    loans: list[dict[str, Any]],
    id_pinjam: str,
    actual_days: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Tandai pinjaman selesai dan pulihkan ketersediaan buku di katalog."""
    matched_loans = filter_by_field(loans, "id_pinjam", id_pinjam)
    if not matched_loans:
        raise ValueError(f"ID peminjaman '{id_pinjam}' tidak ditemukan")

    loan = matched_loans[0]
    updates: dict[str, Any] = {"status": "Dikembalikan"}
    if actual_days is not None and actual_days > 0:
        updates["durasi_hari"] = actual_days

    updated_loans = update_by_id(loans, "id_pinjam", id_pinjam, updates)
    updated_catalog = update_by_id(catalog, "id_buku", loan["id_buku"], {"tersedia": True})
    return updated_catalog, updated_loans


def calculate_fines(loans: list[dict[str, Any]]) -> dict[str, Any]:
    """Hitung hari telat, denda per pinjaman, total denda, dan statistik denda."""
    # Hitung selisih hari melewati batas 7 hari, minimal 0 agar pinjaman tepat waktu tidak minus.
    loans_with_fines = transform_records(
        loans,
        lambda loan: {
            **loan,
            "hari_terlambat": max(0, int(loan["durasi_hari"]) - BATAS_PINJAM_HARI),
            "denda": float(max(0, int(loan["durasi_hari"]) - BATAS_PINJAM_HARI)) * DENDA_PER_HARI,
        },
    )
    total_denda = sum_by_field(loans_with_fines, "denda")
    fine_stats = calculate_summary_stats(loans_with_fines, "denda")
    return {
        "loans": loans_with_fines,
        "total_denda": total_denda,
        "fine_stats": fine_stats,
    }


def _print_catalog(catalog: list[dict[str, Any]], title: str = "Katalog Buku") -> None:
    """Tampilkan daftar buku katalog beserta status ketersediaannya."""
    print(f"\n[{title}]")
    if not catalog:
        print("  (Tidak ada buku)")
        return
    print(f"  {'ID':<5} | {'Judul Buku':<46} | {'Kategori':<18} | {'Status':<10}")
    print("  " + "-" * 86)
    for book in catalog:
        status = "Tersedia" if book["tersedia"] else "Dipinjam"
        print(f"  {book['id_buku']:<5} | {book['judul']:<46} | {book['kategori']:<18} | {status:<10}")


def _print_loans_with_fines(fine_report: dict[str, Any], title: str = "Daftar Peminjaman & Denda") -> None:
    """Cetak tabel peminjaman beserta perhitungan telat, denda, dan ringkasan statistik."""
    print(f"\n[{title}]")
    loans = fine_report["loans"]
    if not loans:
        print("  (Tidak ada data peminjaman)")
        return
    print(
        f"  {'ID':<5} | {'Peminjam':<10} | {'Judul':<34} | {'Hari':>4} | {'Telat':>5} | {'Denda':>10} | {'Status':<12}"
    )
    print("  " + "-" * 94)
    for loan in loans:
        short_title = loan["judul"][:32] + ".." if len(loan["judul"]) > 34 else loan["judul"]
        print(
            f"  {loan['id_pinjam']:<5} | {loan['peminjam']:<10} | {short_title:<34} | "
            f"{loan['durasi_hari']:>4} | {loan['hari_terlambat']:>5} | "
            f"{format_idr(loan['denda']):>10} | {loan['status']:<12}"
        )
    print("  " + "-" * 94)
    stats = fine_report["fine_stats"]
    print(
        f"  Total Denda: {format_idr(fine_report['total_denda'])} | "
        f"Rata-rata: {format_idr(stats['average'])} | Maksimal: {format_idr(stats['max'])}"
    )


def run_demo() -> dict[str, Any]:
    """Jalankan skenario demo otomatis App 3 untuk verifikasi dan pengujian."""
    print_header("APP 3: PERPUSTAKAAN MINI (Katalog, Peminjaman, Denda)")
    catalog = INITIAL_CATALOG
    loans = INITIAL_LOANS

    available_books = filter_by_field(catalog, "tersedia", True)
    _print_catalog(available_books, "Buku Tersedia untuk Dipinjam")

    # Kelompokkan buku per kategori memakai group_by_field.
    grouped_catalog = group_by_field(catalog, "kategori")
    print("\n[Rekap Jumlah Judul per Kategori]")
    for category, items in grouped_catalog.items():
        print(f"  - {category}: {len(items)} judul")

    search_code = search_by_keyword(catalog, "judul", "code")
    _print_catalog(search_code, "Pencarian Judul: 'code'")

    # Simulasi pinjam B01, kembalikan L01, dan hapus log lama L03 via remove_by_id.
    catalog, loans = borrow_book(catalog, loans, "B01", "Nadia", 9)
    catalog, loans = return_book(catalog, loans, "L01", actual_days=10)
    loans = remove_by_id(loans, "id_pinjam", "L03")

    fine_report = calculate_fines(loans)
    _print_loans_with_fines(fine_report, "Laporan Peminjaman & Denda (Batas 7 Hari, Rp2.000/hari)")
    return {
        "catalog": catalog,
        "available_books": available_books,
        "grouped_catalog": grouped_catalog,
        "search_results": search_code,
        "fine_report": fine_report,
    }


def run_cli() -> None:
    """Jalankan antarmuka terminal interaktif untuk Perpustakaan Mini."""
    state: dict[str, Any] = {
        "catalog": list(INITIAL_CATALOG),
        "loans": list(INITIAL_LOANS),
    }

    def show_catalog() -> bool:
        _print_catalog(state["catalog"])
        grouped = group_by_field(state["catalog"], "kategori")
        print("\n  Ringkasan per Kategori:")
        for category, items in grouped.items():
            print(f"   - {category}: {len(items)} buku")
        return True

    def filter_available_or_search() -> bool:
        print("  1. Tampilkan Buku Tersedia  2. Cari Judul Buku")
        mode = prompt_int("Pilih mode", min_value=1, max_value=2)
        if mode == 1:
            results = filter_by_field(state["catalog"], "tersedia", True)
            _print_catalog(results, "Buku Tersedia")
        else:
            keyword = prompt_non_empty("Kata kunci judul buku")
            results = search_by_keyword(state["catalog"], "judul", keyword)
            _print_catalog(results, f"Hasil Cari '{keyword}'")
        return True

    def borrow_action() -> bool:
        _print_catalog(filter_by_field(state["catalog"], "tersedia", True), "Buku Tersedia")
        id_buku = prompt_non_empty("ID Buku yang dipinjam").upper()
        peminjam = prompt_non_empty("Nama peminjam")
        durasi = prompt_int("Durasi pinjam (hari)", min_value=1)
        try:
            state["catalog"], state["loans"] = borrow_book(
                state["catalog"], state["loans"], id_buku, peminjam, durasi
            )
            print("Peminjaman berhasil dicatat.")
        except ValueError as err:
            print(f"Gagal: {err}")
        return True

    def return_action() -> bool:
        _print_loans_with_fines(calculate_fines(state["loans"]))
        id_pinjam = prompt_non_empty("ID Pinjam yang dikembalikan").upper()
        hari = prompt_int("Total hari pinjam aktual", min_value=1)
        try:
            state["catalog"], state["loans"] = return_book(
                state["catalog"], state["loans"], id_pinjam, actual_days=hari
            )
            print("Buku berhasil dikembalikan.")
        except ValueError as err:
            print(f"Gagal: {err}")
        return True

    def delete_loan_action() -> bool:
        _print_loans_with_fines(calculate_fines(state["loans"]))
        id_pinjam = prompt_non_empty("ID Pinjam yang ingin dihapus").upper()
        state["loans"] = remove_by_id(state["loans"], "id_pinjam", id_pinjam)
        print("Data peminjaman dihapus jika ID ditemukan.")
        return True

    def show_fines_action() -> bool:
        _print_loans_with_fines(calculate_fines(state["loans"]))
        return True

    run_menu_loop(
        "PERPUSTAKAAN MINI INTERAKTIF",
        [
            ("Lihat Katalog & Kategori", show_catalog),
            ("Filter Buku Tersedia / Cari Judul", filter_available_or_search),
            ("Pinjam Buku", borrow_action),
            ("Kembalikan Buku", return_action),
            ("Hapus Log Peminjaman", delete_loan_action),
            ("Lihat Laporan Peminjaman & Denda", show_fines_action),
        ],
    )
