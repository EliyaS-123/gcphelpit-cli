# gcphelpit

A friendly CLI that scans a snapshot of your Google Cloud project and finds
**security, IAM, cost, and reliability** issues — with a plain-English fix for each.

It is **mock-first**: it reads a JSON snapshot of your resources, so it runs and
is fully testable with zero cloud access. A live GCP adapter can be layered on
later behind the same interface.

> 🌐 Part of **[GoogleHelpit](https://eliyas-123.github.io/gcphelpit/)** — a community hub of
> troubleshooting guides, tutorials, and tools for Google Cloud & Workspace.
> See the [gcphelpit tool page](https://eliyas-123.github.io/gcphelpit/tool.html).

## Quickstart

```bash
git clone https://github.com/EliyaS-123/gcphelpit-cli && cd gcphelpit-cli
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Scan the bundled demo snapshot
gcphelpit scan
```

Or install straight from GitHub, no clone needed:

```bash
pip install git+https://github.com/EliyaS-123/gcphelpit-cli.git
```

You'll get a colour-coded table of findings, each with the offending resource
and a recommended fix.

## Usage

```bash
gcphelpit scan                          # scan the bundled demo snapshot
gcphelpit scan -f my-project.json       # scan your own snapshot
gcphelpit scan --category security      # only security checks (repeatable)
gcphelpit scan --min-severity high      # only high/critical findings
gcphelpit scan --format json            # machine-readable output
gcphelpit scan --fail-on high           # exit non-zero for CI/CD gating
gcphelpit checks                        # list every check in the catalog
```

**Exit codes:** `0` clean, `1` findings at/above `--fail-on`, `2` usage/error.

## The snapshot

A snapshot is a plain JSON object describing what you collected from a project.
Every top-level key is optional — checks simply skip data that isn't there:

```json
{
  "project_id": "my-project",
  "buckets": [ { "name": "assets", "uniform_bucket_level_access": true, "iam_bindings": [] } ],
  "firewalls": [],
  "instances": [],
  "disks": [],
  "addresses": [],
  "service_accounts": [],
  "iam_policy": { "bindings": [] },
  "sql_instances": [],
  "budgets": []
}
```

See [`fixtures/insecure_project.json`](fixtures/insecure_project.json) for a fully
populated example (and [`clean_project.json`](fixtures/clean_project.json) for a
passing one).

## Check catalog

`gcphelpit checks` lists all built-in checks. They span four categories:

| Category      | Examples |
| ------------- | -------- |
| `security`    | public buckets, world-open firewall ports, public/no-SSL Cloud SQL |
| `iam`         | primitive owner/editor roles, external members, user-managed SA keys |
| `cost`        | unattached disks, idle static IPs, stopped VMs, no budget alert |
| `reliability` | no DB backups, single-zone prod DB, no deletion protection |

### Adding a check

Every check is one decorated function. Drop it in the right file under
[`src/gcphelpit/checks/`](src/gcphelpit/checks) and it auto-registers:

```python
from ..catalog import check
from ..models import Category, Detail, ResourceRef, Severity

@check(id="SEC099", title="…", category=Category.SECURITY,
       severity=Severity.HIGH, references=["https://cloud.google.com/…"])
def my_check(snapshot):
    for bucket in snapshot.get("buckets", []):
        if bad(bucket):
            yield Detail(
                resource=ResourceRef("storage.bucket", bucket["name"]),
                message="What's wrong.",
                recommendation="How to fix it.",
            )
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
