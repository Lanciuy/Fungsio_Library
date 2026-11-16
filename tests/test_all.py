from __future__ import annotations

import ast
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import fungsio_lib
from apps import (
    kasir_kantin,
    keuangan_pribadi,
    nilai_mahasiswa,
    perpustakaan_mini,
    presensi_kelas,
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


class TestFungsioLibCore(unittest.TestCase):
    """Verify correctness, edge cases, and strict immutability of all 10 functions."""

    def setUp(self) -> None:
        self.sample_data = [
            {"id": "1", "name": "Nasi Goreng", "category": "Food", "price": 18000, "tags": ["hot"]},
            {"id": "2", "name": "Es Teh Manis", "category": "Drink", "price": 5000, "tags": ["cold"]},
            {"id": "3", "name": "Mie Ayam", "category": "Food", "price": 15000, "tags": ["noodle"]},
        ]

    def test_add_record_immutability(self) -> None:
        new_item = {"id": "4", "name": "Kopi", "category": "Drink", "price": 12000, "tags": ["hot"]}
        result = add_record(self.sample_data, new_item)
        self.assertEqual(len(self.sample_data), 3)
        self.assertEqual(len(result), 4)
        new_item["tags"].append("sweet")
        self.assertEqual(result[3]["tags"], ["hot"])

    def test_filter_by_field(self) -> None:
        foods = filter_by_field(self.sample_data, "category", "Food")
        self.assertEqual(len(foods), 2)
        self.assertEqual([item["id"] for item in foods], ["1", "3"])
        none_match = filter_by_field([{"id": "1"}], "category", None)
        self.assertEqual(none_match, [])

    def test_search_by_keyword(self) -> None:
        matches = search_by_keyword(self.sample_data, "name", "  NASI ")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["id"], "1")
        all_items = search_by_keyword(self.sample_data, "name", "")
        self.assertEqual(len(all_items), 3)

    def test_update_by_id_immutability(self) -> None:
        updated = update_by_id(self.sample_data, "id", "2", {"price": 7000})
        self.assertEqual(self.sample_data[1]["price"], 5000)
        self.assertEqual(updated[1]["price"], 7000)

    def test_remove_by_id(self) -> None:
        remaining = remove_by_id(self.sample_data, "id", "2")
        self.assertEqual(len(self.sample_data), 3)
        self.assertEqual([item["id"] for item in remaining], ["1", "3"])

    def test_transform_records_protects_source(self) -> None:
        def mutate_and_enrich(item: dict) -> dict:
            item["tags"].append("checked")
            return {**item, "double_price": item["price"] * 2}

        transformed = transform_records(self.sample_data, mutate_and_enrich)
        self.assertEqual(self.sample_data[0]["tags"], ["hot"])
        self.assertEqual(transformed[0]["double_price"], 36000)

    def test_sum_by_field_and_bool_rejection(self) -> None:
        total = sum_by_field(self.sample_data, "price")
        self.assertEqual(total, 38000.0)
        self.assertEqual(sum_by_field([], "price"), 0.0)
        with self.assertRaises(TypeError):
            sum_by_field([{"price": True}], "price")

    def test_group_by_field(self) -> None:
        grouped = group_by_field(self.sample_data, "category")
        self.assertEqual(set(grouped.keys()), {"Food", "Drink"})
        self.assertEqual(len(grouped["Food"]), 2)
        self.assertEqual(len(grouped["Drink"]), 1)

    def test_sort_records_and_rank(self) -> None:
        ranked = sort_records(self.sample_data, "price", descending=True)
        self.assertEqual([item["id"] for item in ranked], ["1", "3", "2"])
        self.assertEqual([item["rank"] for item in ranked], [1, 2, 3])
        self.assertNotIn("rank", self.sample_data[0])

    def test_calculate_summary_stats(self) -> None:
        stats = calculate_summary_stats(self.sample_data, "price")
        self.assertEqual(stats["count"], 3.0)
        self.assertEqual(stats["total"], 38000.0)
        self.assertAlmostEqual(stats["average"], 38000.0 / 3.0)
        self.assertEqual(stats["min"], 5000.0)
        self.assertEqual(stats["max"], 18000.0)

        empty_stats = calculate_summary_stats([], "price")
        self.assertEqual(empty_stats["count"], 0.0)
        self.assertEqual(empty_stats["average"], 0.0)


class TestApplicationsAndMatrixCompliance(unittest.TestCase):
    """Verify all 5 applications run cleanly and satisfy the >= 3 apps per function rule."""

    def test_all_five_app_demos(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            kasir_res = kasir_kantin.run_demo()
            presensi_res = presensi_kelas.run_demo()
            perpus_res = perpustakaan_mini.run_demo()
            keuangan_res = keuangan_pribadi.run_demo()
            nilai_res = nilai_mahasiswa.run_demo()

        # App 1: Kasir Kantin assertions (2*18000 + 1*20000 + 2*5000 = 66000; 10% disc = 6600 -> 59400; +11% = 65934)
        self.assertAlmostEqual(kasir_res["checkout"]["gross_total"], 66000.0)
        self.assertAlmostEqual(kasir_res["checkout"]["discount"], 6600.0)
        self.assertAlmostEqual(kasir_res["checkout"]["grand_total"], 65934.0)

        # App 2: Presensi Kelas assertions
        self.assertGreaterEqual(len(presensi_res["recaps"]), 4)
        self.assertEqual(presensi_res["recaps"][0]["rank"], 1)

        # App 3: Perpustakaan Mini assertions (L01: 10->3d*2000=6000, L02: 12->5d*2000=10000, L04: 9->2d*2000=4000 => total 20000)
        self.assertAlmostEqual(perpus_res["fine_report"]["total_denda"], 20000.0)

        # App 4: Keuangan Pribadi assertions
        # Income: 2500000 + 450000 = 2950000; Expenses: 60000 + 185000 + 110000 + 75000 + 120000 = 550000
        self.assertAlmostEqual(keuangan_res["total_pemasukan"], 2950000.0)
        self.assertAlmostEqual(keuangan_res["total_pengeluaran"], 550000.0)
        self.assertAlmostEqual(keuangan_res["saldo_bersih"], 2400000.0)

        # App 5: Nilai Mahasiswa assertions
        self.assertEqual(len(nilai_res["rankings"]), 6)
        self.assertEqual(nilai_res["rankings"][0]["nama"], "Citra Lestari")
        self.assertEqual(nilai_res["rankings"][0]["grade"], "A")

    def test_ten_functions_used_in_at_least_three_apps(self) -> None:
        self.assertEqual(len(fungsio_lib.__all__), 10)
        apps_dir = Path(__file__).resolve().parent.parent / "apps"
        app_files = [
            "kasir_kantin.py",
            "presensi_kelas.py",
            "perpustakaan_mini.py",
            "keuangan_pribadi.py",
            "nilai_mahasiswa.py",
        ]

        usage_map: dict[str, set[str]] = {fn: set() for fn in fungsio_lib.__all__}
        for filename in app_files:
            file_path = apps_dir / filename
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    called = None
                    if isinstance(node.func, ast.Name):
                        called = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        called = node.func.attr
                    if called in usage_map:
                        usage_map[called].add(filename)

        for fn_name, app_set in usage_map.items():
            with self.subTest(function=fn_name):
                self.assertGreaterEqual(
                    len(app_set),
                    3,
                    f"Fungsi '{fn_name}' hanya dipakai di {len(app_set)} aplikasi: {sorted(app_set)}",
                )


if __name__ == "__main__":
    unittest.main()
