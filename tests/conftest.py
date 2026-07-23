import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def insecure_snapshot() -> dict:
    return json.loads((FIXTURES / "insecure_project.json").read_text())


@pytest.fixture
def clean_snapshot() -> dict:
    return json.loads((FIXTURES / "clean_project.json").read_text())
