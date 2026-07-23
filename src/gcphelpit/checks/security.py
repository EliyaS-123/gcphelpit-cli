"""Security-posture checks (public exposure, encryption, logging)."""

from __future__ import annotations

from typing import Iterator

from ..catalog import check
from ..models import Category, Detail, ResourceRef, Severity

PUBLIC_PRINCIPALS = {"allUsers", "allAuthenticatedUsers"}
# Ports that should essentially never be open to the whole internet.
SENSITIVE_PORTS = {"22": "SSH", "3389": "RDP", "3306": "MySQL", "5432": "PostgreSQL", "27017": "MongoDB"}


@check(
    id="SEC001",
    title="Cloud Storage bucket is publicly accessible",
    category=Category.SECURITY,
    severity=Severity.HIGH,
    references=["https://cloud.google.com/storage/docs/access-control/making-data-public"],
)
def public_buckets(snapshot: dict) -> Iterator[Detail]:
    for bucket in snapshot.get("buckets", []):
        members = {
            m
            for binding in bucket.get("iam_bindings", [])
            for m in binding.get("members", [])
        }
        public = members & PUBLIC_PRINCIPALS
        if public:
            who = " and ".join(sorted(public))
            yield Detail(
                resource=ResourceRef("storage.bucket", bucket.get("name", "?")),
                message=f"Bucket grants access to {who}, exposing its objects to the public internet.",
                recommendation="Remove allUsers/allAuthenticatedUsers bindings and serve public content via signed URLs or a CDN.",
            )


@check(
    id="SEC002",
    title="Bucket has uniform bucket-level access disabled",
    category=Category.SECURITY,
    severity=Severity.MEDIUM,
    references=["https://cloud.google.com/storage/docs/uniform-bucket-level-access"],
)
def uniform_access_disabled(snapshot: dict) -> Iterator[Detail]:
    for bucket in snapshot.get("buckets", []):
        if not bucket.get("uniform_bucket_level_access", False):
            yield Detail(
                resource=ResourceRef("storage.bucket", bucket.get("name", "?")),
                message="Per-object ACLs are still enabled; access is harder to reason about and audit.",
                recommendation="Enable uniform bucket-level access so IAM is the single source of truth.",
            )


@check(
    id="SEC003",
    title="Firewall rule opens a sensitive port to the internet",
    category=Category.SECURITY,
    severity=Severity.HIGH,
    references=["https://cloud.google.com/vpc/docs/firewalls"],
)
def open_firewalls(snapshot: dict) -> Iterator[Detail]:
    for fw in snapshot.get("firewalls", []):
        if fw.get("direction", "INGRESS") != "INGRESS" or fw.get("disabled"):
            continue
        if "0.0.0.0/0" not in fw.get("source_ranges", []):
            continue
        for allowed in fw.get("allowed", []):
            ports = allowed.get("ports", [])
            # An empty port list on tcp/udp means "all ports".
            exposed = [p for p in ports if p in SENSITIVE_PORTS]
            if not ports and allowed.get("protocol") in {"tcp", "all"}:
                yield Detail(
                    resource=ResourceRef("compute.firewall", fw.get("name", "?")),
                    message="Rule allows ALL ports from 0.0.0.0/0 — the entire internet can reach these instances.",
                    recommendation="Restrict source ranges to known CIDRs and limit ports to what is required.",
                )
            for port in exposed:
                yield Detail(
                    resource=ResourceRef("compute.firewall", fw.get("name", "?")),
                    message=f"Rule exposes {SENSITIVE_PORTS[port]} (port {port}) to 0.0.0.0/0.",
                    recommendation=f"Do not expose {SENSITIVE_PORTS[port]} to the internet; use IAP or a bastion and scope source ranges.",
                )


@check(
    id="SEC004",
    title="Cloud SQL instance has a public IP",
    category=Category.SECURITY,
    severity=Severity.HIGH,
    references=["https://cloud.google.com/sql/docs/mysql/configure-private-ip"],
)
def sql_public_ip(snapshot: dict) -> Iterator[Detail]:
    for sql in snapshot.get("sql_instances", []):
        if sql.get("public_ip", False):
            yield Detail(
                resource=ResourceRef("sql.instance", sql.get("name", "?")),
                message="Instance is reachable over a public IP address.",
                recommendation="Use Private IP / Private Service Connect and disable the public IP.",
            )


@check(
    id="SEC005",
    title="Cloud SQL does not require SSL/TLS",
    category=Category.SECURITY,
    severity=Severity.MEDIUM,
    references=["https://cloud.google.com/sql/docs/mysql/configure-ssl-instance"],
)
def sql_no_ssl(snapshot: dict) -> Iterator[Detail]:
    for sql in snapshot.get("sql_instances", []):
        if not sql.get("require_ssl", False):
            yield Detail(
                resource=ResourceRef("sql.instance", sql.get("name", "?")),
                message="Connections are accepted without enforced SSL/TLS.",
                recommendation="Set the instance to require SSL for all connections.",
            )
