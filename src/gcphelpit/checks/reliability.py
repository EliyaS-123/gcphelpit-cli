"""Reliability / best-practice checks."""

from __future__ import annotations

from typing import Iterator

from ..catalog import check
from ..models import Category, Detail, ResourceRef, Severity


@check(
    id="REL001",
    title="Cloud SQL instance has no automated backups",
    category=Category.RELIABILITY,
    severity=Severity.HIGH,
    references=["https://cloud.google.com/sql/docs/mysql/backup-recovery/backups"],
)
def sql_no_backups(snapshot: dict) -> Iterator[Detail]:
    for sql in snapshot.get("sql_instances", []):
        if not sql.get("backups_enabled", False):
            yield Detail(
                resource=ResourceRef("sql.instance", sql.get("name", "?")),
                message="Automated backups are disabled; data loss would be unrecoverable.",
                recommendation="Enable automated backups and point-in-time recovery.",
            )


@check(
    id="REL002",
    title="Instance has deletion protection disabled",
    category=Category.RELIABILITY,
    severity=Severity.LOW,
    references=["https://cloud.google.com/compute/docs/instances/preventing-accidental-vm-deletion"],
)
def no_deletion_protection(snapshot: dict) -> Iterator[Detail]:
    for inst in snapshot.get("instances", []):
        # Only flag instances the snapshot marks as production.
        if inst.get("labels", {}).get("env") == "prod" and not inst.get("deletion_protection", False):
            yield Detail(
                resource=ResourceRef("compute.instance", inst.get("name", "?")),
                message="Production instance can be deleted without a guard.",
                recommendation="Enable deletion protection on production instances.",
            )


@check(
    id="REL003",
    title="Cloud SQL instance is not highly available (single zone)",
    category=Category.RELIABILITY,
    severity=Severity.MEDIUM,
    references=["https://cloud.google.com/sql/docs/mysql/high-availability"],
)
def sql_single_zone(snapshot: dict) -> Iterator[Detail]:
    for sql in snapshot.get("sql_instances", []):
        if sql.get("labels", {}).get("env") == "prod" and sql.get("availability_type") != "REGIONAL":
            yield Detail(
                resource=ResourceRef("sql.instance", sql.get("name", "?")),
                message="Production database runs in a single zone; a zonal outage causes downtime.",
                recommendation="Set availability type to REGIONAL for automatic failover.",
            )
