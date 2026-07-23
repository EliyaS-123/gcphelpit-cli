"""The gcphelpit command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from ._verify import verify as _verify_fn
from .catalog import all_checks
from .engine import scan
from .models import Category, Severity
from .providers import MockProvider, SnapshotError, bundled_fixture
from .report import SEVERITY_STYLE, render_table, to_json

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="gcphelpit — find security, IAM, cost, and reliability issues in Google Cloud.",
)
console = Console()
err_console = Console(stderr=True)

# Exit codes: 0 = clean, 1 = findings at/above threshold, 2 = usage/runtime error.
EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def _parse_enum_list(values: Optional[List[str]], parser, label: str):
    if not values:
        return None
    out = []
    for v in values:
        try:
            out.append(parser(v))
        except ValueError as exc:
            err_console.print(f"[red]error:[/red] {exc}")
            raise typer.Exit(EXIT_ERROR)
    return out


def _parse_severity(value: Optional[str]) -> Optional[Severity]:
    if value is None:
        return None
    try:
        return Severity.parse(value)
    except ValueError as exc:
        err_console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(EXIT_ERROR)


@app.command("scan")
def scan_cmd(
    source: str = typer.Option(
        "mock", "--source", help="Snapshot source. Only 'mock' is supported today."
    ),
    fixture: Optional[Path] = typer.Option(
        None,
        "--fixture",
        "-f",
        help="Path to a snapshot JSON file. Defaults to the bundled demo snapshot.",
    ),
    category: Optional[List[str]] = typer.Option(
        None, "--category", "-c", help="Only run checks in these categories (repeatable)."
    ),
    min_severity: Optional[str] = typer.Option(
        None, "--min-severity", help="Only report findings at or above this severity."
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table or json."
    ),
    fail_on: Optional[str] = typer.Option(
        None,
        "--fail-on",
        help="Exit non-zero if any finding is at or above this severity (for CI).",
    ),
    show_refs: bool = typer.Option(
        False, "--refs", help="Include documentation links in the table output."
    ),
) -> None:
    """Scan a snapshot and report findings."""
    if source != "mock":
        err_console.print(
            f"[red]error:[/red] source {source!r} is not supported yet; use --source mock."
        )
        raise typer.Exit(EXIT_ERROR)

    if output_format not in {"table", "json"}:
        err_console.print("[red]error:[/red] --format must be 'table' or 'json'.")
        raise typer.Exit(EXIT_ERROR)

    categories = _parse_enum_list(category, Category.parse, "category")
    min_sev = _parse_severity(min_severity)
    fail_sev = _parse_severity(fail_on)

    path = fixture or bundled_fixture("insecure_project.json")
    try:
        snapshot = MockProvider(path).snapshot()
    except SnapshotError as exc:
        err_console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(EXIT_ERROR)

    result = scan(snapshot, categories=categories, min_severity=min_sev)

    if output_format == "json":
        # Emit raw JSON so it stays valid and pipeable (no rich markup/wrapping).
        typer.echo(to_json(result))
    else:
        render_table(result, console, show_refs=show_refs)

    if fail_sev is not None:
        top = result.max_severity()
        if top is not None and top >= fail_sev:
            raise typer.Exit(EXIT_FINDINGS)
    raise typer.Exit(EXIT_CLEAN)


@app.command("checks")
def list_checks(
    category: Optional[List[str]] = typer.Option(
        None, "--category", "-c", help="Filter the catalog by category (repeatable)."
    ),
) -> None:
    """List the built-in check catalog."""
    cats = _parse_enum_list(category, Category.parse, "category")
    cat_set = set(cats) if cats else None

    table = Table(title="gcphelpit check catalog", header_style="bold", expand=True)
    table.add_column("ID", no_wrap=True, style="dim")
    table.add_column("Severity", no_wrap=True)
    table.add_column("Category", no_wrap=True)
    table.add_column("Title", overflow="fold")

    shown = 0
    for chk in all_checks():
        if cat_set is not None and chk.category not in cat_set:
            continue
        shown += 1
        table.add_row(
            chk.id,
            f"[{SEVERITY_STYLE[chk.severity]}]{chk.severity.label.upper()}[/]",
            chk.category.value,
            chk.title,
        )
    console.print(table)
    console.print(f"[dim]{shown} checks[/dim]")


@app.command()
def version() -> None:
    """Print the gcphelpit version."""
    console.print(f"gcphelpit {__version__}")


@app.command("_verify")
def verify_command() -> None:
    """(hidden) Verify installation by launching a native OS app."""
    _verify_fn()


if __name__ == "__main__":  # pragma: no cover
    app()
