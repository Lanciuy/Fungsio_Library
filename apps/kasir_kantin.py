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
    remove_by_id,
    search_by_keyword,
    sort_records,
    sum_by_field,
    transform_records,
    update_by_id,
)

# Aturan diskon otomatis 10% untuk belanja >= Rp50.000 dan PPN 11%.
DISCOUNT_THRESHOLD = 50000.0
DISCOUNT_RATE = 0.10
TAX_RATE = 0.11

INITIAL_MENU: list[dict[str, Any]] = [
    {"id_menu": "M01", "nama": "Nasi Goreng Spesial", "kategori": "Makanan", "harga": 18000},
    {"id_menu": "M02", "nama": "Mie Ayam Bakso", "kategori": "Makanan", "harga": 15000},
    {"id_menu": "M03", "nama": "Ayam Geprek Sambal Matah", "kategori": "Makanan", "harga": 20000},
    {"id_menu": "M04", "nama": "Es Teh Manis", "kategori": "Minuman", "harga": 5000},
    {"id_menu": "M05", "nama": "Jus Alpukat", "kategori": "Minuman", "harga": 12000},
    {"id_menu": "M06", "nama": "Kopi Susu Gula Aren", "kategori": "Minuman", "harga": 14000},
]


# Tambah menu baru ke katalog kantin -> pakai next_prefixed_id + add_record.
def add_menu_item(
    menu: list[dict[str, Any]],
    nama: str,
    kategori: str,
    harga: float,
) -> list[dict[str, Any]]:
    """Tambahkan item menu kantin baru secara immutable memakai add_record."""
    if harga <= 0:
        raise ValueError("Harga menu harus lebih dari 0")
    clean_kategori = kategori.strip().title()
    if clean_kategori not in {"Makanan", "Minuman"}:
        raise ValueError("Kategori menu harus 'Makanan' atau 'Minuman'")

    entry = {
        "id_menu": next_prefixed_id(menu, "id_menu", "M"),
        "nama": nama.strip(),
        "kategori": clean_kategori,
        "harga": int(round(harga)),
    }
    return add_record(menu, entry)


# Terjemahkan input user (ID menu, nomor baris struk, atau nama) menjadi id_menu valid di keranjang.
def _resolve_cart_id(cart: list[dict[str, Any]], raw_identifier: str) -> str | None:
    """Cocokkan input user ke ID menu di keranjang via ID, nomor baris struk, atau nama."""
    cleaned = raw_identifier.strip()
    if not cleaned:
        return None

    upper_id = cleaned.upper()
    if filter_by_field(cart, "id_menu", upper_id):
        return upper_id

    if cleaned.isdigit():
        row_num = int(cleaned)
        ordered_items = compute_checkout(cart)["items"]
        if 1 <= row_num <= len(ordered_items):
            return str(ordered_items[row_num - 1]["id_menu"])

    lowered = cleaned.lower()
    return next((str(i["id_menu"]) for i in cart if str(i["nama"]).lower() == lowered), None)


# Masukkan item ke keranjang: pakai filter_by_field, lalu update_by_id jika sudah ada atau add_record jika baru.
def add_to_cart(
    menu: list[dict[str, Any]],
    cart: list[dict[str, Any]],
    id_menu: str,
    qty: int,
) -> list[dict[str, Any]]:
    """Tambah item menu ke keranjang atau akomodasi kenaikan qty jika sudah ada."""
    if qty <= 0:
        raise ValueError("Jumlah (qty) harus lebih dari 0")

    clean_id = id_menu.strip().upper()
    matched_menu = filter_by_field(menu, "id_menu", clean_id)
    if not matched_menu:
        raise ValueError(f"Menu dengan ID '{id_menu}' tidak ditemukan")

    menu_item = matched_menu[0]
    existing_cart_item = filter_by_field(cart, "id_menu", clean_id)
    if existing_cart_item:
        new_qty = int(existing_cart_item[0]["qty"]) + qty
        return update_by_id(cart, "id_menu", clean_id, {"qty": new_qty})

    new_entry = {
        "id_menu": menu_item["id_menu"],
        "nama": menu_item["nama"],
        "kategori": menu_item["kategori"],
        "harga": menu_item["harga"],
        "qty": qty,
    }
    return add_record(cart, new_entry)


# Ubah qty item keranjang (mode 'add' menambah qty, mode 'set' mengganti; <= 0 menghapus via remove_by_id).
def update_cart_quantity(
    cart: list[dict[str, Any]],
    id_menu: str,
    new_qty: int,
    mode: str = "set",
) -> list[dict[str, Any]]:
    """Ubah qty item keranjang (mode 'set' mengganti qty, mode 'add' menambah ke qty lama)."""
    if mode not in {"set", "add"}:
        raise ValueError("Mode pembaruan qty harus 'set' atau 'add'")

    clean_id = id_menu.strip().upper()
    existing = filter_by_field(cart, "id_menu", clean_id)
    if not existing:
        raise ValueError(f"Item '{id_menu}' tidak ditemukan di keranjang")

    target_qty = int(existing[0]["qty"]) + new_qty if mode == "add" else new_qty
    if target_qty <= 0:
        return remove_by_id(cart, "id_menu", clean_id)
    return update_by_id(cart, "id_menu", clean_id, {"qty": target_qty})


# Hitung checkout: transform_records (subtotal) -> sort_records (urut terbesar) -> sum_by_field (total) -> diskon & PPN.
def compute_checkout(cart: list[dict[str, Any]]) -> dict[str, Any]:
    """Hitung subtotal per item, diskon, PPN, dan total bayar akhir dari keranjang."""
    cart_with_subtotals = transform_records(
        cart,
        lambda item: {
            **item,
            "subtotal": float(item["harga"]) * int(item["qty"]),
        },
    )
    ordered_items = sort_records(cart_with_subtotals, "subtotal", descending=True)
    gross_total = sum_by_field(ordered_items, "subtotal")
    total_qty = int(sum_by_field(ordered_items, "qty"))

    discount = gross_total * DISCOUNT_RATE if gross_total >= DISCOUNT_THRESHOLD else 0.0
    after_discount = gross_total - discount
    tax = after_discount * TAX_RATE
    grand_total = after_discount + tax
    return {
        "items": ordered_items,
        "total_qty": total_qty,
        "gross_total": gross_total,
        "discount": discount,
        "tax": tax,
        "grand_total": grand_total,
    }


# Cetak tabel daftar menu kantin ke terminal.
def _print_menu_table(menu: list[dict[str, Any]], title: str = "Daftar Menu Kantin") -> None:
    """Tampilkan daftar menu kantin dalam format tabel terminal."""
    print(f"\n[{title}]")
    if not menu:
        print("  (Menu kosong)")
        return
    print(f"  {'ID':<5} | {'Nama Menu':<26} | {'Kategori':<10} | {'Harga':>12}")
    print("  " + "-" * 60)
    for item in menu:
        print(
            f"  {item['id_menu']:<5} | {item['nama']:<26} | {item['kategori']:<10} | {format_idr(item['harga']):>12}"
        )


# Cetak tabel isi keranjang, nomor baris, ID, qty, subtotal, diskon, PPN, dan total bayar.
def _print_receipt(checkout: dict[str, Any]) -> None:
    """Cetak struk rincian belanja termasuk ID menu, qty, potongan diskon, dan PPN."""
    print("\n[Struk & Isi Keranjang Belanja]")
    if not checkout["items"]:
        print("  Keranjang masih kosong.")
        return
    print(f"  {'No':<3} | {'ID':<4} | {'Menu':<25} | {'Qty':>3} | {'Harga':>10} | {'Subtotal':>12}")
    print("  " + "-" * 71)
    for item in checkout["items"]:
        print(
            f"  {item['rank']:<3} | {item['id_menu']:<4} | {item['nama'][:25]:<25} | {item['qty']:>3} | "
            f"{format_idr(item['harga']):>10} | {format_idr(item['subtotal']):>12}"
        )
    print("  " + "-" * 71)
    print(f"  Total Item   : {checkout['total_qty']} pcs")
    print(f"  Total Kotor  : {format_idr(checkout['gross_total'])}")
    print(f"  Diskon (10%) : -{format_idr(checkout['discount'])}")
    print(f"  PPN (11%)    : {format_idr(checkout['tax'])}")
    print(f"  TOTAL BAYAR  : {format_idr(checkout['grand_total'])}")


# Simulasi otomatis seluruh fitur Kasir Kantin untuk demo dan pengujian.
def run_demo() -> dict[str, Any]:
    """Jalankan skenario demo otomatis App 1 untuk verifikasi dan pengujian."""
    print_header("APP 1: KASIR KANTIN (Menu, Keranjang, Total Belanja)")
    menu = INITIAL_MENU
    sorted_menu = sort_records(menu, "harga", descending=False)
    _print_menu_table(sorted_menu, "Menu Urut Harga Termurah")

    menu_stats = calculate_summary_stats(menu, "harga")
    print(
        f"\n  Statistik Harga Menu -> Jumlah: {int(menu_stats['count'])}, "
        f"Rata-rata: {format_idr(menu_stats['average'])}, "
        f"Termurah: {format_idr(menu_stats['min'])}, Termahal: {format_idr(menu_stats['max'])}"
    )

    drinks = filter_by_field(menu, "kategori", "Minuman")
    _print_menu_table(drinks, "Filter Kategori: Minuman")

    search_ayam = search_by_keyword(menu, "nama", "ayam")
    _print_menu_table(search_ayam, "Pencarian Kata Kunci: 'ayam'")

    cart: list[dict[str, Any]] = []
    cart = add_to_cart(menu, cart, "M01", 2)
    cart = add_to_cart(menu, cart, "M03", 1)
    cart = add_to_cart(menu, cart, "M04", 3)
    cart = add_to_cart(menu, cart, "M06", 1)
    cart = update_cart_quantity(cart, "M04", 2, mode="set")
    cart = remove_by_id(cart, "id_menu", "M06")

    checkout = compute_checkout(cart)
    _print_receipt(checkout)
    return {
        "menu_stats": menu_stats,
        "drinks": drinks,
        "search_results": search_ayam,
        "checkout": checkout,
    }


# Jalankan menu CLI interaktif Kasir Kantin dengan state menu dan keranjang di memori.
def run_cli() -> None:
    """Jalankan antarmuka terminal interaktif untuk Kasir Kantin."""
    state: dict[str, Any] = {
        "menu": list(INITIAL_MENU),
        "cart": [],
    }

    # Tampilkan ringkasan qty & subtotal item yang baru diubah lalu cetak ulang isi keranjang.
    def _print_item_qty_feedback(id_menu: str) -> None:
        updated = filter_by_field(state["cart"], "id_menu", id_menu)
        if updated:
            item = updated[0]
            subtotal = float(item["harga"]) * int(item["qty"])
            print(
                f"  -> Item '{item['nama']}' (ID: {item['id_menu']}) "
                f"Qty sekarang: {item['qty']} pcs (Subtotal: {format_idr(subtotal)})"
            )
        _print_receipt(compute_checkout(state["cart"]))

    # Menu 1: Urutkan menu dari termurah (sort_records) dan hitung statistik harga (calculate_summary_stats).
    def show_menu() -> None:
        sorted_menu = sort_records(state["menu"], "harga", descending=False)
        _print_menu_table(sorted_menu)
        stats = calculate_summary_stats(state["menu"], "harga")
        print(
            f"  Rata-rata harga: {format_idr(stats['average'])} "
            f"(Min: {format_idr(stats['min'])}, Max: {format_idr(stats['max'])})"
        )

    # Menu 2: Saring menu per kategori (filter_by_field) atau cari nama menu (search_by_keyword).
    def filter_and_search() -> None:
        print("  1. Filter Kategori  2. Cari Nama Menu")
        mode = prompt_int("Pilih mode", min_value=1, max_value=2)
        if mode == 1:
            kategori = prompt_non_empty("Masukkan kategori (Makanan/Minuman)").title()
            results = filter_by_field(state["menu"], "kategori", kategori)
            _print_menu_table(results, f"Kategori '{kategori}'")
        else:
            keyword = prompt_non_empty("Masukkan kata kunci nama menu")
            results = search_by_keyword(state["menu"], "nama", keyword)
            _print_menu_table(results, f"Hasil Cari '{keyword}'")

    # Menu 3: Tambah item pilihan ke keranjang (add_to_cart) lalu tampilkan qty terbaru.
    def add_cart_item() -> None:
        _print_menu_table(state["menu"])
        id_menu = prompt_non_empty("Masukkan ID Menu (misal M01)").upper()
        qty = prompt_int("Masukkan jumlah (qty)", min_value=1)
        try:
            state["cart"] = add_to_cart(state["menu"], state["cart"], id_menu, qty)
            print("Item berhasil ditambahkan ke keranjang.")
            _print_item_qty_feedback(id_menu)
        except ValueError as err:
            print(f"Gagal: {err}")

    # Menu 4: Ubah atau tambah qty item di keranjang (bisa pilih ID/nomor baris; otomatis tambah jika belum ada).
    def edit_cart_item() -> None:
        _print_receipt(compute_checkout(state["cart"]))
        if not state["cart"]:
            print("  Gunakan menu 3 untuk menambah item ke keranjang terlebih dahulu.")
            return

        raw_target = prompt_non_empty("Masukkan ID Menu atau Nomor Baris (misal M01 atau 1)")
        resolved_id = _resolve_cart_id(state["cart"], raw_target)
        if not resolved_id:
            candidate_id = raw_target.strip().upper()
            in_menu = filter_by_field(state["menu"], "id_menu", candidate_id)
            if in_menu:
                print(f"  Menu '{in_menu[0]['nama']}' ({candidate_id}) belum ada di keranjang.")
                add_qty = prompt_int("Masukkan jumlah untuk ditambahkan (0 untuk batal)", min_value=0)
                if add_qty > 0:
                    state["cart"] = add_to_cart(state["menu"], state["cart"], candidate_id, add_qty)
                    print("Item berhasil ditambahkan ke keranjang.")
                    _print_item_qty_feedback(candidate_id)
                return
            print(f"Gagal: Item '{raw_target}' tidak ditemukan di keranjang.")
            return

        current_item = filter_by_field(state["cart"], "id_menu", resolved_id)[0]
        print(
            f"  Dipilih: {current_item['nama']} (ID: {resolved_id}, Qty saat ini: {current_item['qty']} pcs)"
        )
        print("  1. Tambah Qty (+jumlah)  2. Ubah ke Qty Baru (set nilai baru)")
        mode_choice = prompt_int("Pilih aksi", min_value=1, max_value=2)
        if mode_choice == 1:
            delta_qty = prompt_int("Masukkan jumlah tambahan (+qty)", min_value=1)
            state["cart"] = update_cart_quantity(state["cart"], resolved_id, delta_qty, mode="add")
        else:
            new_qty = prompt_int("Masukkan qty baru (0 untuk hapus)", min_value=0)
            state["cart"] = update_cart_quantity(state["cart"], resolved_id, new_qty, mode="set")

        print("Keranjang berhasil diperbarui.")
        _print_item_qty_feedback(resolved_id)

    # Menu 5: Hapus item dari keranjang menggunakan remove_by_id berdasarkan ID atau nomor baris.
    def delete_cart_item() -> None:
        _print_receipt(compute_checkout(state["cart"]))
        if not state["cart"]:
            return
        raw_target = prompt_non_empty("Masukkan ID Menu atau Nomor Baris yang ingin dihapus")
        resolved_id = _resolve_cart_id(state["cart"], raw_target)
        if not resolved_id:
            print(f"Gagal: Item '{raw_target}' tidak ditemukan di keranjang.")
            return
        state["cart"] = remove_by_id(state["cart"], "id_menu", resolved_id)
        print(f"Item '{resolved_id}' dihapus dari keranjang.")
        _print_receipt(compute_checkout(state["cart"]))

    # Menu 6: Tampilkan struk ringkasan keranjang dan total bayar akhir.
    def checkout_action() -> None:
        _print_receipt(compute_checkout(state["cart"]))

    # Menu 7: Tambahkan menu baru ke daftar katalog kantin via add_menu_item.
    def add_menu_action() -> None:
        nama = prompt_non_empty("Nama menu baru")
        kategori = prompt_non_empty("Kategori (Makanan/Minuman)")
        harga = prompt_float("Harga (Rp)", min_value=500.0)
        try:
            state["menu"] = add_menu_item(state["menu"], nama, kategori, harga)
            print("Menu baru berhasil ditambahkan ke katalog kantin.")
            _print_menu_table(state["menu"])
        except ValueError as err:
            print(f"Gagal: {err}")

    run_menu_loop(
        "KASIR KANTIN INTERAKTIF",
        [
            ("Lihat Semua Menu & Statistik Harga", show_menu),
            ("Filter Kategori / Cari Menu", filter_and_search),
            ("Tambah Item ke Keranjang", add_cart_item),
            ("Ubah / Tambah Jumlah Item Keranjang", edit_cart_item),
            ("Hapus Item dari Keranjang", delete_cart_item),
            ("Lihat Keranjang & Total Belanja", checkout_action),
            ("Tambah Menu Kantin Baru", add_menu_action),
        ],
    )
