import sqlite3
from dataclasses import dataclass
from typing import Any

from app.config import APP_DB
from app.services.aquarium_load import calculate_tank_load


class AquariumUpdateError(ValueError):
    pass


@dataclass
class AquariumUpdateResult:
    success: bool
    message: str
    aquarium: dict[str, Any]
    compatibility: dict[str, Any]


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(APP_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def validate_aquarium_data(name: str, volume: float | int) -> None:
    if not isinstance(name, str) or not name.strip():
        raise AquariumUpdateError("Akvariumo pavadinimas yra privalomas.")

    try:
        normalized_volume = float(volume)
    except (TypeError, ValueError) as exc:
        raise AquariumUpdateError("Akvariumo litrai turi būti skaičius.") from exc

    if normalized_volume <= 0:
        raise AquariumUpdateError("Akvariumo litrai turi būti didesni už 0.")


def get_aquarium_by_id(aquarium_id: int) -> dict[str, Any]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, aquarium_name, volume FROM aquarium WHERE id = ?",
            (aquarium_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise AquariumUpdateError("Akvariumas nerastas.")

        return {
            "id": row["id"],
            "name": row["aquarium_name"],
            "volume": row["volume"],
        }
    finally:
        conn.close()


def build_indicator(status: str) -> dict[str, str]:
    mapping = {
        "safe": {
            "status": "safe",
            "label": "Suderinama",
            "color": "green",
        },
        "warning": {
            "status": "warning",
            "label": "Atsargiai",
            "color": "yellow",
        },
    }
    return mapping.get(
        status,
        {
            "status": "unknown",
            "label": "Nežinoma",
            "color": "grey",
        },
    )


def update_aquarium(aquarium_id: int, name: str, volume: float | int) -> dict[str, Any]:
    validate_aquarium_data(name, volume)
    normalized_name = name.strip()
    normalized_volume = float(volume)

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM aquarium WHERE id = ?", (aquarium_id,))
        if not cursor.fetchone():
            raise AquariumUpdateError("Akvariumas nerastas.")

        cursor.execute(
            """
            UPDATE aquarium
            SET aquarium_name = ?, volume = ?
            WHERE id = ?
            """,
            (normalized_name, normalized_volume, aquarium_id),
        )
        conn.commit()
    finally:
        conn.close()

    updated_aquarium = get_aquarium_by_id(aquarium_id)
    load_result = calculate_tank_load(aquarium_id)

    return {
        "success": True,
        "message": "Akvariumo parametrai sėkmingai atnaujinti.",
        "aquarium": updated_aquarium,
        "compatibility": {
            "indicator": build_indicator(load_result.get("status")),
            "load": load_result,
        },
    }
