from __future__ import annotations

from typing import Any

from apps import next_prefixed_id, print_header, prompt_int, prompt_non_empty, run_menu_loop
from fungsio_lib import (
    add_record,
    filter_by_field,
    group_by_field,
    remove_by_id,
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


# Validasi dan seragamkan input status (Hadir/Izin/Sakit/Alfa).
def _normalize_status(raw_status: str) -> str:
    """Validasi dan seragamkan penulisan status kehadiran."""
    formatted = raw_status.strip().capitalize()
    if formatted not in STATUS_POINTS:
        valid = ", ".join(STATUS_POINTS.keys())
        raise ValueError(f"Status '{raw_status}' tidak valid. Pilih: {valid}")
    return formatted


# Catat presensi baru via add_record, atau perbarui status via update_by_id jika (NIM, pertemuan) sudah ada.
def record_attendance(
    logs: list[dict[str, Any]],
    nim: str,
    nama: str,
    pertemuan: int,
    status: str,
) -> list[dict[str, Any]]:
    """Catat presensi baru atau perbarui otomatis jika (NIM, pertemuan) sudah tercatat."""
    clean_nim = nim.strip()
    if not clean_nim:
        raise ValueError("NIM tidak boleh kosong")
    if pertemuan <= 0:
        raise ValueError("Pertemuan harus lebih dari 0")

    clean_status = _normalize_status(status)
    existing_student = filter_by_field(logs, "nim", clean_nim)
    resolved_name = existing_student[0]["nama"] if existing_student else nama.strip()
    if not resolved_name:
        raise ValueError("Nama mahasiswa tidak boleh kosong")

    existing_meeting = filter_by_field(existing_student, "pertemuan", pertemuan)
    if existing_meeting:
        return update_by_id(logs, "id_log", existing_meeting[0]["id_log"], {"status": clean_status})

    entry = {
        "id_log": next_prefixed_id(logs, "id_log", "P"),
        "nim": clean_nim,
        "nama": resolved_name,
        "pertemuan": pertemuan,
        "status": clean_status,
    }
    return add_record(logs, entry)


# Validasi ID log lalu hapus entri presensi via remove_by_id.
def delete_attendance_log(logs: list[dict[str, Any]], id_log: str) -> list[dict[str, Any]]:
    """Hapus log presensi berdasarkan ID setelah memvalidasi keberadaannya."""
    clean_id = id_log.strip().upper()
    if not filter_by_field(logs, "id_log", clean_id):
        raise ValueError(f"ID Log '{id_log}' tidak ditemukan")
    return remove_by_id(logs, "id_log", clean_id)


# Alur rekap: transform_records (bobot) -> group_by_field (NIM) -> sum_by_field (poin) -> transform (% & UAS) -> sort.
def build_student_recaps(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rekap log presensi per mahasiswa: hitung % hadir, kelayakan UAS, dan peringkat."""
    weighted_logs = transform_records(
        logs,
        lambda item: {
            **item,
            "poin": STATUS_POINTS.get(item["status"], 0.0),
        },
    )
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

    final_recaps = transform_records(
        raw_recaps,
        lambda rec: {
            **rec,
            "persentase": (
                pct := round((rec["total_poin"] / rec["total_pertemuan"]) * 100, 1)
                if rec["total_pertemuan"] > 0
                else 0.0
            ),
            "kelayakan_uas": "Layak UAS" if pct >= MIN_UAS_PERCENTAGE else "Tidak Layak",
        },
    )
    return sort_records(final_recaps, "persentase", descending=True)


# Cetak tabel daftar log kehadiran mentah per pertemuan.
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


# Cetak tabel rekap kehadiran, persentase hadir, dan kelayakan UAS per mahasiswa.
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


# Simulasi otomatis fitur Presensi Kelas untuk mode demo dan pengujian.
def run_demo() -> dict[str, Any]:
    """Jalankan skenario demo otomatis App 2 untuk verifikasi dan pengujian."""
    print_header("APP 2: PRESENSI KELAS (Kehadiran & Rekap per Mahasiswa)")
    logs = INITIAL_LOGS
    logs = record_attendance(logs, "230104", "Dewi Anggraini", 1, "Hadir")
    logs = record_attendance(logs, "230104", "Dewi Anggraini", 2, "Hadir")
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


# Jalankan menu CLI interaktif Presensi Kelas.
def run_cli() -> None:
    """Jalankan antarmuka terminal interaktif untuk Presensi Kelas."""
    state: dict[str, Any] = {"logs": list(INITIAL_LOGS)}

    # Menu 1: Tampilkan seluruh catatan log kehadiran.
    def show_all_logs() -> None:
        _print_logs(state["logs"])

    # Menu 2: Catat kehadiran mahasiswa (otomatis deteksi nama jika NIM ada) lalu tampilkan rekapnya.
    def add_log_action() -> None:
        nim = prompt_non_empty("NIM Mahasiswa")
        existing_student = filter_by_field(state["logs"], "nim", nim)
        if existing_student:
            nama = str(existing_student[0]["nama"])
            print(f"  Mahasiswa ditemukan: {nama} (NIM: {nim})")
        else:
            nama = prompt_non_empty("Nama Mahasiswa")
        pertemuan = prompt_int("Pertemuan ke-", min_value=1, max_value=16)
        status = prompt_non_empty("Status (Hadir/Izin/Sakit/Alfa)")
        try:
            state["logs"] = record_attendance(state["logs"], nim, nama, pertemuan, status)
            print("Presensi berhasil dicatat/diperbarui.")
            student_recap = filter_by_field(build_student_recaps(state["logs"]), "nim", nim)
            _print_recaps(student_recap, f"Rekap Terbaru NIM {nim}")
        except ValueError as err:
            print(f"Gagal: {err}")

    # Menu 3: Koreksi status presensi lewat update_by_id lalu cetak rekap terbaru mahasiswa terkait.
    def update_log_action() -> None:
        _print_logs(state["logs"])
        id_log = prompt_non_empty("Masukkan ID Log (misal P07)").upper()
        matched = filter_by_field(state["logs"], "id_log", id_log)
        if not matched:
            print(f"Gagal: ID Log '{id_log}' tidak ditemukan.")
            return
        status = prompt_non_empty("Status baru (Hadir/Izin/Sakit/Alfa)")
        try:
            clean_status = _normalize_status(status)
            state["logs"] = update_by_id(state["logs"], "id_log", id_log, {"status": clean_status})
            print(f"Log '{id_log}' diperbarui ke status '{clean_status}'.")
            nim = str(matched[0]["nim"])
            _print_recaps(filter_by_field(build_student_recaps(state["logs"]), "nim", nim), f"Rekap Terbaru NIM {nim}")
        except ValueError as err:
            print(f"Gagal: {err}")

    # Menu 4: Hapus log kehadiran lewat delete_attendance_log lalu tampilkan rekap terbaru.
    def delete_log_action() -> None:
        _print_logs(state["logs"])
        id_log = prompt_non_empty("Masukkan ID Log yang ingin dihapus").upper()
        try:
            state["logs"] = delete_attendance_log(state["logs"], id_log)
            print(f"Log '{id_log}' berhasil dihapus.")
            _print_recaps(build_student_recaps(state["logs"]))
        except ValueError as err:
            print(f"Gagal: {err}")

    # Menu 5: Saring log kehadiran berdasarkan status via filter_by_field.
    def filter_logs_action() -> None:
        status = prompt_non_empty("Filter status (Hadir/Izin/Sakit/Alfa)")
        try:
            clean_status = _normalize_status(status)
            filtered = filter_by_field(state["logs"], "status", clean_status)
            _print_logs(filtered, f"Log Status: {clean_status}")
        except ValueError as err:
            print(f"Gagal: {err}")

    # Menu 6: Tampilkan rekap % hadir dan kelayakan UAS semua mahasiswa.
    def show_recaps_action() -> None:
        recaps = build_student_recaps(state["logs"])
        _print_recaps(recaps)

    # Menu 7: Cari rekap mahasiswa berdasarkan potongan nama via search_by_keyword.
    def search_recap_action() -> None:
        keyword = prompt_non_empty("Masukkan kata kunci nama mahasiswa")
        recaps = build_student_recaps(state["logs"])
        matches = search_by_keyword(recaps, "nama", keyword)
        _print_recaps(matches, f"Hasil Cari '{keyword}'")

    run_menu_loop(
        "PRESENSI KELAS INTERAKTIF",
        [
            ("Lihat Semua Log Kehadiran", show_all_logs),
            ("Catat Kehadiran Baru", add_log_action),
            ("Koreksi Status Kehadiran", update_log_action),
            ("Hapus Log Kehadiran", delete_log_action),
            ("Filter Log Berdasarkan Status", filter_logs_action),
            ("Lihat Rekap Kehadiran per Mahasiswa", show_recaps_action),
            ("Cari Rekap Mahasiswa", search_recap_action),
        ],
    )
