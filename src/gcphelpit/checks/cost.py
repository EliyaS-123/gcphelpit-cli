"""Cost / waste checks."""

from __future__ import annotations

from typing import Iterator

from ..catalog import check
from ..models import Category, Detail, ResourceRef, Severity


@check(
    id="COST001",
    title="Unattached persistent disk",
    category=Category.COST,
    severity=Severity.LOW,
    references=["https://cloud.google.com/compute/docs/disks"],
)
def unattached_disks(snapshot: dict) -> Iterator[Detail]:
    for disk in snapshot.get("disks", []):
        if not disk.get("users"):
            size = disk.get("size_gb", "?")
            yield Detail(
                resource=ResourceRef("compute.disk", disk.get("name", "?")),
                message=f"Disk ({size} GB) is not attached to any instance but still incurs storage cost.",
                recommendation="Snapshot then delete the disk if it is no longer needed.",
            )


@check(
    id="COST002",
    title="Reserved static IP address is unused",
    category=Category.COST,
    severity=Severity.LOW,
    references=["https://cloud.google.com/vpc/docs/reserve-static-external-ip-address"],
)
def unused_addresses(snapshot: dict) -> Iterator[Detail]:
    for addr in snapshot.get("addresses", []):
        if addr.get("status") == "RESERVED" and not addr.get("users"):
            yield Detail(
                resource=ResourceRef("compute.address", addr.get("name", "?")),
                message="Static IP is reserved but not attached; idle static IPs are billed.",
                recommendation="Release the static IP if it is no longer required.",
            )


@check(
    id="COST003",
    title="Instance stopped but disks still allocated",
    category=Category.COST,
    severity=Severity.LOW,
    references=["https://cloud.google.com/compute/docs/instances/instance-life-cycle"],
)
def stopped_instances(snapshot: dict) -> Iterator[Detail]:
    for inst in snapshot.get("instances", []):
        if inst.get("status") == "TERMINATED":
            yield Detail(
                resource=ResourceRef("compute.instance", inst.get("name", "?")),
                message="Instance is stopped; attached disks and reserved IPs continue to be billed.",
                recommendation="Delete the instance (keeping a snapshot) if it is no longer used.",
            )


@check(
    id="COST004",
    title="No budget alert configured for the project",
    category=Category.COST,
    severity=Severity.MEDIUM,
    references=["https://cloud.google.com/billing/docs/how-to/budgets"],
)
def no_budget(snapshot: dict) -> Iterator[Detail]:
    # Only meaningful when billing info was collected into the snapshot.
    if "budgets" in snapshot and not snapshot.get("budgets"):
        yield Detail(
            resource=ResourceRef("billing.project", snapshot.get("project_id", "?")),
            message="No budget or budget alert is configured; runaway spend would go unnoticed.",
            recommendation="Create a budget with threshold alerts in Cloud Billing.",
        )
