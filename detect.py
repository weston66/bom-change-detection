import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from db import query, execute
from snapshot import load_snapshot, save_snapshot, bom_to_dict

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack(message: str):
    if not SLACK_WEBHOOK_URL:
        print("No Slack webhook configured.")
        return
    requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)


def log_change(bom_id: str, change_type: str, old_value: dict, new_value: dict):
    execute(
        """
        INSERT INTO bom_audit_log (bom_id, change_type, old_value, new_value, detected_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (bom_id, change_type, str(old_value), str(new_value), datetime.now(timezone.utc)),
    )


def diff_bom(old: dict, new: dict) -> list[dict]:
    changes = []

    added = set(new) - set(old)
    removed = set(old) - set(new)
    common = set(old) & set(new)

    for bom_id in added:
        changes.append({"bom_id": bom_id, "type": "ADDED", "old": {}, "new": new[bom_id]})

    for bom_id in removed:
        changes.append({"bom_id": bom_id, "type": "REMOVED", "old": old[bom_id], "new": {}})

    for bom_id in common:
        if old[bom_id] != new[bom_id]:
            changes.append({"bom_id": bom_id, "type": "MODIFIED", "old": old[bom_id], "new": new[bom_id]})

    return changes


def format_slack_message(changes: list[dict]) -> str:
    lines = [f":memo: *BOM Change Detection - {len(changes)} change(s) detected*"]
    for c in changes[:20]:  # cap at 20 to avoid giant messages
        bom_id = c["bom_id"]
        change_type = c["type"]
        if change_type == "ADDED":
            lines.append(f"  :new: `{bom_id}` ADDED - {c['new']['parent_part']} -> {c['new']['child_part']} (rev {c['new']['revision']})")
        elif change_type == "REMOVED":
            lines.append(f"  :x: `{bom_id}` REMOVED - {c['old']['parent_part']} -> {c['old']['child_part']}")
        elif change_type == "MODIFIED":
            diffs = [k for k in c["new"] if c["old"].get(k) != c["new"][k]]
            lines.append(f"  :pencil2: `{bom_id}` MODIFIED - fields changed: {', '.join(diffs)}")
    if len(changes) > 20:
        lines.append(f"  ... and {len(changes) - 20} more changes.")
    return "\n".join(lines)


def run():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Running BOM change detection...")

    rows = query("SELECT * FROM bom")
    current_bom = bom_to_dict(rows)
    previous_bom = load_snapshot()

    if not previous_bom:
        print("No previous snapshot found. Saving current BOM as baseline.")
        save_snapshot(current_bom)
        print(f"Snapshot saved with {len(current_bom)} BOM entries.")
        return

    changes = diff_bom(previous_bom, current_bom)

    if not changes:
        print("No BOM changes detected.")
    else:
        print(f"{len(changes)} change(s) detected. Logging and alerting...")
        for c in changes:
            log_change(c["bom_id"], c["type"], c["old"], c["new"])
        message = format_slack_message(changes)
        send_slack(message)
        print("Slack alert sent.")

    save_snapshot(current_bom)
    print("Snapshot updated.")


if __name__ == "__main__":
    run()
