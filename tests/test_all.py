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
    """Uji kebenaran logika, edge case, dan immutability ke-10 fungsi library."""

    def setUp(self) -> None:
        self.sample_data = [
            {"id": "1", "name": "Nasi Goreng", "category": "Food", "price": 18000, "tags": ["hot"]},
            {"id": "2", "name": "Es Teh Manis", "category": "Drink", "price": 5000, "tags": ["cold"]},
            {"id": "3", "name": "Mie Ayam", "category": "Food", "price": 15000, "tags": ["noodle"]},
        ]

    def test_add_record_immutability(self) -> None:
        """Pastikan add_record tidak memutasi list awal maupun referensi dict baru."""
        new_item = {"id": "4", "name": "Kopi", "category": "Drink", "price": 12000, "tags": ["hot"]}
        result = add_record(self.sample_data, new_item)
        self.assertEqual(len(self.sample_data), 3)
        self.assertEqual(len(result), 4)
        new_item["tags"].append("sweet")
        self.assertEqual(result[3]["tags"], ["hot"])

    def test_filter_by_field(self) -> None:
        """Pastikan filter_by_field hanya mengambil record dengan field & nilai yang cocok."""
        foods = filter_by_field(self.sample_data, "category", "Food")
        self.assertEqual(len(foods), 2)
        self.assertEqual([item["id"] for item in foods], ["1", "3"])
        none_match = filter_by_field([{"id": "1"}], "category", None)
        self.assertEqual(none_match, [])

    def test_search_by_keyword(self) -> None:
        """Pastikan pencarian mengabaikan spasi tepi, huruf besar/kecil, dan fallback saat kosong."""
        matches = search_by_keyword(self.sample_data, "name", "  NASI ")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["id"], "1")
        all_items = search_by_keyword(self.sample_data, "name", "")
        self.assertEqual(len(all_items), 3)

    def test_update_by_id_immutability(self) -> None:
        """Pastikan update_by_id memperbarui salinan baru tanpa mengubah data awal."""
        updated = update_by_id(self.sample_data, "id", "2", {"price": 7000})
        self.assertEqual(self.sample_data[1]["price"], 5000)
        self.assertEqual(updated[1]["price"], 7000)

    def test_remove_by_id(self) -> None:
        """Pastikan remove_by_id membuang record ber-ID target tanpa mutasi list asal."""
        remaining = remove_by_id(self.sample_data, "id", "2")
        self.assertEqual(len(self.sample_data), 3)
        self.assertEqual([item["id"] for item in remaining], ["1", "3"])

    def test_transform_records_protects_source(self) -> None:
        """Pastikan transform_records mengisolasi sumber jika callback memutasi argumennya."""
        def mutate_and_enrich(item: dict) -> dict:
            item["tags"].append("checked")
            return {**item, "double_price": item["price"] * 2}

        transformed = transform_records(self.sample_data, mutate_and_enrich)
        self.assertEqual(self.sample_data[0]["tags"], ["hot"])
        self.assertEqual(transformed[0]["double_price"], 36000)

    def test_sum_by_field_and_bool_rejection(self) -> None:
        """Pastikan sum_by_field menjumlahkan akurat dan menolak tipe bool."""
        total = sum_by_field(self.sample_data, "price")
        self.assertEqual(total, 38000.0)
        self.assertEqual(sum_by_field([], "price"), 0.0)
        with self.assertRaises(TypeError):
            sum_by_field([{"price": True}], "price")

    def test_group_by_field(self) -> None:
        """Pastikan group_by_field mengelompokkan record sesuai nilai key."""
        grouped = group_by_field(self.sample_data, "category")
        self.assertEqual(set(grouped.keys()), {"Food", "Drink"})
        self.assertEqual(len(grouped["Food"]), 2)
        self.assertEqual(len(grouped["Drink"]), 1)

    def test_sort_records_and_rank(self) -> None:
        """Pastikan sort_records mengurutkan dan menyematkan rank 1..N tanpa mengubah data asal."""
        ranked = sort_records(self.sample_data, "price", descending=True)
        self.assertEqual([item["id"] for item in ranked], ["1", "3", "2"])
        self.assertEqual([item["rank"] for item in ranked], [1, 2, 3])
        self.assertNotIn("rank", self.sample_data[0])

    def test_calculate_summary_stats(self) -> None:
        """Pastikan statistik mengembalikan count/total/avg/min/max serta aman saat list kosong."""
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
    """Uji integrasi 5 aplikasi dan kepatuhan syarat minimal 3 aplikasi per fungsi."""

    def test_all_five_app_demos(self) -> None:
        """Verifikasi output kalkulasi bisnis dari kelima demo aplikasi."""
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            kasir_res = kasir_kantin.run_demo()
            presensi_res = presensi_kelas.run_demo()
            perpus_res = perpustakaan_mini.run_demo()
            keuangan_res = keuangan_pribadi.run_demo()
            nilai_res = nilai_mahasiswa.run_demo()

        # Kasir: 2*18000 + 1*20000 + 2*5000 = 66000; diskon 10% = 6600; +PPN 11% = 65934.
        self.assertAlmostEqual(kasir_res["checkout"]["gross_total"], 66000.0)
        self.assertAlmostEqual(kasir_res["checkout"]["discount"], 6600.0)
        self.assertAlmostEqual(kasir_res["checkout"]["grand_total"], 65934.0)

        # Presensi: pastikan semua mahasiswa terekap dan peringkat 1 terisi.
        self.assertGreaterEqual(len(presensi_res["recaps"]), 4)
        self.assertEqual(presensi_res["recaps"][0]["rank"], 1)

        # Perpustakaan: L01 (telat 3 hari = 6000) + L02 (5 hari = 10000) + L04 (2 hari = 4000) = 20000.
        self.assertAlmostEqual(perpus_res["fine_report"]["total_denda"], 20000.0)

        # Keuangan: Pemasukan 2.950.000, Pengeluaran 550.000, Saldo bersih 2.400.000.
        self.assertAlmostEqual(keuangan_res["total_pemasukan"], 2950000.0)
        self.assertAlmostEqual(keuangan_res["total_pengeluaran"], 550000.0)
        self.assertAlmostEqual(keuangan_res["saldo_bersih"], 2400000.0)

        # Nilai: 6 mahasiswa dengan peringkat 1 Citra Lestari (grade A).
        self.assertEqual(len(nilai_res["rankings"]), 6)
        self.assertEqual(nilai_res["rankings"][0]["nama"], "Citra Lestari")
        self.assertEqual(nilai_res["rankings"][0]["grade"], "A")

    def test_ten_functions_used_in_at_least_three_apps(self) -> None:
        """Audit AST untuk menjamin tiap dari 10 fungsi dipakai di minimal 3 aplikasi berbeda."""
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
