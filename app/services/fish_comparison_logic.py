"""English-only service helpers for the fish comparison UI."""

from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from app.config import APP_DB
    from app.database.db_setup import create_tables
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from app.config import APP_DB
    from app.database.db_setup import create_tables


MIN_FISH_TO_COMPARE = 2
MAX_FISH_TO_COMPARE = 5


class FishComparisonError(ValueError):
    """Raised when the fish comparison request is invalid."""


@dataclass(frozen=True)
class FishRecord:
    id: int
    fish_name: str
    aggression: str
    size: float
    temp_min: float
    temp_max: float
    ph_min: float
    ph_max: float


AGGRESSION_ORDER = {
    "rami": 1,
    "peaceful": 1,
    "low": 1,
    "taiki": 1,
    "semi aggressive": 2,
    "semi_aggressive": 2,
    "semi-aggressive": 2,
    "medium": 2,
    "pusiau agresyvi": 2,
    "pusiau_agresyvi": 2,
    "territorial": 2,
    "teritorine": 2,
    "teritorinee": 2,
    "teritorine ": 2,
    "teritorine.": 2,
    "teritorine,": 2,
    "teritorine-": 2,
    "teritorinė": 2,
    "teritorinä—": 2,
    "aggressive": 3,
    "high": 3,
    "aukstas": 3,
    "aukštas": 3,
    "aukå¡tas": 3,
    "agresyvi": 3,
    "predatory": 3,
    "plesri": 3,
    "plėšri": 3,
    "plä—å¡ri": 3,
}

SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}
STATUS_LABELS = {
    "ok": "Compatibility looks good.",
    "warning": "There are some notable differences.",
    "critical": "There are major compatibility conflicts.",
}


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables() -> None:
    create_tables()


def _normalize_aggression(value: str) -> tuple[int, str]:
    normalized = (value or "").strip().lower()
    score = AGGRESSION_ORDER.get(normalized, 0)
    labels = {
        1: "Peaceful",
        2: "Semi-aggressive / territorial",
        3: "Aggressive",
        0: "Unknown",
    }
    return score, labels[score]


def _serialize_fish(row: sqlite3.Row) -> FishRecord:
    return FishRecord(
        id=int(row["id"]),
        fish_name=str(row["fish_name"]),
        aggression=str(row["aggression"]),
        size=float(row["size"]),
        temp_min=float(row["temp_min"]),
        temp_max=float(row["temp_max"]),
        ph_min=float(row["ph_min"]),
        ph_max=float(row["ph_max"]),
    )


def search_fish_candidates(
    search_text: str = "",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    ensure_tables()

    query = """
        SELECT id, fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max
        FROM fish_list
        WHERE fish_name LIKE ? COLLATE NOCASE
        ORDER BY fish_name COLLATE NOCASE ASC
    """
    parameters: list[Any] = [f"%{search_text.strip()}%"]

    if limit is not None:
        query += "\nLIMIT ?"
        parameters.append(limit)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, tuple(parameters))
        rows = cursor.fetchall()
        return [_build_fish_card(_serialize_fish(row)) for row in rows]
    finally:
        conn.close()


def _fetch_fish_by_ids(selected_ids: list[int]) -> list[FishRecord]:
    if not selected_ids:
        return []

    placeholders = ",".join("?" for _ in selected_ids)
    query = f"""
        SELECT id, fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max
        FROM fish_list
        WHERE id IN ({placeholders})
    """

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, tuple(selected_ids))
        rows = cursor.fetchall()
        fish_by_id = {int(row["id"]): _serialize_fish(row) for row in rows}
        return [fish_by_id[fish_id] for fish_id in selected_ids if fish_id in fish_by_id]
    finally:
        conn.close()


def _validate_selected_ids(selected_ids: list[int]) -> list[int]:
    if not isinstance(selected_ids, list):
        raise FishComparisonError("Fish comparison expects a list of fish IDs.")

    normalized_ids: list[int] = []
    seen: set[int] = set()
    for raw_value in selected_ids:
        try:
            fish_id = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise FishComparisonError("Each fish ID must be numeric.") from exc

        if fish_id in seen:
            continue

        seen.add(fish_id)
        normalized_ids.append(fish_id)

    if len(normalized_ids) < MIN_FISH_TO_COMPARE:
        raise FishComparisonError("Select at least 2 fish for comparison.")

    if len(normalized_ids) > MAX_FISH_TO_COMPARE:
        raise FishComparisonError("Select no more than 5 fish for comparison.")

    return normalized_ids


def _build_fish_card(fish: FishRecord) -> dict[str, Any]:
    aggression_score, aggression_label = _normalize_aggression(fish.aggression)
    return {
        "id": fish.id,
        "name": fish.fish_name,
        "selected": False,
        "can_add_to_aquarium": True,
        "parameters": {
            "temperature": {
                "label": "Temperature Range",
                "value": f"{fish.temp_min:g}-{fish.temp_max:g} C",
                "min": fish.temp_min,
                "max": fish.temp_max,
            },
            "ph": {
                "label": "pH Range",
                "value": f"{fish.ph_min:g}-{fish.ph_max:g}",
                "min": fish.ph_min,
                "max": fish.ph_max,
            },
            "size": {
                "label": "Maximum Size",
                "value": f"{fish.size:g} cm",
                "numeric": fish.size,
            },
            "aggression": {
                "label": "Aggression Level",
                "value": aggression_label,
                "score": aggression_score,
                "raw": fish.aggression,
            },
        },
    }


def _build_range_result(
    parameter_key: str,
    label: str,
    values: list[tuple[float, float]],
    unit: str,
    narrow_overlap_threshold: float,
) -> dict[str, Any]:
    overlap_min = max(value[0] for value in values)
    overlap_max = min(value[1] for value in values)
    minimum = min(value[0] for value in values)
    maximum = max(value[1] for value in values)

    if overlap_min > overlap_max:
        severity = "critical"
        message = f"There is no shared {label.lower()}."
        significant = True
        overlap = None
    else:
        overlap_width = overlap_max - overlap_min
        overlap = {
            "min": overlap_min,
            "max": overlap_max,
            "value": f"{overlap_min:g}-{overlap_max:g}{unit}",
        }
        if overlap_width < narrow_overlap_threshold:
            severity = "warning"
            message = f"The shared {label.lower()} is very narrow."
            significant = True
        else:
            severity = "info"
            message = f"There is a shared {label.lower()}."
            significant = False

    return {
        "parameter": parameter_key,
        "label": label,
        "severity": severity,
        "significant_difference": significant,
        "message": message,
        "global_range": f"{minimum:g}-{maximum:g}{unit}",
        "overlap": overlap,
    }


def _build_size_result(fish: list[FishRecord]) -> dict[str, Any]:
    sizes = [item.size for item in fish]
    min_size = min(sizes)
    max_size = max(sizes)
    ratio = float("inf") if min_size == 0 else max_size / min_size

    if ratio >= 3:
        severity = "critical"
        message = "The size difference between these fish is very large."
        significant = True
    elif ratio >= 2:
        severity = "warning"
        message = "The fish sizes differ noticeably."
        significant = True
    else:
        severity = "info"
        message = "The fish sizes are similar."
        significant = False

    return {
        "parameter": "size",
        "label": "Maximum Size",
        "severity": severity,
        "significant_difference": significant,
        "message": message,
        "global_range": f"{min_size:g}-{max_size:g} cm",
        "ratio": round(ratio, 2) if ratio != float("inf") else None,
    }


def _build_aggression_result(fish: list[FishRecord]) -> dict[str, Any]:
    scores: list[int] = []
    raw_values: list[str] = []
    for item in fish:
        score, label = _normalize_aggression(item.aggression)
        scores.append(score)
        raw_values.append(label)

    score_min = min(scores)
    score_max = max(scores)
    difference = score_max - score_min

    if score_max == 3 and score_min == 1:
        severity = "critical"
        message = "The selection mixes peaceful and aggressive fish."
        significant = True
    elif difference >= 1:
        severity = "warning"
        message = "The aggression levels differ."
        significant = True
    else:
        severity = "info"
        message = "The aggression levels are similar."
        significant = False

    return {
        "parameter": "aggression",
        "label": "Aggression Level",
        "severity": severity,
        "significant_difference": significant,
        "message": message,
        "values": raw_values,
    }


def _collect_highlights(parameter_results: list[dict[str, Any]]) -> list[dict[str, str]]:
    highlights: list[dict[str, str]] = []
    for result in parameter_results:
        if result["significant_difference"]:
            highlights.append(
                {
                    "parameter": result["parameter"],
                    "label": result["label"],
                    "severity": result["severity"],
                    "message": result["message"],
                }
            )
    return highlights


def _overall_status(parameter_results: list[dict[str, Any]]) -> str:
    highest = max(SEVERITY_ORDER[item["severity"]] for item in parameter_results)
    if highest == SEVERITY_ORDER["critical"]:
        return "critical"
    if highest == SEVERITY_ORDER["warning"]:
        return "warning"
    return "ok"


def _build_table_rows(
    fish_cards: list[dict[str, Any]],
    parameter_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results_by_parameter = {result["parameter"]: result for result in parameter_results}
    row_order = ["temperature", "ph", "size", "aggression"]

    table_rows: list[dict[str, Any]] = []
    for parameter_key in row_order:
        result = results_by_parameter[parameter_key]
        table_rows.append(
            {
                "parameter": parameter_key,
                "label": result["label"],
                "severity": result["severity"],
                "significant_difference": result["significant_difference"],
                "insight": result["message"],
                "summary": result.get("overlap", {}).get("value")
                if result.get("overlap")
                else result.get("global_range", "-"),
                "fish_values": [
                    {
                        "id": card["id"],
                        "name": card["name"],
                        "value": card["parameters"][parameter_key]["value"],
                    }
                    for card in fish_cards
                ],
            }
        )
    return table_rows


def compare_selected_fish(selected_ids: list[int]) -> dict[str, Any]:
    ensure_tables()
    normalized_ids = _validate_selected_ids(selected_ids)
    fish = _fetch_fish_by_ids(normalized_ids)

    if len(fish) != len(normalized_ids):
        found_ids = {item.id for item in fish}
        missing_ids = [fish_id for fish_id in normalized_ids if fish_id not in found_ids]
        raise FishComparisonError(
            f"Fish not found for ID(s): {', '.join(map(str, missing_ids))}."
        )

    fish_cards = [_build_fish_card(item) for item in fish]
    for card in fish_cards:
        card["selected"] = True

    parameter_results = [
        _build_range_result(
            parameter_key="temperature",
            label="Temperature Range",
            values=[(item.temp_min, item.temp_max) for item in fish],
            unit=" C",
            narrow_overlap_threshold=2.0,
        ),
        _build_range_result(
            parameter_key="ph",
            label="pH Range",
            values=[(item.ph_min, item.ph_max) for item in fish],
            unit="",
            narrow_overlap_threshold=0.5,
        ),
        _build_size_result(fish),
        _build_aggression_result(fish),
    ]

    highlights = _collect_highlights(parameter_results)
    overall_status = _overall_status(parameter_results)

    return {
        "success": True,
        "selected_count": len(fish_cards),
        "selected_fish": fish_cards,
        "parameters": parameter_results,
        "table_rows": _build_table_rows(fish_cards, parameter_results),
        "highlights": highlights,
        "overall_status": overall_status,
        "overall_label": STATUS_LABELS[overall_status],
        "actions": {
            "add_to_aquarium_enabled": True,
            "available_fish_ids": [item.id for item in fish],
            "message": "You can add a compared fish directly to an aquarium.",
        },
    }


def get_comparison_view_model(selected_ids: list[int]) -> dict[str, Any]:
    comparison = compare_selected_fish(selected_ids)
    return {
        "window_title": "Fish Comparison",
        "reload_required": False,
        "comparison": comparison,
    }


if __name__ == "__main__":
    demo_ids = [1, 2]
    try:
        from pprint import pprint

        pprint(get_comparison_view_model(demo_ids))
    except FishComparisonError as exc:
        print(f"Error: {exc}")
