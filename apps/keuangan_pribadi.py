from __future__ import annotations

from typing import Any

from apps import format_idr, print_header, prompt_float, prompt_int, prompt_non_empty, run_menu_loop
from fungsio_lib import (
    add_record,
    calculate_summary_stats,
    filter_by_field,
    group_by_field,
    remove_by_id,
    sort_records,
    sum_by_field,
    transform_records,
)

INITIAL_TRANSACTIONS: list[dict[str, Any]] = [
    {"id_trx": "T01", "tanggal": "2026-11-01", "tipe": "Pemasukan", "kategori": "Uang Saku", "keterangan": "Kiriman bulanan", "nominal": 2500000.0},
    {"id_trx": "T02", "tanggal": "2026-11-02", "tipe": "Pengeluaran", "kategori": "Makan", "keterangan": "Makan siang & kopi", "nominal": 45000.0},
    {"id_trx": "T03", "tanggal": "2026-11-03", "tipe": "Pengeluaran", "kategori": "Transportasi", "keterangan": "Isi bensin motor", "nominal": 60000.0},
    {"id_trx": "T04", "tanggal": "2026-11-04", "tipe": "Pemasukan", "kategori": "Freelance", "keterangan": "Desain poster acara", "nominal": 450000.0},
    {"id_trx": "T05", "tanggal": "2026-11-05", "tipe": "Pengeluaran", "kategori": "Makan", "keterangan": "Belanja bahan dapur", "nominal": 185000.0},
    {"id_trx": "T06", "tanggal": "2026-11-06", "tipe": "Pengeluaran", "kategori": "Tagihan", "keterangan": "Paket data internet", "nominal": 110000.0},
]


def _normalize_type(raw_type: str) -> str:
    clean = raw_type.strip().capitalize()
    if clean not in {"Pemasukan", "Pengeluaran"}:
        raise ValueError("Tipe transaksi harus 'Pemasukan' atau 'Pengeluaran'")
    return clean


def add_transaction(
    transactions: list[dict[str, Any]],
    tanggal: str,
    tipe: str,
    kategori: str,
    keterangan: str,
    nominal: float,
) -> list[dict[str, Any]]:
    """Append a validated income or expense record immutably."""
    if nominal <= 0:
        raise ValueError("Nominal harus lebih besar dari 0")
    clean_type = _normalize_type(tipe)
    next_id = f"T{len(transactions) + 1:02d}"
    entry = {
        "id_trx": next_id,
        "tanggal": tanggal.strip(),
        "tipe": clean_type,
        "kategori": kategori.strip().title(),
        "keterangan": keterangan.strip(),
        "nominal": float(nominal),
    }
    return add_record(transactions, entry)


def analyze_finances(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute signed cashflows, total income/expense, balance, and category breakdown."""
    signed_transactions = transform_records(
        transactions,
        lambda trx: {
            **trx,
            "arus_kas": float(trx["nominal"]) if trx["tipe"] == "Pemasukan" else -float(trx["nominal"]),
        },
    )
    incomes = filter_by_field(signed_transactions, "tipe", "Pemasukan")
    expenses = filter_by_field(signed_transactions, "tipe", "Pengeluaran")

    total_pemasukan = sum_by_field(incomes, "nominal")
    total_pengeluaran = sum_by_field(expenses, "nominal")
    saldo_bersih = sum_by_field(signed_transactions, "arus_kas")

    grouped_categories = group_by_field(signed_transactions, "kategori")
    category_totals = [
        {
            "kategori": category,
            "jumlah_transaksi": len(items),
            "total_arus_kas": sum_by_field(items, "arus_kas"),
            "total_nominal": sum_by_field(items, "nominal"),
        }
        for category, items in grouped_categories.items()
    ]

    largest_expenses = sort_records(expenses, "nominal", descending=True)
    expense_stats = calculate_summary_stats(expenses, "nominal")

    return {
        "transactions": signed_transactions,
        "incomes": incomes,
        "expenses": expenses,
        "total_pemasukan": total_pemasukan,
        "total_pengeluaran": total_pengeluaran,
        "saldo_bersih": saldo_bersih,
        "category_totals": category_totals,
        "largest_expenses": largest_expenses,
        "expense_stats": expense_stats,
    }


def _print_transactions(transactions: list[dict[str, Any]], title: str = "Daftar Transaksi") -> None:
    print(f"\n[{title}]")
    if not transactions:
        print("  (Belum ada transaksi)")
        return
    print(f"  {'ID':<4} | {'Tanggal':<10} | {'Tipe':<11} | {'Kategori':<13} | {'Keterangan':<22} | {'Nominal':>12}")
    print("  " + "-" * 84)
    for trx in transactions:
        print(
            f"  {trx['id_trx']:<4} | {trx['tanggal']:<10} | {trx['tipe']:<11} | "
            f"{trx['kategori']:<13} | {trx['keterangan'][:22]:<22} | {format_idr(trx['nominal']):>12}"
        )


def _print_financial_report(report: dict[str, Any]) -> None:
    print("\n[Ringkasan Keuangan Pribadi]")
    print(f"  Total Pemasukan   : {format_idr(report['total_pemasukan'])}")
    print(f"  Total Pengeluaran : {format_idr(report['total_pengeluaran'])}")
    print(f"  Saldo Bersih      : {format_idr(report['saldo_bersih'])}")

    stats = report["expense_stats"]
    print(
        f"  Statistik Belanja -> {int(stats['count'])} transaksi, "
        f"Rata-rata: {format_idr(stats['average'])}, Terbesar: {format_idr(stats['max'])}"
    )

    print("\n[Rekap per Kategori]")
    print(f"  {'Kategori':<16} | {'Transaksi':>9} | {'Arus Kas Bersih':>16}")
    print("  " + "-" * 48)
    for cat in report["category_totals"]:
        print(
            f"  {cat['kategori']:<16} | {cat['jumlah_transaksi']:>9} | {format_idr(cat['total_arus_kas']):>16}"
        )

    print("\n[Pengeluaran Terbesar]")
    for item in report["largest_expenses"][:3]:
        print(
            f"  #{item['rank']} {item['keterangan']} ({item['kategori']}): {format_idr(item['nominal'])}"
        )


def run_demo() -> dict[str, Any]:
    """Execute an end-to-end automated walkthrough of the Personal Finance app."""
    print_header("APP 4: KEUANGAN PRIBADI (Pemasukan, Pengeluaran, Kategori)")
    transactions = INITIAL_TRANSACTIONS
    transactions = add_transaction(transactions, "2026-11-07", "Pengeluaran", "Hiburan", "Nonton bioskop", 75000)
    transactions = add_transaction(transactions, "2026-11-08", "Pengeluaran", "Makan", "Traktir teman", 120000)
    transactions = remove_by_id(transactions, "id_trx", "T02")

    report = analyze_finances(transactions)
    _print_transactions(report["transactions"], "Semua Transaksi Terkini")
    _print_financial_report(report)
    return report


def run_cli() -> None:
    """Launch interactive terminal UI for Personal Finance management."""
    state: dict[str, Any] = {"transactions": list(INITIAL_TRANSACTIONS)}

    def show_all() -> bool:
        _print_transactions(state["transactions"])
        return True

    def add_action() -> bool:
        tanggal = prompt_non_empty("Tanggal (YYYY-MM-DD)")
        tipe = prompt_non_empty("Tipe (Pemasukan/Pengeluaran)")
        kategori = prompt_non_empty("Kategori (misal Makan, Gaji, Transportasi)")
        keterangan = prompt_non_empty("Keterangan")
        nominal = prompt_float("Nominal (Rp)", min_value=1.0)
        try:
            state["transactions"] = add_transaction(
                state["transactions"], tanggal, tipe, kategori, keterangan, nominal
            )
            print("Transaksi berhasil disimpan.")
        except ValueError as err:
            print(f"Gagal: {err}")
        return True

    def filter_type_action() -> bool:
        tipe = prompt_non_empty("Filter tipe (Pemasukan/Pengeluaran)")
        try:
            clean_type = _normalize_type(tipe)
            filtered = filter_by_field(state["transactions"], "tipe", clean_type)
            _print_transactions(filtered, f"Transaksi {clean_type}")
        except ValueError as err:
            print(f"Gagal: {err}")
        return True

    def remove_action() -> bool:
        _print_transactions(state["transactions"])
        id_trx = prompt_non_empty("ID Transaksi yang ingin dihapus").upper()
        state["transactions"] = remove_by_id(state["transactions"], "id_trx", id_trx)
        print("Transaksi dihapus jika ID ditemukan.")
        return True

    def report_action() -> bool:
        report = analyze_finances(state["transactions"])
        _print_financial_report(report)
        return True

    run_menu_loop(
        "KEUANGAN PRIBADI INTERAKTIF",
        [
            ("Lihat Semua Transaksi", show_all),
            ("Tambah Pemasukan / Pengeluaran", add_action),
            ("Filter Berdasarkan Tipe Transaksi", filter_type_action),
            ("Hapus Transaksi", remove_action),
            ("Lihat Laporan Saldo, Kategori & Statistik", report_action),
        ],
    )
