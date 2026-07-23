"""Where snapshots come from.

gcphelpit is *mock-first*: it operates on a plain JSON "snapshot" of a project's
resources. The MockProvider loads one from disk, so the whole tool runs and is
fully testable with zero cloud access. A real GCP adapter can be added later
behind the same ``Provider`` interface without touching the checks or CLI.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

# Top-level keys a snapshot may contain. Checks tolerate missing keys, so a
# partial snapshot is fine — you only pay for what you collect.
SNAPSHOT_KEYS = (
    "project_id",
    "buckets",
    "firewalls",
    "instances",
    "disks",
    "addresses",
    "service_accounts",
    "iam_policy",
    "sql_instances",
    "budgets",
)


class SnapshotError(Exception):
    """Raised when a snapshot cannot be loaded or is malformed."""


class Provider(Protocol):
    def snapshot(self) -> dict: ...


class MockProvider:
    """Loads a snapshot from a JSON file on disk."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def snapshot(self) -> dict:
        if not self.path.exists():
            raise SnapshotError(f"snapshot file not found: {self.path}")
        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError as exc:
            raise SnapshotError(f"invalid JSON in {self.path}: {exc}") from exc
        if not isinstance(data, dict):
            raise SnapshotError(f"snapshot must be a JSON object, got {type(data).__name__}")
        return data


def bundled_fixture(name: str) -> Path:
    """Path to a fixture shipped in the repo (used for the demo/quickstart)."""
    root = Path(__file__).resolve().parents[2]
    return root / "fixtures" / name
