"""IAM / least-privilege checks."""

from __future__ import annotations

from typing import Iterator

from ..catalog import check
from ..models import Category, Detail, ResourceRef, Severity

PRIMITIVE_ROLES = {"roles/owner", "roles/editor"}
# Domains that indicate an account outside the organization.
EXTERNAL_DOMAINS = {"gmail.com", "googlemail.com", "hotmail.com", "outlook.com", "yahoo.com"}


def _iter_bindings(snapshot: dict):
    for binding in snapshot.get("iam_policy", {}).get("bindings", []):
        role = binding.get("role", "")
        for member in binding.get("members", []):
            yield role, member


@check(
    id="IAM001",
    title="Primitive role (owner/editor) granted to a user",
    category=Category.IAM,
    severity=Severity.HIGH,
    references=["https://cloud.google.com/iam/docs/using-iam-securely#least_privilege"],
)
def primitive_roles(snapshot: dict) -> Iterator[Detail]:
    for role, member in _iter_bindings(snapshot):
        if role in PRIMITIVE_ROLES and member.startswith("user:"):
            yield Detail(
                resource=ResourceRef("iam.binding", member),
                message=f"{member} holds {role}, a broad primitive role.",
                recommendation="Replace primitive roles with predefined or custom roles scoped to what the user needs.",
            )


@check(
    id="IAM002",
    title="Service account granted owner/editor at the project level",
    category=Category.IAM,
    severity=Severity.HIGH,
    references=["https://cloud.google.com/iam/docs/best-practices-service-accounts"],
)
def service_account_primitive(snapshot: dict) -> Iterator[Detail]:
    for role, member in _iter_bindings(snapshot):
        if role in PRIMITIVE_ROLES and member.startswith("serviceAccount:"):
            yield Detail(
                resource=ResourceRef("iam.binding", member),
                message=f"Service account {member} holds {role}; a compromised key would own the project.",
                recommendation="Grant the service account only the specific roles its workload requires.",
            )


@check(
    id="IAM003",
    title="External (non-organization) member has access",
    category=Category.IAM,
    severity=Severity.MEDIUM,
    references=["https://cloud.google.com/resource-manager/docs/organization-policy/restricting-domains"],
)
def external_members(snapshot: dict) -> Iterator[Detail]:
    for role, member in _iter_bindings(snapshot):
        if ":" not in member:
            continue
        _, identity = member.split(":", 1)
        domain = identity.split("@")[-1].lower() if "@" in identity else ""
        if domain in EXTERNAL_DOMAINS:
            yield Detail(
                resource=ResourceRef("iam.binding", member),
                message=f"{member} is an external account with {role}.",
                recommendation="Use organization-managed identities and a domain-restriction org policy.",
            )


@check(
    id="IAM004",
    title="Service account has user-managed keys",
    category=Category.IAM,
    severity=Severity.MEDIUM,
    references=["https://cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys"],
)
def user_managed_keys(snapshot: dict) -> Iterator[Detail]:
    for sa in snapshot.get("service_accounts", []):
        keys = [k for k in sa.get("keys", []) if k.get("type") == "USER_MANAGED"]
        if keys:
            yield Detail(
                resource=ResourceRef("iam.serviceAccount", sa.get("email", "?")),
                message=f"{len(keys)} user-managed key(s) exist; long-lived keys are a common exfiltration target.",
                recommendation="Prefer workload identity / short-lived credentials and delete unused user-managed keys.",
            )
