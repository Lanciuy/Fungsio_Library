from __future__ import annotations

from typing import Any

from apps import print_header, prompt_int, prompt_non_empty, run_menu_loop
from fungsio_lib import (
    add_record,
    filter_by_field,
    group_by_field,
    search_by_keyword,
    sort_records,
    sum_by_field,
    transform_records,
    update_by_id,
)

# Bobot poin per status kehadiran dan ambang minimal kelayakan ikut UAS (75%).
STATUS_POINTS: dict[str, float] = {
    "Hadir": 1.0,
    "Izin": 0.5,
    "Sakit": 0.5,
    "Alfa": 0.0,
}
MIN_UAS_PERCENTAGE = 75.0

INITIAL_LOGS: list[dict[str, Any]] = [
    {"id_log": "P01", "nim": "230101", "nama": "Andi Pratama", "pertemuan": 1, "status": "Hadir"},
    {"id_log": "P02", "nim": "230101", "nama": "Andi Pratama", "pertemuan": 2, "status": "Hadir"},
    {"id_log": "P03", "nim": "230101", "nama": "Andi Pratama", "pertemuan": 3, "status": "Hadir"},
    {"id_log": "P04", "nim": "230101", "nama": "Andi Pratama", "pertemuan": 4, "status": "Izin"},
    {"id_log": "P05", "nim": "230102", "nama": "Budi Santoso", "pertemuan": 1, "status": "Hadir"},
    {"id_log": "P06", "nim": "230102", "nama": "Budi Santoso", "pertemuan": 2, "status": "Alfa"},
    {"id_log": "P07", "nim": "230102", "nama": "Budi Santoso", "pertemuan": 3, "status": "Alfa"},
    {"id_log": "P08", "nim": "230102", "nama": "Budi Santoso", "pertemuan": 4, "status": "Sakit"},
    {"id_log": "P09", "nim": "230103", "nama": "Citra Lestari", "pertemuan": 1, "status": "Hadir"},
    {"id_log": "P10", "nim": "230103", "nama": "Citra Lestari", "pertemuan": 2, "status": "Hadir"},
    {"id_log": "P11", "nim": "230103", "nama": "Citra Lestari", "pertemuan": 3, "status": "Hadir"},
    {"id_log": "P12", "nim": "230103", "nama": "Citra Lestari", "pertemuan": 4, "status": "Hadir"},
]


def _normalize_status(raw_status: str) -> str:
    """Validasi dan seragamkan penulisan status kehadiran."""
    formatted = raw_status.strip().capitalize()
    if formatted not in STATUS_POINTS:
        valid = ", ".join(STATUS_POINTS.keys())
        raise ValueError(f"Status '{raw_status}' tidak valid. Pilih: {valid}")
    return formatted


def record_attendance(
    logs: list[dict[str, Any]],
    nim: str,
    nama: str,
    pertemuan: int,
    status: str,
) -> list[dict[str, Any]]:
    """Catat entri presensi baru secara immutable via add_record."""
    clean_status = _normalize_status(status)
    next_id = f"P{len(logs) + 1:02d}"
    entry = {
        "id_log": next_id,
        "nim": nim.strip(),
        "nama": nama.strip(),
        "pertemuan": pertemuan,
        "status": clean_status,
    }
    return add_record(logs, entry)


def build_student_recaps(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rekap log presensi per mahasiswa: hitung % hadir, kelayakan UAS, dan peringkat."""
    # Beri bobot poin pada tiap log presensi lewat transform_records.
    weighted_logs = transform_records(
        logs,
        lambda item: {
            **item,
            "poin": STATUS_POINTS.get(item["status"], 0.0),
        },
    )
    # Kelompokkan seluruh log berdasarkan NIM mahasiswa memakai group_by_field.
    grouped_by_nim = group_by_field(weighted_logs, "nim")

    raw_recaps: list[dict[str, Any]] = []
    for nim, student_logs in grouped_by_nim.items():
        total_pertemuan = len(student_logs)
        hadir_count = len(filter_by_field(student_logs, "status", "Hadir"))
        total_poin = sum_by_field(student_logs, "poin")
        raw_recaps.append(
            {
                "nim": nim,
                "nama": student_logs[0]["nama"],
                "total_pertemuan": total_pertemuan,
                "jumlah_hadir": hadir_count,
                "total_poin": total_poin,
            }
        )

    # Hitung persentase kehadiran dan tentukan status kelayakan UAS (>= 75%).
    enriched_recaps = transform_records(
        raw_recaps,
        lambda rec: {
            **rec,
            "persentase": round((rec["total_poin"] / rec["total_pertemuan"]) * 100, 1)
            if rec["total_pertemuan"] > 0
            else 0.0,
        },
    )
    final_recaps = transform_records(
        enriched_recaps,
        lambda rec: {
            **rec,
            "kelayakan_uas": "Layak UAS" if rec["persentase"] >= MIN_UAS_PERCENTAGE else "Tidak Layak",
        },
    )
    # Urutkan mahasiswa dari persentase kehadiran tertinggi via sort_records.
    return sort_records(final_recaps, "persentase", descending=True)


def _print_logs(logs: list[dict[str, Any]], title: str = "Log Presensi Kelas") -> None:
    """Cetak daftar log presensi mentah per pertemuan."""
    print(f"\n[{title}]")
    if not logs:
        print("  (Belum ada data log presensi)")
        return
    print(f"  {'ID':<5} | {'NIM':<8} | {'Nama Mahasiswa':<18} | {'Pert':>4} | {'Status':<8}")
    print("  " + "-" * 55)
    for log in logs:
        print(
            f"  {log['id_log']:<5} | {log['nim']:<8} | {log['nama']:<18} | "
            f"{log['pertemuan']:>4} | {log['status']:<8}"
        )


def _print_recaps(recaps: list[dict[str, Any]], title: str = "Rekap Kehadiran per Mahasiswa") -> None:
    """Cetak tabel rekap kehadiran, persentase, dan status kelayakan UAS."""
    print(f"\n[{title}]")
    if not recaps:
        print("  (Belum ada rekap mahasiswa)")
        return
    print(
        f"  {'No':<3} | {'NIM':<8} | {'Nama Mahasiswa':<18} | {'Pert':>4} | "
        f"{'Hadir':>5} | {'% Hadir':>7} | {'Status UAS':<12}"
    )
    print("  " + "-" * 72)
    for rec in recaps:
        rank_display = rec.get("rank", "-")
        print(
            f"  {rank_display:<3} | {rec['nim']:<8} | {rec['nama']:<18} | {rec['total_pertemuan']:>4} | "
            f"{rec['jumlah_hadir']:>5} | {rec['persentase']:>6.1f}% | {rec['kelayakan_uas']:<12}"
        )


def run_demo() -> dict[str, Any]:
    """Jalankan skenario demo otomatis App 2 untuk verifikasi dan pengujian."""
    print_header("APP 2: PRESENSI KELAS (Kehadiran & Rekap per Mahasiswa)")
    logs = INITIAL_LOGS
    logs = record_attendance(logs, "230104", "Dewi Anggraini", 1, "Hadir")
    logs = record_attendance(logs, "230104", "Dewi Anggraini", 2, "Hadir")
    # Koreksi log P07 dari Alfa menjadi Izin memakai update_by_id.
    logs = update_by_id(logs, "id_log", "P07", {"status": "Izin"})

    alfa_logs = filter_by_field(logs, "status", "Alfa")
    _print_logs(alfa_logs, "Filter Status Kehadiran: Alfa")

    recaps = build_student_recaps(logs)
    _print_recaps(recaps, "Rekap Kehadiran Semua Mahasiswa (Urut % Tertinggi)")

    search_citra = search_by_keyword(recaps, "nama", "citra")
    _print_recaps(search_citra, "Pencarian Rekap Mahasiswa: 'citra'")
    return {
        "logs": logs,
        "alfa_logs": alfa_logs,
        "recaps": recaps,
        "search_results": search_citra,
    }


def run_cli() -> None:
    """Jalankan antarmuka terminal interaktif untuk Presensi Kelas."""
    state: dict[str, Any] = {"logs": list(INITIAL_LOGS)}

    def show_all_logs() -> bool:
        _print_logs(state["logs"])
        return True

    def add_log_action() -> bool:
        nim = prompt_non_empty("NIM Mahasiswa")
        nama = prompt_non_empty("Nama Mahasiswa")
        pertemuan = prompt_int("Pertemuan ke-", min_value=1, max_value=16)
        status = prompt_non_empty("Status (Hadir/Izin/Sakit/Alfa)")
        try:
            state["logs"] = record_attendance(state["logs"], nim, nama, pertemuan, status)
            print("Presensi berhasil dicatat.")
        except ValueError as err:
            print(f"Gagal: {err}")
        return True

    def update_log_action() -> bool:
        _print_logs(state["logs"])
        id_log = prompt_non_empty("Masukkan ID Log (misal P07)").upper()
        status = prompt_non_empty("Status baru (Hadir/Izin/Sakit/Alfa)")
        try:
            clean_status = _normalize_status(status)
            state["logs"] = update_by_id(state["logs"], "id_log", id_log, {"status": clean_status})
            print("Status presensi diperbarui jika ID ditemukan.")
        except ValueError as err:
            print(f"Gagal: {err}")
        return True

    def filter_logs_action() -> bool:
        status = prompt_non_empty("Filter status (Hadir/Izin/Sakit/Alfa)")
        try:
            clean_status = _normalize_status(status)
            filtered = filter_by_field(state["logs"], "status", clean_status)
            _print_logs(filtered, f"Log Status: {clean_status}")
        except ValueError as err:
            print(f"Gagal: {err}")
        return True

    def show_recaps_action() -> bool:
        recaps = build_student_recaps(state["logs"])
        _print_recaps(recaps)
        return True

    def search_recap_action() -> bool:
        keyword = prompt_non_empty("Masukkan kata kunci nama mahasiswa")
        recaps = build_student_recaps(state["logs"])
        matches = search_by_keyword(recaps, "nama", keyword)
        _print_recaps(matches, f"Hasil Cari '{keyword}'")
        return True

    run_menu_loop(
        "PRESENSI KELAS INTERAKTIF",
        [
            ("Lihat Semua Log Kehadiran", show_all_logs),
            ("Catat Kehadiran Baru", add_log_action),
            ("Koreksi Status Kehadiran", update_log_action),
            ("Filter Log Berdasarkan Status", filter_logs_action),
            ("Lihat Rekap Kehadiran per Mahasiswa", show_recaps_action),
            ("Cari Rekap Mahasiswa", search_recap_action),
        ],
    )
