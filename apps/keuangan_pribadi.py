from __future__ import annotations

from typing import Any

from apps import (
    format_idr,
    next_prefixed_id,
    print_header,
    prompt_float,
    prompt_int,
    prompt_non_empty,
    run_menu_loop,
)
from fungsio_lib import (
    add_record,
    calculate_summary_stats,
    filter_by_field,
    group_by_field,
    remove_by_id,
    search_by_keyword,
    sort_records,
    sum_by_field,
    transform_records,
    update_by_id,
)

INITIAL_TRANSACTIONS: list[dict[str, Any]] = [
    {"id_trx": "T01", "tanggal": "2026-11-01", "tipe": "Pemasukan", "kategori": "Uang Saku", "keterangan": "Kiriman bulanan", "nominal": 2500000.0},
    {"id_trx": "T02", "tanggal": "2026-11-02", "tipe": "Pengeluaran", "kategori": "Makan", "keterangan": "Makan siang & kopi", "nominal": 45000.0},
    {"id_trx": "T03", "tanggal": "2026-11-03", "tipe": "Pengeluaran", "kategori": "Transportasi", "keterangan": "Isi bensin motor", "nominal": 60000.0},
    {"id_trx": "T04", "tanggal": "2026-11-04", "tipe": "Pemasukan", "kategori": "Freelance", "keterangan": "Desain poster acara", "nominal": 450000.0},
    {"id_trx": "T05", "tanggal": "2026-11-05", "tipe": "Pengeluaran", "kategori": "Makan", "keterangan": "Belanja bahan dapur", "nominal": 185000.0},
    {"id_trx": "T06", "tanggal": "2026-11-06", "tipe": "Pengeluaran", "kategori": "Tagihan", "keterangan": "Paket data internet", "nominal": 110000.0},
]


# Validasi dan seragamkan tipe transaksi (Pemasukan atau Pengeluaran).
def _normalize_type(raw_type: str) -> str:
    """Validasi dan seragamkan tipe transaksi (Pemasukan atau Pengeluaran)."""
    clean = raw_type.strip().capitalize()
    if clean not in {"Pemasukan", "Pengeluaran"}:
        raise ValueError("Tipe transaksi harus 'Pemasukan' atau 'Pengeluaran'")
    return clean


# Tambah transaksi baru secara immutable via add_record dengan ID otomatis bebas bentrok.
def add_transaction(
    transactions: list[dict[str, Any]],
    tanggal: str,
    tipe: str,
    kategori: str,
    keterangan: str,
    nominal: float,
) -> list[dict[str, Any]]:
    """Tambah transaksi pemasukan/pengeluaran baru secara immutable via add_record."""
    if nominal <= 0:
        raise ValueError("Nominal harus lebih besar dari 0")
    clean_type = _normalize_type(tipe)
    entry = {
        "id_trx": next_prefixed_id(transactions, "id_trx", "T"),
        "tanggal": tanggal.strip(),
        "tipe": clean_type,
        "kategori": kategori.strip().title(),
        "keterangan": keterangan.strip(),
        "nominal": float(nominal),
    }
    return add_record(transactions, entry)


# Validasi ID & field perubahan lalu perbarui transaksi via update_by_id.
def update_transaction(
    transactions: list[dict[str, Any]],
    id_trx: str,
    updates: dict[str, Any],
) -> list[dict[str, Any]]:
    """Perbarui data transaksi berdasarkan ID dengan validasi tipe dan nominal."""
    clean_id = id_trx.strip().upper()
    if not filter_by_field(transactions, "id_trx", clean_id):
        raise ValueError(f"ID Transaksi '{id_trx}' tidak ditemukan")

    clean_updates: dict[str, Any] = {}
    if "tanggal" in updates:
        clean_updates["tanggal"] = str(updates["tanggal"]).strip()
    if "tipe" in updates:
        clean_updates["tipe"] = _normalize_type(str(updates["tipe"]))
    if "kategori" in updates:
        clean_updates["kategori"] = str(updates["kategori"]).strip().title()
    if "keterangan" in updates:
        clean_updates["keterangan"] = str(updates["keterangan"]).strip()
    if "nominal" in updates:
        val = float(updates["nominal"])
        if val <= 0:
            raise ValueError("Nominal harus lebih besar dari 0")
        clean_updates["nominal"] = val

    return update_by_id(transactions, "id_trx", clean_id, clean_updates)


# Validasi ID transaksi lalu hapus transaksi via remove_by_id.
def delete_transaction(transactions: list[dict[str, Any]], id_trx: str) -> list[dict[str, Any]]:
    """Hapus transaksi berdasarkan ID setelah memvalidasi keberadaannya."""
    clean_id = id_trx.strip().upper()
    if not filter_by_field(transactions, "id_trx", clean_id):
        raise ValueError(f"ID Transaksi '{id_trx}' tidak ditemukan")
    return remove_by_id(transactions, "id_trx", clean_id)


# Alur analisis: transform (+ / - arus_kas) -> filter (masuk/keluar) -> sum -> group (kategori) -> sort & stats.
def analyze_finances(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Hitung arus kas bertanda, saldo bersih, rekap kategori, dan statistik pengeluaran."""
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


# Cetak daftar seluruh transaksi pemasukan dan pengeluaran.
def _print_transactions(transactions: list[dict[str, Any]], title: str = "Daftar Transaksi") -> None:
    """Cetak daftar transaksi pemasukan dan pengeluaran."""
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


# Cetak ringkasan 1 baris total pemasukan, pengeluaran, dan saldo bersih.
def _print_balance_summary(report: dict[str, Any]) -> None:
    """Cetak ringkasan cepat pemasukan, pengeluaran, dan saldo bersih."""
    print(
        f"  Ringkasan -> Masuk: {format_idr(report['total_pemasukan'])} | "
        f"Keluar: {format_idr(report['total_pengeluaran'])} | "
        f"Saldo Bersih: {format_idr(report['saldo_bersih'])}"
    )


# Cetak laporan lengkap keuangan: saldo, statistik belanja, rekap kategori, dan top 3 pengeluaran.
def _print_financial_report(report: dict[str, Any]) -> None:
    """Cetak ringkasan saldo bersih, rekap kategori, dan 3 pengeluaran terbesar."""
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


# Simulasi otomatis fitur Keuangan Pribadi untuk mode demo dan pengujian.
def run_demo() -> dict[str, Any]:
    """Jalankan skenario demo otomatis App 4 untuk verifikasi dan pengujian."""
    print_header("APP 4: KEUANGAN PRIBADI (Pemasukan, Pengeluaran, Kategori)")
    transactions = INITIAL_TRANSACTIONS
    transactions = add_transaction(transactions, "2026-11-07", "Pengeluaran", "Hiburan", "Nonton bioskop", 75000)
    transactions = add_transaction(transactions, "2026-11-08", "Pengeluaran", "Makan", "Traktir teman", 120000)
    transactions = delete_transaction(transactions, "T02")

    report = analyze_finances(transactions)
    _print_transactions(report["transactions"], "Semua Transaksi Terkini")
    _print_financial_report(report)
    return report


# Jalankan menu CLI interaktif Keuangan Pribadi.
def run_cli() -> None:
    """Jalankan antarmuka terminal interaktif untuk Keuangan Pribadi."""
    state: dict[str, Any] = {"transactions": list(INITIAL_TRANSACTIONS)}

    # Menu 1: Tampilkan seluruh daftar transaksi beserta ringkasan saldo terkini.
    def show_all() -> None:
        _print_transactions(state["transactions"])
        _print_balance_summary(analyze_finances(state["transactions"]))

    # Menu 2: Input transaksi pemasukan/pengeluaran baru via add_transaction dan perbarui ringkasan saldo.
    def add_action() -> None:
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
            _print_balance_summary(analyze_finances(state["transactions"]))
        except ValueError as err:
            print(f"Gagal: {err}")

    # Menu 3: Ubah field transaksi (tipe/kategori/keterangan/nominal) via update_transaction.
    def edit_action() -> None:
        _print_transactions(state["transactions"])
        if not state["transactions"]:
            return
        id_trx = prompt_non_empty("ID Transaksi yang ingin diubah").upper()
        if not filter_by_field(state["transactions"], "id_trx", id_trx):
            print(f"Gagal: ID Transaksi '{id_trx}' tidak ditemukan.")
            return
        print("  Field: 1. Tipe  2. Kategori  3. Keterangan  4. Nominal")
        field_choice = prompt_int("Pilih field yang diubah", min_value=1, max_value=4)
        try:
            if field_choice == 1:
                updates: dict[str, Any] = {"tipe": prompt_non_empty("Tipe baru (Pemasukan/Pengeluaran)")}
            elif field_choice == 2:
                updates = {"kategori": prompt_non_empty("Kategori baru")}
            elif field_choice == 3:
                updates = {"keterangan": prompt_non_empty("Keterangan baru")}
            else:
                updates = {"nominal": prompt_float("Nominal baru (Rp)", min_value=1.0)}
            state["transactions"] = update_transaction(state["transactions"], id_trx, updates)
            print(f"Transaksi '{id_trx}' berhasil diperbarui.")
            _print_balance_summary(analyze_finances(state["transactions"]))
        except ValueError as err:
            print(f"Gagal: {err}")

    # Menu 4: Saring transaksi berdasarkan tipe/kategori (filter_by_field) atau cari keterangan (search_by_keyword).
    def filter_and_search_action() -> None:
        print("  1. Filter Tipe (Pemasukan/Pengeluaran)  2. Filter Kategori  3. Cari Keterangan")
        mode = prompt_int("Pilih mode", min_value=1, max_value=3)
        try:
            if mode == 1:
                clean_type = _normalize_type(prompt_non_empty("Tipe (Pemasukan/Pengeluaran)"))
                filtered = filter_by_field(state["transactions"], "tipe", clean_type)
                _print_transactions(filtered, f"Transaksi {clean_type}")
            elif mode == 2:
                kategori = prompt_non_empty("Nama kategori").title()
                filtered = filter_by_field(state["transactions"], "kategori", kategori)
                _print_transactions(filtered, f"Kategori: {kategori}")
            else:
                keyword = prompt_non_empty("Kata kunci keterangan")
                matched = search_by_keyword(state["transactions"], "keterangan", keyword)
                _print_transactions(matched, f"Hasil Cari '{keyword}'")
        except ValueError as err:
            print(f"Gagal: {err}")

    # Menu 5: Hapus transaksi via delete_transaction dan tampilkan ringkasan saldo terbaru.
    def remove_action() -> None:
        _print_transactions(state["transactions"])
        if not state["transactions"]:
            return
        id_trx = prompt_non_empty("ID Transaksi yang ingin dihapus").upper()
        try:
            state["transactions"] = delete_transaction(state["transactions"], id_trx)
            print(f"Transaksi '{id_trx}' berhasil dihapus.")
            _print_balance_summary(analyze_finances(state["transactions"]))
        except ValueError as err:
            print(f"Gagal: {err}")

    # Menu 6: Tampilkan laporan lengkap arus kas, rekap per kategori, dan pengeluaran terbesar.
    def report_action() -> None:
        report = analyze_finances(state["transactions"])
        _print_financial_report(report)

    run_menu_loop(
        "KEUANGAN PRIBADI INTERAKTIF",
        [
            ("Lihat Semua Transaksi", show_all),
            ("Tambah Pemasukan / Pengeluaran", add_action),
            ("Edit Transaksi", edit_action),
            ("Filter Tipe/Kategori & Cari Transaksi", filter_and_search_action),
            ("Hapus Transaksi", remove_action),
            ("Lihat Laporan Saldo, Kategori & Statistik", report_action),
        ],
    )
