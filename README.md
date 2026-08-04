# gcphelpit — free CLI to scan Google Cloud for security, IAM, cost & reliability

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Checks](https://img.shields.io/badge/checks-16-orange)
![Mock-first](https://img.shields.io/badge/mock--first-no%20cloud%20access-brightgreen)

**gcphelpit** is a free, open-source command-line tool that scans a snapshot of your
Google Cloud project and finds **security, IAM, cost, and reliability** issues — with a
**plain-English fix for each finding**.

It is **mock-first**: it reads a JSON snapshot of your resources, so it runs — and is
fully testable — with **zero live cloud access or credentials**. A live GCP adapter can
be layered on later behind the same interface.

**📦 Install from PyPI:** [`pip install gcphelpit`](https://pypi.org/project/gcphelpit/)
**🌐 Documentation & guides:** [https://eliyas-123.github.io/gcphelpit/](https://eliyas-123.github.io/gcphelpit/)
**📋 Check catalog:** [All 16 checks →](https://eliyas-123.github.io/gcphelpit/checks.html)

## Who is this for

- You want to **audit a Google Cloud project without giving a tool live access** — point it at an exported JSON snapshot instead.
- You want **security, IAM, cost, and reliability** covered in **one** pass, not four separate tools.
- You want each finding to come with a **recommended fix in plain English**, not just a rule ID.
- You want to **gate CI/CD** on GCP misconfigurations with a simple exit code.

## Install & run

```bash
pip install gcphelpit
gcphelpit scan
```

You'll get a colour-coded table of findings, each with the offending resource and a
recommended fix.

**From source** (for development):

```bash
git clone https://github.com/EliyaS-123/gcphelpit-cli && cd gcphelpit-cli
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
gcphelpit scan
```

## What it checks

`gcphelpit checks` lists all built-in checks. They span four categories, each finding
paired with a plain-English fix:

| Category      | Examples |
| ------------- | -------- |
| `security`    | public buckets, world-open firewall ports, public/no-SSL Cloud SQL |
| `iam`         | primitive owner/editor roles, external members, user-managed SA keys |
| `cost`        | unattached disks, idle static IPs, stopped VMs, no budget alert |
| `reliability` | no DB backups, single-zone prod DB, no deletion protection |

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

## CI/CD gating

Fail the build when a project snapshot has issues at or above a severity — for example
in GitHub Actions:

```yaml
# .github/workflows/gcp-audit.yml
name: GCP audit
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install gcphelpit
      - run: gcphelpit scan -f snapshot.json --fail-on high
```

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

## How it compares

gcphelpit's niche is being the scanner you can point at an **exported snapshot with no
credentials**, covering all four categories at once with plain-English fixes. For broad
multi-cloud security coverage, tools like Prowler are stronger. See the honest
[gcphelpit vs Prowler / ScoutSuite / gcp-auditor comparison](https://eliyas-123.github.io/gcphelpit/compare.html).

## Adding a check

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
