"""Runs the check catalog over a snapshot and collects findings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from .catalog import Check, all_checks
from .models import Category, Finding, Severity


@dataclass
class ScanResult:
    project_id: str
    findings: List[Finding] = field(default_factory=list)
    checks_run: int = 0

    def sorted_findings(self) -> List[Finding]:
        """Most severe first, then grouped by check id."""
        return sorted(
            self.findings,
            key=lambda f: (-int(f.severity), f.category.value, f.check_id),
        )

    def counts_by_severity(self) -> "dict[Severity, int]":
        counts = {s: 0 for s in Severity}
        for f in self.findings:
            counts[f.severity] += 1
        return counts

    def max_severity(self) -> Optional[Severity]:
        return max((f.severity for f in self.findings), default=None)


def scan(
    snapshot: dict,
    *,
    categories: Optional[Iterable[Category]] = None,
    min_severity: Optional[Severity] = None,
    checks: Optional[Iterable[Check]] = None,
) -> ScanResult:
    """Evaluate checks against ``snapshot``.

    ``categories``/``min_severity`` narrow which checks run and which findings
    are kept. ``checks`` overrides the catalog (used in tests).
    """
    selected = list(checks) if checks is not None else all_checks()
    cat_set = set(categories) if categories else None

    result = ScanResult(project_id=snapshot.get("project_id", "unknown"))
    for chk in selected:
        if cat_set is not None and chk.category not in cat_set:
            continue
        if min_severity is not None and chk.severity < min_severity:
            continue
        result.checks_run += 1
        result.findings.extend(chk.run(snapshot))
    return result
