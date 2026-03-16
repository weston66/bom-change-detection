import json
import os

SNAPSHOT_FILE = "bom_snapshot.json"


def load_snapshot() -> dict:
    if not os.path.exists(SNAPSHOT_FILE):
        return {}
    with open(SNAPSHOT_FILE, "r") as f:
        return json.load(f)


def save_snapshot(bom: dict):
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(bom, f, indent=2, default=str)


def bom_to_dict(rows) -> dict:
    """Convert BOM rows into a dict keyed by bom_id for easy diffing."""
    return {
        row["bom_id"]: {
            "parent_part": row["parent_part"],
            "child_part": row["child_part"],
            "quantity": str(row["quantity"]),
            "unit_of_measure": row["unit_of_measure"],
            "revision": row["revision"],
            "effective_date": str(row["effective_date"]),
        }
        for row in rows
    }
