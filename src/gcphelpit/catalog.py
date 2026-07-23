"""The check registry.

A *check* is a small function that inspects a snapshot and yields a ``Detail``
for every offending resource. The ``@check`` decorator attaches metadata
(id, title, category, severity, references) and registers it. Adding a new
check is therefore a single decorated function — no wiring elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List

from .models import Category, Detail, Finding, Severity

# A check reads a snapshot (plain dict) and yields Details.
CheckFn = Callable[[dict], Iterable[Detail]]


@dataclass
class Check:
    id: str
    title: str
    category: Category
    severity: Severity
    references: List[str]
    fn: CheckFn = field(repr=False)

    def run(self, snapshot: dict) -> Iterator[Finding]:
        for detail in self.fn(snapshot) or []:
            yield Finding(
                check_id=self.id,
                title=self.title,
                category=self.category,
                severity=self.severity,
                resource=detail.resource,
                message=detail.message,
                recommendation=detail.recommendation,
                references=self.references,
            )


_REGISTRY: Dict[str, Check] = {}


def check(
    *,
    id: str,
    title: str,
    category: Category,
    severity: Severity,
    references: Iterable[str] = (),
) -> Callable[[CheckFn], CheckFn]:
    """Register a check. The wrapped function is returned unchanged."""

    def decorator(fn: CheckFn) -> CheckFn:
        if id in _REGISTRY:
            raise ValueError(f"duplicate check id: {id!r}")
        _REGISTRY[id] = Check(
            id=id,
            title=title,
            category=category,
            severity=severity,
            references=list(references),
            fn=fn,
        )
        return fn

    return decorator


def all_checks() -> List[Check]:
    """Every registered check, sorted by id for stable output."""
    _load_builtin_checks()
    return sorted(_REGISTRY.values(), key=lambda c: c.id)


_loaded = False


def _load_builtin_checks() -> None:
    """Import the built-in check modules so their decorators run once."""
    global _loaded
    if _loaded:
        return
    from .checks import cost, iam, reliability, security  # noqa: F401

    _loaded = True
