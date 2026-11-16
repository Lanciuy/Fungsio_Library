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
    next_prefixed_id,
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
    """Uji integrasi 5 aplikasi, perbaikan bug, dan kepatuhan syarat >= 3 app per fungsi."""

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

    def test_kasir_cart_qty_add_set_and_resolve(self) -> None:
        """Pastikan tambah/ubah qty keranjang dan resolusi nomor baris/ID bekerja akurat."""
        menu = kasir_kantin.INITIAL_MENU
        cart = kasir_kantin.add_to_cart(menu, [], "M01", 2)
        cart = kasir_kantin.add_to_cart(menu, cart, "m04", 1)

        # Tambah qty lewat mode='add' (2 + 3 = 5).
        cart = kasir_kantin.update_cart_quantity(cart, "M01", 3, mode="add")
        m01 = filter_by_field(cart, "id_menu", "M01")[0]
        self.assertEqual(m01["qty"], 5)

        # Resolve baris 1 (M01 punya subtotal terbesar) dan nama persis (M04).
        self.assertEqual(kasir_kantin._resolve_cart_id(cart, "1"), "M01")
        self.assertEqual(kasir_kantin._resolve_cart_id(cart, "es teh manis"), "M04")

        # Set qty ke 0 menghapus item, dan item tak dikenal melempar ValueError.
        cart = kasir_kantin.update_cart_quantity(cart, "M04", 0, mode="set")
        self.assertEqual(len(cart), 1)
        with self.assertRaises(ValueError):
            kasir_kantin.update_cart_quantity(cart, "M99", 2, mode="set")

        # Tambah menu baru menghasilkan ID M07.
        updated_menu = kasir_kantin.add_menu_item(menu, "Soto Ayam", "makanan", 16000)
        self.assertEqual(updated_menu[-1]["id_menu"], "M07")

    def test_next_id_and_app_edge_cases(self) -> None:
        """Verifikasi perbaikan bug ID bentrok, presensi duplikat, pinjaman aktif, transaksi, & nilai."""
        # ID generator tidak bentrok setelah record tengah dihapus.
        records = [{"id": "P01"}, {"id": "P03"}]
        self.assertEqual(next_prefixed_id(records, "id", "P"), "P04")

        # Presensi: mencatat NIM+pertemuan yang sama memperbarui status tanpa duplikasi.
        logs = presensi_kelas.record_attendance(presensi_kelas.INITIAL_LOGS, "230101", "", 4, "Hadir")
        self.assertEqual(len(logs), len(presensi_kelas.INITIAL_LOGS))
        p04 = filter_by_field(logs, "id_log", "P04")[0]
        self.assertEqual(p04["status"], "Hadir")
        logs_after_del = presensi_kelas.delete_attendance_log(logs, "P04")
        self.assertEqual(len(logs_after_del), len(logs) - 1)

        # Perpustakaan: kembalikan pinjaman selesai ditolak; hapus pinjaman aktif memulihkan stok buku.
        with self.assertRaises(ValueError):
            perpustakaan_mini.return_book(
                perpustakaan_mini.INITIAL_CATALOG, perpustakaan_mini.INITIAL_LOANS, "L03"
            )
        cat_restored, loans_left = perpustakaan_mini.delete_loan(
            perpustakaan_mini.INITIAL_CATALOG, perpustakaan_mini.INITIAL_LOANS, "L01"
        )
        self.assertTrue(filter_by_field(cat_restored, "id_buku", "B02")[0]["tersedia"])
        self.assertEqual(len(loans_left), 2)

        # Keuangan: update_transaction & delete_transaction bekerja dan memvalidasi ID.
        trx = keuangan_pribadi.update_transaction(
            keuangan_pribadi.INITIAL_TRANSACTIONS, "T02", {"nominal": 50000}
        )
        self.assertEqual(filter_by_field(trx, "id_trx", "T02")[0]["nominal"], 50000.0)
        trx = keuangan_pribadi.delete_transaction(trx, "T02")
        self.assertEqual(len(trx), 5)

        # Nilai: delete_student_scores membuang data mahasiswa sesuai NIM.
        remaining_students = nilai_mahasiswa.delete_student_scores(
            nilai_mahasiswa.INITIAL_STUDENTS, "230104"
        )
        self.assertEqual(len(remaining_students), 4)

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
