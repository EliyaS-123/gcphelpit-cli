from gcphelpit.engine import scan
from gcphelpit.models import Category, Severity


def test_category_filter_only_runs_matching_checks(insecure_snapshot):
    result = scan(insecure_snapshot, categories=[Category.COST])
    assert result.findings
    assert {f.category for f in result.findings} == {Category.COST}


def test_min_severity_excludes_lower_severity_checks(insecure_snapshot):
    result = scan(insecure_snapshot, min_severity=Severity.HIGH)
    assert result.findings
    assert all(f.severity >= Severity.HIGH for f in result.findings)


def test_findings_sorted_most_severe_first(insecure_snapshot):
    result = scan(insecure_snapshot)
    severities = [f.severity for f in result.sorted_findings()]
    assert severities == sorted(severities, reverse=True)


def test_max_severity_and_counts(insecure_snapshot):
    result = scan(insecure_snapshot)
    counts = result.counts_by_severity()
    assert sum(counts.values()) == len(result.findings)
    assert result.max_severity() == max(f.severity for f in result.findings)


def test_max_severity_is_none_when_clean(clean_snapshot):
    assert scan(clean_snapshot).max_severity() is None
