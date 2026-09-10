"""Teacher-approved, installed-code policies; never loaded from a delivery/root.

Published policy versions must remain immutable for historical result readers.
Callers validate revision bytes before matching the material fingerprint.
"""
from scripts import student_delivery_store as delivery


def accessory_policy(revision: dict) -> dict | None:
    materials = {"activity": revision["activity"], "assets": [
        {"path": entry["path"], "sha256": entry["sha256"]} for entry in revision["assets"]]}
    fingerprint = delivery.content_digest(delivery._json_bytes(materials))
    if fingerprint != "dc16ae5bb215d90a089721afbaf2ec7434d4327ef666209416707867ce1ced5b":
        return None
    # A fresh value prevents callers from mutating the installed policy in place.
    return {
        "id": "python-m04-stdio-accessory.v1",
        "origin": {
            "repository": "TheBitPoets/python-docente",
            "revision": "1bc6d712c9e44d482846cc3c290b66e979c24905",
            "activity_path": "activities/python/py2-activity-b-input-somma-001/activity.json",
        },
        "materials_digest": fingerprint,
        "language": "python",
        "tests_total": 3,
        "source": {"asset_path": "starter/main.py", "target_path": "main.py"},
        "required_accessory": {"asset_path": "student/GUIDA.md", "target_path": "GUIDA.md",
                               "comparison": "identical_bytes", "worker": False},
        "private_assets": ["teacher/README.md"],
        "extra_files": "reject",
    }
