"""Each check must fire on the insecure fixture and stay silent on the clean one."""

import pytest

from gcphelpit.catalog import all_checks
from gcphelpit.engine import scan
from gcphelpit.models import Category, Detail


def test_clean_snapshot_has_no_findings(clean_snapshot):
    result = scan(clean_snapshot)
    assert result.findings == [], [f.check_id for f in result.findings]


def test_insecure_snapshot_covers_all_categories(insecure_snapshot):
    result = scan(insecure_snapshot)
    categories = {f.category for f in result.findings}
    assert categories == set(Category), categories


@pytest.mark.parametrize("chk", all_checks(), ids=lambda c: c.id)
def test_every_check_fires_on_insecure_fixture(chk, insecure_snapshot):
    """The demo fixture is designed so every built-in check triggers at least once."""
    details = list(chk.fn(insecure_snapshot))
    assert details, f"{chk.id} produced no findings on the insecure fixture"
    for d in details:
        assert isinstance(d, Detail)
        assert d.message and d.recommendation


def test_checks_are_pure_and_tolerate_empty_snapshot():
    """A check must not raise on a snapshot missing every key."""
    for chk in all_checks():
        assert list(chk.fn({})) == []


def test_check_ids_are_unique():
    ids = [c.id for c in all_checks()]
    assert len(ids) == len(set(ids))
