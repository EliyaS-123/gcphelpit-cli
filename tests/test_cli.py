import json

from typer.testing import CliRunner

from gcphelpit.cli import app
from gcphelpit.providers import bundled_fixture

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "gcphelpit" in result.stdout


def test_checks_lists_catalog():
    result = runner.invoke(app, ["checks"])
    assert result.exit_code == 0
    assert "SEC001" in result.stdout
    assert "checks" in result.stdout


def test_scan_default_fixture_exits_clean_without_fail_on():
    result = runner.invoke(app, ["scan"])
    # Findings exist, but without --fail-on the command still exits 0.
    assert result.exit_code == 0


def test_scan_fail_on_high_exits_nonzero_on_insecure():
    result = runner.invoke(app, ["scan", "--fail-on", "high"])
    assert result.exit_code == 1


def test_scan_clean_fixture_reports_no_issues():
    clean = str(bundled_fixture("clean_project.json"))
    result = runner.invoke(app, ["scan", "--fixture", clean, "--fail-on", "low"])
    assert result.exit_code == 0
    assert "No issues found" in result.stdout


def test_scan_json_output_is_valid():
    result = runner.invoke(app, ["scan", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["project_id"] == "acme-demo-dev"
    assert payload["findings"]
    assert "summary" in payload


def test_scan_category_filter():
    result = runner.invoke(app, ["scan", "--format", "json", "--category", "cost"])
    payload = json.loads(result.stdout)
    assert {f["category"] for f in payload["findings"]} == {"cost"}


def test_scan_missing_fixture_errors():
    result = runner.invoke(app, ["scan", "--fixture", "/nonexistent/snap.json"])
    assert result.exit_code == 2


def test_bad_category_errors():
    result = runner.invoke(app, ["scan", "--category", "banana"])
    assert result.exit_code == 2
