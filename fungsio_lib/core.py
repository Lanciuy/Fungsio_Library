from __future__ import annotations

from copy import deepcopy
from functools import reduce
from typing import Any, Callable

Record = dict[str, Any]
Collection = list[Record]


def _validate_collection(collection: Collection) -> None:
    """Validasi bahwa input berupa list of dict sebelum diproses."""
    if not isinstance(collection, list):
        raise TypeError("collection must be a list of dict records")
    for idx, item in enumerate(collection):
        if not isinstance(item, dict):
            raise TypeError(f"collection item at index {idx} must be a dict")


def _to_numeric(value: Any, field_name: str) -> float:
    """Konversi angka ke float sambil menolak bool agar True/False tidak terhitung 1/0."""
    # Di Python, bool adalah turunan int sehingga wajib ditolak eksplisit.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' must contain numeric values, got {type(value).__name__}")
    return float(value)


def add_record(collection: Collection, record: Record) -> Collection:
    """[Fungsi 1] Tambah record baru secara immutable (tidak mengubah list asal)."""
    _validate_collection(collection)
    if not isinstance(record, dict):
        raise TypeError("record must be a dict")
    # Deep copy menjaga data lama aman dari mutasi referensi dict bersarang.
    return [deepcopy(item) for item in collection] + [deepcopy(record)]


def filter_by_field(collection: Collection, field: str, value: Any) -> Collection:
    """[Fungsi 2] Saring record yang nilai field-nya sama persis dengan value."""
    _validate_collection(collection)
    if not isinstance(field, str) or not field:
        raise ValueError("field must be a non-empty string")
    # Cek keberadaan key lebih dulu agar field yang hilang tidak cocok saat value=None.
    return [
        deepcopy(item)
        for item in collection
        if field in item and item[field] == value
    ]


def search_by_keyword(collection: Collection, field: str, keyword: str) -> Collection:
    """[Fungsi 3] Cari record berdasarkan substring pada field (case-insensitive)."""
    _validate_collection(collection)
    if not isinstance(field, str) or not field:
        raise ValueError("field must be a non-empty string")
    if not isinstance(keyword, str):
        raise TypeError("keyword must be a string")

    normalized = keyword.strip().lower()
    # Keyword kosong mengembalikan seluruh salinan data agar pencarian reset mulus.
    if not normalized:
        return [deepcopy(item) for item in collection]

    return [
        deepcopy(item)
        for item in collection
        if normalized in str(item.get(field, "")).lower()
    ]


def update_by_id(
    collection: Collection,
    id_field: str,
    target_id: Any,
    updates: dict[str, Any],
) -> Collection:
    """[Fungsi 4] Perbarui field pada record ber-ID target secara immutable."""
    _validate_collection(collection)
    if not isinstance(id_field, str) or not id_field:
        raise ValueError("id_field must be a non-empty string")
    if not isinstance(updates, dict):
        raise TypeError("updates must be a dict")

    updated_collection: Collection = []
    for item in collection:
        copied_item = deepcopy(item)
        # Gabungkan salinan lama + updates hanya pada record yang ID-nya cocok.
        if id_field in copied_item and copied_item[id_field] == target_id:
            copied_item = {**copied_item, **deepcopy(updates)}
        updated_collection.append(copied_item)
    return updated_collection


def remove_by_id(collection: Collection, id_field: str, target_id: Any) -> Collection:
    """[Fungsi 5] Hapus record dengan ID target dan kembalikan list baru."""
    _validate_collection(collection)
    if not isinstance(id_field, str) or not id_field:
        raise ValueError("id_field must be a non-empty string")

    return [
        deepcopy(item)
        for item in collection
        if not (id_field in item and item[id_field] == target_id)
    ]


def transform_records(
    collection: Collection,
    transformer: Callable[[Record], Record],
) -> Collection:
    """[Fungsi 6] Higher-order function untuk memetakan/menghitung atribut baru tiap record."""
    _validate_collection(collection)
    if not callable(transformer):
        raise TypeError("transformer must be callable")

    transformed: Collection = []
    for idx, item in enumerate(collection):
        # Kirim deepcopy ke transformer agar fungsi pemanggil tidak merusak data asli.
        result = transformer(deepcopy(item))
        if not isinstance(result, dict):
            raise TypeError(f"transformer must return a dict for item at index {idx}")
        transformed.append(deepcopy(result))
    return transformed


def sum_by_field(collection: Collection, numeric_field: str) -> float:
    """[Fungsi 7] Jumlahkan nilai numerik pada satu field menggunakan reduce."""
    _validate_collection(collection)
    if not isinstance(numeric_field, str) or not numeric_field:
        raise ValueError("numeric_field must be a non-empty string")

    def _accumulate(total: float, item: Record) -> float:
        # Field kosong/None diperlakukan 0.0 agar agregasi data parsial tetap aman.
        raw_value = item.get(numeric_field, 0.0)
        if raw_value is None:
            return total
        return total + _to_numeric(raw_value, numeric_field)

    return float(reduce(_accumulate, collection, 0.0))


def group_by_field(collection: Collection, key_field: str) -> dict[Any, Collection]:
    """[Fungsi 8] Kelompokkan koleksi data ke dict berdasarkan nilai key_field."""
    _validate_collection(collection)
    if not isinstance(key_field, str) or not key_field:
        raise ValueError("key_field must be a non-empty string")

    grouped: dict[Any, Collection] = {}
    for item in collection:
        group_key = item.get(key_field)
        try:
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(deepcopy(item))
        except TypeError as exc:
            # Nilai key harus hashable (seperti str/int) agar bisa jadi key dictionary.
            raise TypeError(f"Group key '{group_key}' for field '{key_field}' must be hashable") from exc
    return grouped


def sort_records(
    collection: Collection,
    sort_field: str,
    descending: bool = True,
) -> Collection:
    """[Fungsi 9] Urutkan record berdasarkan sort_field dan sisipkan atribut 'rank' (1..N)."""
    _validate_collection(collection)
    if not isinstance(sort_field, str) or not sort_field:
        raise ValueError("sort_field must be a non-empty string")

    def _sort_key(item: Record) -> Any:
        # Nilai None diganti 0 agar perbandingan sort tidak memicu TypeError.
        val = item.get(sort_field)
        return 0 if val is None else val

    sorted_items = sorted(
        (deepcopy(item) for item in collection),
        key=_sort_key,
        reverse=descending,
    )
    return [
        {**item, "rank": rank}
        for rank, item in enumerate(sorted_items, start=1)
    ]


def calculate_summary_stats(collection: Collection, numeric_field: str) -> dict[str, float]:
    """[Fungsi 10] Hitung ringkasan statistik (count, total, average, min, max) field numerik."""
    _validate_collection(collection)
    if not isinstance(numeric_field, str) or not numeric_field:
        raise ValueError("numeric_field must be a non-empty string")

    values = [
        _to_numeric(item[numeric_field], numeric_field)
        for item in collection
        if numeric_field in item and item[numeric_field] is not None
    ]

    # Kembalikan nol semua saat koleksi kosong agar pemanggil terhindar dari ZeroDivisionError.
    if not values:
        return {
            "count": 0.0,
            "total": 0.0,
            "average": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    total = float(sum(values))
    count = float(len(values))
    return {
        "count": count,
        "total": total,
        "average": total / count,
        "min": float(min(values)),
        "max": float(max(values)),
    }
