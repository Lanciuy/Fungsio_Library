from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

Record = dict[str, Any]
Collection = list[Record]


# Helper validasi tipe koleksi sebelum diproses fungsi library.
def _validate_collection(collection: Collection) -> None:
    """Validasi bahwa input berupa list of dict sebelum diproses."""
    if not isinstance(collection, list):
        raise TypeError("collection must be a list of dict records")
    for idx, item in enumerate(collection):
        if not isinstance(item, dict):
            raise TypeError(f"collection item at index {idx} must be a dict")


# Helper konversi angka sambil menolak bool (karena bool turunan int di Python).
def _to_numeric(value: Any, field_name: str) -> float:
    """Konversi angka ke float sambil menolak bool agar True/False tidak terhitung 1/0."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' must contain numeric values, got {type(value).__name__}")
    return float(value)


# 1. Tambah data baru -> Input: (list, dict baru) | Output: list baru berisi deepcopy data lama + baru.
def add_record(collection: Collection, record: Record) -> Collection:
    """[Fungsi 1] Tambah record baru secara immutable (tidak mengubah list asal)."""
    _validate_collection(collection)
    if not isinstance(record, dict):
        raise TypeError("record must be a dict")
    return [deepcopy(item) for item in collection] + [deepcopy(record)]


# 2. Saring data eksak -> Input: (list, nama field, nilai target) | Output: list record yang cocok.
def filter_by_field(collection: Collection, field: str, value: Any) -> Collection:
    """[Fungsi 2] Saring record yang nilai field-nya sama persis dengan value."""
    _validate_collection(collection)
    if not isinstance(field, str) or not field:
        raise ValueError("field must be a non-empty string")
    return [
        deepcopy(item)
        for item in collection
        if field in item and item[field] == value
    ]


# 3. Cari kata kunci -> Input: (list, field teks, keyword) | Output: list yang mengandung substring (case-insensitive).
def search_by_keyword(collection: Collection, field: str, keyword: str) -> Collection:
    """[Fungsi 3] Cari record berdasarkan substring pada field (case-insensitive)."""
    _validate_collection(collection)
    if not isinstance(field, str) or not field:
        raise ValueError("field must be a non-empty string")
    if not isinstance(keyword, str):
        raise TypeError("keyword must be a string")

    normalized = keyword.strip().lower()
    if not normalized:
        return [deepcopy(item) for item in collection]

    return [
        deepcopy(item)
        for item in collection
        if normalized in str(item.get(field, "")).lower()
    ]


# 4. Ubah data berdasarkan ID -> Input: (list, kolom ID, nilai ID, dict perubahan) | Output: list baru terperbarui.
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

    return [
        {**deepcopy(item), **deepcopy(updates)}
        if id_field in item and item[id_field] == target_id
        else deepcopy(item)
        for item in collection
    ]


# 5. Hapus data berdasarkan ID -> Input: (list, kolom ID, nilai ID) | Output: list baru tanpa record target.
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


# 6. Petakan/hitung atribut turunan -> Input: (list, fungsi lambda/transformer) | Output: list baru hasil pemetaan.
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
        result = transformer(deepcopy(item))
        if not isinstance(result, dict):
            raise TypeError(f"transformer must return a dict for item at index {idx}")
        transformed.append(deepcopy(result))
    return transformed


# 7. Total kolom numerik -> Input: (list, nama kolom angka) | Output: float hasil penjumlahan seluruh baris.
def sum_by_field(collection: Collection, numeric_field: str) -> float:
    """[Fungsi 7] Jumlahkan nilai numerik pada satu field (field None dianggap 0)."""
    _validate_collection(collection)
    if not isinstance(numeric_field, str) or not numeric_field:
        raise ValueError("numeric_field must be a non-empty string")

    return float(
        sum(
            _to_numeric(item[numeric_field], numeric_field)
            for item in collection
            if item.get(numeric_field) is not None
        )
    )


# 8. Kelompokkan data -> Input: (list, nama kolom pengelompok) | Output: dict {nilai_key: [daftar_record]}.
def group_by_field(collection: Collection, key_field: str) -> dict[Any, Collection]:
    """[Fungsi 8] Kelompokkan koleksi data ke dict berdasarkan nilai key_field."""
    _validate_collection(collection)
    if not isinstance(key_field, str) or not key_field:
        raise ValueError("key_field must be a non-empty string")

    grouped: dict[Any, Collection] = {}
    for item in collection:
        group_key = item.get(key_field)
        try:
            grouped.setdefault(group_key, []).append(deepcopy(item))
        except TypeError as exc:
            raise TypeError(f"Group key '{group_key}' for field '{key_field}' must be hashable") from exc
    return grouped


# 9. Urutkan + beri peringkat -> Input: (list, kolom urut, descending) | Output: list terurut berkolom 'rank' (1..N).
def sort_records(
    collection: Collection,
    sort_field: str,
    descending: bool = True,
) -> Collection:
    """[Fungsi 9] Urutkan record berdasarkan sort_field dan sisipkan atribut 'rank' (1..N)."""
    _validate_collection(collection)
    if not isinstance(sort_field, str) or not sort_field:
        raise ValueError("sort_field must be a non-empty string")

    sorted_items = sorted(
        (deepcopy(item) for item in collection),
        key=lambda item: 0 if item.get(sort_field) is None else item.get(sort_field),
        reverse=descending,
    )
    return [
        {**item, "rank": rank}
        for rank, item in enumerate(sorted_items, start=1)
    ]


# 10. Statistik ringkas -> Input: (list, kolom angka) | Output: dict {count, total, average, min, max}.
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

    if not values:
        return dict.fromkeys(("count", "total", "average", "min", "max"), 0.0)

    total = float(sum(values))
    count = float(len(values))
    return {
        "count": count,
        "total": total,
        "average": total / count,
        "min": float(min(values)),
        "max": float(max(values)),
    }
