from __future__ import annotations

# Ekspor seluruh 10 pure function agar bisa diimpor langsung lewat `from fungsio_lib import ...`.
from fungsio_lib.core import (
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

__all__ = [
    "add_record",
    "filter_by_field",
    "search_by_keyword",
    "update_by_id",
    "remove_by_id",
    "transform_records",
    "sum_by_field",
    "group_by_field",
    "sort_records",
    "calculate_summary_stats",
]
