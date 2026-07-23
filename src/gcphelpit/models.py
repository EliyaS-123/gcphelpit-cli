"""Core data types shared across the scanner."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import List


class Severity(enum.IntEnum):
    """Ordered so severities compare and sort naturally (CRITICAL is highest)."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def parse(cls, value: str) -> "Severity":
        try:
            return cls[value.strip().upper()]
        except KeyError as exc:  # pragma: no cover - defensive
            valid = ", ".join(s.name.lower() for s in cls)
            raise ValueError(f"unknown severity {value!r}; choose one of {valid}") from exc

    @property
    def label(self) -> str:
        return self.name.lower()


class Category(enum.Enum):
    SECURITY = "security"
    IAM = "iam"
    COST = "cost"
    RELIABILITY = "reliability"

    @classmethod
    def parse(cls, value: str) -> "Category":
        try:
            return cls(value.strip().lower())
        except ValueError as exc:
            valid = ", ".join(c.value for c in cls)
            raise ValueError(f"unknown category {value!r}; choose one of {valid}") from exc


@dataclass(frozen=True)
class ResourceRef:
    """Identifies the specific resource a finding is about."""

    kind: str
    name: str


@dataclass
class Detail:
    """What a check yields for a single offending resource."""

    resource: ResourceRef
    message: str
    recommendation: str


@dataclass
class Finding:
    """A fully-resolved issue: check metadata + the offending resource."""

    check_id: str
    title: str
    category: Category
    severity: Severity
    resource: ResourceRef
    message: str
    recommendation: str
    references: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "title": self.title,
            "category": self.category.value,
            "severity": self.severity.label,
            "resource": {"kind": self.resource.kind, "name": self.resource.name},
            "message": self.message,
            "recommendation": self.recommendation,
            "references": list(self.references),
        }
