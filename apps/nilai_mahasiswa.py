from __future__ import annotations

from typing import Any

from apps import print_header, prompt_float, prompt_int, prompt_non_empty, run_menu_loop
from fungsio_lib import (
    add_record,
    calculate_summary_stats,
    filter_by_field,
    group_by_field,
    search_by_keyword,
    sort_records,
    transform_records,
    update_by_id,
)

WEIGHT_TUGAS = 0.25
WEIGHT_KUIS = 0.15
WEIGHT_UTS = 0.30
WEIGHT_UAS = 0.30

INITIAL_STUDENTS: list[dict[str, Any]] = [
    {"nim": "230101", "nama": "Andi Pratama", "tugas": 85.0, "kuis": 80.0, "uts": 78.0, "uas": 84.0},
    {"nim": "230102", "nama": "Budi Santoso", "tugas": 70.0, "kuis": 65.0, "uts": 60.0, "uas": 55.0},
    {"nim": "230103", "nama": "Citra Lestari", "tugas": 92.0, "kuis": 90.0, "uts": 88.0, "uas": 94.0},
    {"nim": "230104", "nama": "Dewi Anggraini", "tugas": 55.0, "kuis": 50.0, "uts": 48.0, "uas": 45.0},
    {"nim": "230105", "nama": "Eko Wijaya", "tugas": 78.0, "kuis": 75.0, "uts": 80.0, "uas": 76.0},
]


def _validate_score(score: float, label: str) -> float:
    if score < 0.0 or score > 100.0:
        raise ValueError(f"Nilai {label} harus berada di rentang 0 - 100")
    return float(score)


def _determine_grade(final_score: float) -> str:
    if final_score >= 85.0:
        return "A"
    if final_score >= 75.0:
        return "B"
    if final_score >= 60.0:
        return "C"
    if final_score >= 50.0:
        return "D"
    return "E"


def add_student_scores(
    students: list[dict[str, Any]],
    nim: str,
    nama: str,
    tugas: float,
    kuis: float,
    uts: float,
    uas: float,
) -> list[dict[str, Any]]:
    """Append a validated student component-score record immutably."""
    if filter_by_field(students, "nim", nim.strip()):
        raise ValueError(f"Mahasiswa dengan NIM '{nim}' sudah terdaftar")

    entry = {
        "nim": nim.strip(),
        "nama": nama.strip(),
        "tugas": _validate_score(tugas, "Tugas"),
        "kuis": _validate_score(kuis, "Kuis"),
        "uts": _validate_score(uts, "UTS"),
        "uas": _validate_score(uas, "UAS"),
    }
    return add_record(students, entry)


def revise_student_scores(
    students: list[dict[str, Any]],
    nim: str,
    updates: dict[str, float],
) -> list[dict[str, Any]]:
    """Update specific component scores for a student by NIM."""
    if not filter_by_field(students, "nim", nim.strip()):
        raise ValueError(f"Mahasiswa dengan NIM '{nim}' tidak ditemukan")
    validated = {key: _validate_score(val, key.upper()) for key, val in updates.items()}
    return update_by_id(students, "nim", nim.strip(), validated)


def evaluate_class_grades(students: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute weighted final scores, grades, rankings, and class statistics."""
    computed_scores = transform_records(
        students,
        lambda s: {
            **s,
            "nilai_akhir": round(
                (float(s["tugas"]) * WEIGHT_TUGAS)
                + (float(s["kuis"]) * WEIGHT_KUIS)
                + (float(s["uts"]) * WEIGHT_UTS)
                + (float(s["uas"]) * WEIGHT_UAS),
                2,
            ),
        },
    )
    graded_students = transform_records(
        computed_scores,
        lambda s: {
            **s,
            "grade": _determine_grade(float(s["nilai_akhir"])),
            "status_lulus": "Lulus" if float(s["nilai_akhir"]) >= 60.0 else "Mengulang",
        },
    )
    rankings = sort_records(graded_students, "nilai_akhir", descending=True)
    passed_students = filter_by_field(rankings, "status_lulus", "Lulus")
    grade_distribution = group_by_field(rankings, "grade")
    class_stats = calculate_summary_stats(rankings, "nilai_akhir")

    return {
        "rankings": rankings,
        "passed_students": passed_students,
        "grade_distribution": grade_distribution,
        "class_stats": class_stats,
    }


def _print_rankings(students: list[dict[str, Any]], title: str = "Peringkat Nilai Akhir Mahasiswa") -> None:
    print(f"\n[{title}]")
    if not students:
        print("  (Data mahasiswa kosong)")
        return
    print(
        f"  {'Rank':<4} | {'NIM':<7} | {'Nama Mahasiswa':<18} | {'Tugas':>5} | {'Kuis':>5} | "
        f"{'UTS':>5} | {'UAS':>5} | {'Akhir':>6} | {'Grade':^5} | {'Status':<10}"
    )
    print("  " + "-" * 94)
    for s in students:
        rank = s.get("rank", "-")
        print(
            f"  {rank:<4} | {s['nim']:<7} | {s['nama'][:18]:<18} | {s['tugas']:>5.1f} | "
            f"{s['kuis']:>5.1f} | {s['uts']:>5.1f} | {s['uas']:>5.1f} | "
            f"{s['nilai_akhir']:>6.2f} | {s['grade']:^5} | {s['status_lulus']:<10}"
        )


def run_demo() -> dict[str, Any]:
    """Execute an end-to-end automated walkthrough of the Student Grades app."""
    print_header("APP 5: NILAI MAHASISWA (Komponen Nilai, Nilai Akhir, Peringkat)")
    students = INITIAL_STUDENTS
    students = add_student_scores(students, "230106", "Fajar Nugroho", 88, 84, 82, 86)
    students = revise_student_scores(students, "230102", {"uas": 68.0})

    evaluation = evaluate_class_grades(students)
    _print_rankings(evaluation["rankings"], "Peringkat Nilai Akhir Kelas")

    stats = evaluation["class_stats"]
    print(
        f"\n  Statistik Nilai Akhir -> Jumlah: {int(stats['count'])}, "
        f"Rata-rata: {stats['average']:.2f}, Terendah: {stats['min']:.2f}, Tertinggi: {stats['max']:.2f}"
    )

    print("\n  Distribusi Huruf Mutu:")
    for grade in sorted(evaluation["grade_distribution"].keys()):
        count = len(evaluation["grade_distribution"][grade])
        print(f"    - Grade {grade}: {count} mahasiswa")

    search_eko = search_by_keyword(evaluation["rankings"], "nama", "eko")
    _print_rankings(search_eko, "Pencarian Mahasiswa: 'eko'")
    return {
        **evaluation,
        "search_results": search_eko,
    }


def run_cli() -> None:
    """Launch interactive terminal UI for Student Grade calculation and ranking."""
    state: dict[str, Any] = {"students": list(INITIAL_STUDENTS)}

    def show_rankings() -> bool:
        evaluation = evaluate_class_grades(state["students"])
        _print_rankings(evaluation["rankings"])
        stats = evaluation["class_stats"]
        print(
            f"  Rata-rata Kelas: {stats['average']:.2f} | "
            f"Tertinggi: {stats['max']:.2f} | Terendah: {stats['min']:.2f}"
        )
        return True

    def add_student_action() -> bool:
        nim = prompt_non_empty("NIM Mahasiswa")
        nama = prompt_non_empty("Nama Mahasiswa")
        tugas = prompt_float("Nilai Tugas (0-100)", min_value=0.0, max_value=100.0)
        kuis = prompt_float("Nilai Kuis (0-100)", min_value=0.0, max_value=100.0)
        uts = prompt_float("Nilai UTS (0-100)", min_value=0.0, max_value=100.0)
        uas = prompt_float("Nilai UAS (0-100)", min_value=0.0, max_value=100.0)
        try:
            state["students"] = add_student_scores(
                state["students"], nim, nama, tugas, kuis, uts, uas
            )
            print("Data nilai mahasiswa berhasil ditambahkan.")
        except ValueError as err:
            print(f"Gagal: {err}")
        return True

    def revise_action() -> bool:
        evaluation = evaluate_class_grades(state["students"])
        _print_rankings(evaluation["rankings"])
        nim = prompt_non_empty("NIM Mahasiswa yang ingin direvisi")
        print("  Komponen: 1. Tugas  2. Kuis  3. UTS  4. UAS")
        comp_idx = prompt_int("Pilih komponen", min_value=1, max_value=4)
        comp_name = ["tugas", "kuis", "uts", "uas"][comp_idx - 1]
        new_score = prompt_float(f"Nilai {comp_name.upper()} baru (0-100)", min_value=0.0, max_value=100.0)
        try:
            state["students"] = revise_student_scores(state["students"], nim, {comp_name: new_score})
            print("Nilai berhasil direvisi.")
        except ValueError as err:
            print(f"Gagal: {err}")
        return True

    def filter_and_search_action() -> bool:
        evaluation = evaluate_class_grades(state["students"])
        print("  1. Filter Status Lulus/Mengulang  2. Cari Nama Mahasiswa")
        mode = prompt_int("Pilih mode", min_value=1, max_value=2)
        if mode == 1:
            status = prompt_non_empty("Status (Lulus/Mengulang)").capitalize()
            results = filter_by_field(evaluation["rankings"], "status_lulus", status)
            _print_rankings(results, f"Mahasiswa Status: {status}")
        else:
            keyword = prompt_non_empty("Kata kunci nama mahasiswa")
            results = search_by_keyword(evaluation["rankings"], "nama", keyword)
            _print_rankings(results, f"Hasil Cari '{keyword}'")
        return True

    def distribution_action() -> bool:
        evaluation = evaluate_class_grades(state["students"])
        print("\n[Distribusi Grade Mahasiswa]")
        for grade in sorted(evaluation["grade_distribution"].keys()):
            members = evaluation["grade_distribution"][grade]
            names = ", ".join(m["nama"] for m in members)
            print(f"  Grade {grade} ({len(members)}): {names}")
        return True

    run_menu_loop(
        "NILAI MAHASISWA INTERAKTIF",
        [
            ("Lihat Peringkat Nilai Akhir & Statistik", show_rankings),
            ("Input Nilai Mahasiswa Baru", add_student_action),
            ("Revisi Komponen Nilai Mahasiswa", revise_action),
            ("Filter Kelulusan / Cari Mahasiswa", filter_and_search_action),
            ("Lihat Distribusi Huruf Mutu (Grade)", distribution_action),
        ],
    )
