from __future__ import annotations

from copy import deepcopy
from functools import reduce
from typing import Any, Callable

Record = dict[str, Any]
Collection = list[Record]


def _validate_collection(collection: Collection) -> None:
    """Validate that collection is a list of dictionary records.

    Validating at the library boundary enforces predictable failure early
    before pure transformations execute downstream.
    """
    if not isinstance(collection, list):
        raise TypeError("collection must be a list of dict records")
    for idx, item in enumerate(collection):
        if not isinstance(item, dict):
            raise TypeError(f"collection item at index {idx} must be a dict")


def _to_numeric(value: Any, field_name: str) -> float:
    """Convert a scalar field value to float while rejecting booleans.

    Python treats bool as a subclass of int, so rejecting booleans explicitly
    prevents accidental True/False arithmetic corruption in numeric aggregations.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"Field '{field_name}' must contain numeric values, got {type(value).__name__}")
    return float(value)


def add_record(collection: Collection, record: Record) -> Collection:
    """Return a new collection with a deep copy of record appended.

    Deep copying prevents caller mutations from leaking into existing state.
    """
    _validate_collection(collection)
    if not isinstance(record, dict):
        raise TypeError("record must be a dict")
    return [deepcopy(item) for item in collection] + [deepcopy(record)]


def filter_by_field(collection: Collection, field: str, value: Any) -> Collection:
    """Return a new collection containing records where field equals value.

    Checking key membership before value comparison avoids falsely matching
    records that omit the field when filtering for None.
    """
    _validate_collection(collection)
    if not isinstance(field, str) or not field:
        raise ValueError("field must be a non-empty string")
    return [
        deepcopy(item)
        for item in collection
        if field in item and item[field] == value
    ]


def search_by_keyword(collection: Collection, field: str, keyword: str) -> Collection:
    """Return records whose field contains keyword (case-insensitive substring).

    Trimming and lowercasing the keyword allows human-friendly CLI searches
    without mutating the underlying stored text casing.
    """
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


def update_by_id(
    collection: Collection,
    id_field: str,
    target_id: Any,
    updates: dict[str, Any],
) -> Collection:
    """Return a new collection with matching records merged with updates.

    Non-matching records are deep-copied untouched, ensuring pure state updates
    that are safe for undo/audit histories or concurrent reads.
    """
    _validate_collection(collection)
    if not isinstance(id_field, str) or not id_field:
        raise ValueError("id_field must be a non-empty string")
    if not isinstance(updates, dict):
        raise TypeError("updates must be a dict")

    updated_collection: Collection = []
    for item in collection:
        copied_item = deepcopy(item)
        if id_field in copied_item and copied_item[id_field] == target_id:
            copied_item = {**copied_item, **deepcopy(updates)}
        updated_collection.append(copied_item)
    return updated_collection


def remove_by_id(collection: Collection, id_field: str, target_id: Any) -> Collection:
    """Return a new collection excluding records whose id_field matches target_id.

    Records missing id_field are preserved so deletion only affects exact matches.
    """
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
    """Apply a pure mapping function to every record and return a new collection.

    Passing a deep copy to transformer prevents accidental in-place mutation of
    source records even if a caller-supplied lambda mutates its argument.
    """
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


def sum_by_field(collection: Collection, numeric_field: str) -> float:
    """Reduce a numeric field across all records into a single floating-point sum.

    Missing or None values are treated as 0.0 so sparse records can still be
    aggregated cleanly without crashing interactive reports.
    """
    _validate_collection(collection)
    if not isinstance(numeric_field, str) or not numeric_field:
        raise ValueError("numeric_field must be a non-empty string")

    def _accumulate(total: float, item: Record) -> float:
        raw_value = item.get(numeric_field, 0.0)
        if raw_value is None:
            return total
        return total + _to_numeric(raw_value, numeric_field)

    return float(reduce(_accumulate, collection, 0.0))


def group_by_field(collection: Collection, key_field: str) -> dict[Any, Collection]:
    """Group deep-copied records into a dictionary keyed by key_field values.

    Preserves insertion order of groups and relative order of records within
    each group for deterministic CLI reporting.
    """
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
            raise TypeError(f"Group key '{group_key}' for field '{key_field}' must be hashable") from exc
    return grouped


def sort_records(
    collection: Collection,
    sort_field: str,
    descending: bool = True,
) -> Collection:
    """Return records sorted by sort_field and annotated with a 1-based 'rank'.

    Records with missing/None sort values fall back to 0 so sorting mixed
    optional records remains predictable while maintaining immutability.
    """
    _validate_collection(collection)
    if not isinstance(sort_field, str) or not sort_field:
        raise ValueError("sort_field must be a non-empty string")

    def _sort_key(item: Record) -> Any:
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
    """Compute count, total, average, min, and max for a numeric field.

    Returns zeroed metrics on empty or non-populated collections so UI layers
    never suffer ZeroDivisionError or ValueError from min()/max().
    """
    _validate_collection(collection)
    if not isinstance(numeric_field, str) or not numeric_field:
        raise ValueError("numeric_field must be a non-empty string")

    values = [
        _to_numeric(item[numeric_field], numeric_field)
        for item in collection
        if numeric_field in item and item[numeric_field] is not None
    ]

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
