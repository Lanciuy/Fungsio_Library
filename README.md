# Fungsio Library (`fungsio_lib`) & 5 Aplikasi CLI Python

Proyek ini mengimplementasikan **1 library fungsional Python (`fungsio_lib`)** berisi **10 pure functions** yang bersifat *reusable* dan **5 aplikasi CLI interaktif** yang memanfaatkan fungsi-fungsi tersebut. Setiap fungsi di dalam library dipakai di **minimal 3 aplikasi berbeda** dan diaudit secara otomatis melalui AST (*Abstract Syntax Tree*).

---

## Prinsip Functional Programming

Seluruh fungsi pada [`fungsio_lib/core.py`](fungsio_lib/core.py) dirancang dengan pendekatan fungsional:
- **Pure Functions**: Output bergantung sepenuhnya pada input tanpa efek samping tersembunyi.
- **Immutability**: Menggunakan `copy.deepcopy` untuk mengembalikan koleksi baru tanpa memutasi list atau dictionary asal.
- **Higher-Order Function & Reduction**: Menggunakan fungsi pemetaan (`transform_records`) dan agregasi (`functools.reduce` pada `sum_by_field`).
- **Zero External Dependencies**: Hanya menggunakan Python Standard Library.

---

## Struktur Direktori

```text
Fungsio_API/
├── fungsio_lib/
│   ├── __init__.py          # Ekspor 10 pure functions
│   └── core.py              # Implementasi 10 pure functions + validasi tipe
├── apps/
│   ├── __init__.py          # Helper CLI bersama (format Rupiah, input validasi, loop menu)
│   ├── kasir_kantin.py      # App 1: Menu, keranjang, total belanja
│   ├── presensi_kelas.py    # App 2: Kehadiran & rekap per mahasiswa
│   ├── perpustakaan_mini.py # App 3: Katalog, peminjaman, denda
│   ├── keuangan_pribadi.py  # App 4: Pemasukan, pengeluaran, kategori
│   └── nilai_mahasiswa.py   # App 5: Komponen nilai, nilai akhir, peringkat
├── tests/
│   └── test_all.py          # Unit test, integrasi 5 app, dan audit AST matriks 10x5
├── main.py                  # Portal CLI interaktif & runner mode --demo
├── .gitignore
└── README.md
```

---

## Daftar 10 Fungsi pada `fungsio_lib`

| No | Nama Fungsi | Signature & Kegunaan |
| :-: | :--- | :--- |
| 1 | `add_record` | `add_record(collection, record) -> list[dict]` — Menambahkan record baru secara *immutable*. |
| 2 | `filter_by_field` | `filter_by_field(collection, field, value) -> list[dict]` — Menyaring data berdasarkan kecocokan nilai pada field. |
| 3 | `search_by_keyword` | `search_by_keyword(collection, field, keyword) -> list[dict]` — Pencarian substring *case-insensitive* pada field teks. |
| 4 | `update_by_id` | `update_by_id(collection, id_field, target_id, updates) -> list[dict]` — Memperbarui field record berdasarkan ID secara *immutable*. |
| 5 | `remove_by_id` | `remove_by_id(collection, id_field, target_id) -> list[dict]` — Menghapus record berdasarkan ID target dan mengembalikan koleksi baru. |
| 6 | `transform_records` | `transform_records(collection, transformer) -> list[dict]` — *Higher-order function* untuk menghitung atau memetakan atribut turunan tiap record. |
| 7 | `sum_by_field` | `sum_by_field(collection, numeric_field) -> float` — Menjumlahkan field numerik menggunakan `functools.reduce`. |
| 8 | `group_by_field` | `group_by_field(collection, key_field) -> dict[Any, list[dict]]` — Mengelompokkan record berdasarkan nilai field kunci. |
| 9 | `sort_records` | `sort_records(collection, sort_field, descending=True) -> list[dict]` — Mengurutkan record dan menambahkan atribut `rank` (`1..N`). |
| 10 | `calculate_summary_stats` | `calculate_summary_stats(collection, numeric_field) -> dict[str, float]` — Menghitung statistik `count`, `total`, `average`, `min`, dan `max`. |

---

## 5 Aplikasi CLI

1. **Kasir Kantin** ([`apps/kasir_kantin.py`](apps/kasir_kantin.py))
   - Menampilkan dan mengurutkan menu, filter kategori (`Makanan`/`Minuman`), pencarian nama menu, statistik harga menu, manajemen keranjang (tambah, ubah `qty`, hapus item), serta hitung subtotal, diskon 10% (`>= Rp50.000`), PPN 11%, dan total bayar.
2. **Presensi Kelas** ([`apps/presensi_kelas.py`](apps/presensi_kelas.py))
   - Pencatatan log kehadiran (`Hadir`, `Izin`, `Sakit`, `Alfa`), koreksi status kehadiran, filter status, rekap per mahasiswa (pengelompokan per NIM, total poin, persentase kehadiran, kelayakan UAS `>= 75%`), pencarian mahasiswa, dan urutan peringkat kehadiran.
3. **Perpustakaan Mini** ([`apps/perpustakaan_mini.py`](apps/perpustakaan_mini.py))
   - Katalog buku, filter buku tersedia, pencarian judul, rekap jumlah buku per kategori, pencatatan pinjam/kembali, hapus log peminjaman, serta hitung keterlambatan (`> 7 hari`) dan denda (`Rp2.000/hari`) beserta statistik denda.
4. **Keuangan Pribadi** ([`apps/keuangan_pribadi.py`](apps/keuangan_pribadi.py))
   - Pencatatan transaksi `Pemasukan` dan `Pengeluaran`, filter tipe transaksi, hapus transaksi, kalkulasi arus kas bertanda, saldo bersih, rekap per kategori, urutan pengeluaran terbesar, dan statistik pengeluaran.
5. **Nilai Mahasiswa** ([`apps/nilai_mahasiswa.py`](apps/nilai_mahasiswa.py))
   - Input dan revisi komponen nilai (`Tugas` 25%, `Kuis` 15%, `UTS` 30%, `UAS` 30%), perhitungan `nilai_akhir`, konversi huruf mutu (`A`–`E`) dan kelulusan, peringkat kelas, distribusi grade, pencarian mahasiswa, dan statistik nilai kelas.

---

## Matriks Pemakaian Fungsi (10 × 5)

Setiap fungsi di `fungsio_lib` dipakai di 3 hingga 5 aplikasi berbeda:

| No | Fungsi Library | 1. Kasir Kantin | 2. Presensi Kelas | 3. Perpustakaan Mini | 4. Keuangan Pribadi | 5. Nilai Mahasiswa | Total App |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `add_record` | ✅ | ✅ | ✅ | ✅ | ✅ | **5 App** |
| 2 | `filter_by_field` | ✅ | ✅ | ✅ | ✅ | ✅ | **5 App** |
| 3 | `search_by_keyword` | ✅ | ✅ | ✅ | — | ✅ | **4 App** |
| 4 | `update_by_id` | ✅ | ✅ | ✅ | — | ✅ | **4 App** |
| 5 | `remove_by_id` | ✅ | — | ✅ | ✅ | — | **3 App** |
| 6 | `transform_records` | ✅ | ✅ | ✅ | ✅ | ✅ | **5 App** |
| 7 | `sum_by_field` | ✅ | ✅ | ✅ | ✅ | — | **4 App** |
| 8 | `group_by_field` | — | ✅ | ✅ | ✅ | ✅ | **4 App** |
| 9 | `sort_records` | ✅ | ✅ | — | ✅ | ✅ | **4 App** |
| 10 | `calculate_summary_stats` | ✅ | — | ✅ | ✅ | ✅ | **4 App** |

---

## Cara Menjalankan

### 1. Mode Interaktif (Memilih salah satu dari 5 aplikasi)
```bash
python main.py
```

### 2. Mode Demo Otomatis (Menjalankan 5 aplikasi + Audit Matriks AST)
```bash
python main.py --demo
```

### 3. Menjalankan Unit & Integration Tests
```bash
python -m unittest discover -s tests -v
```
