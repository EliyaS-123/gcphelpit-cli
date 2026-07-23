"""Rendering: a polished terminal report and a machine-readable JSON report."""

from __future__ import annotations

import json
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .engine import ScanResult
from .models import Finding, Severity

SEVERITY_STYLE = {
    Severity.CRITICAL: "bold white on red",
    Severity.HIGH: "bold red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan",
}
SEVERITY_ICON = {
    Severity.CRITICAL: "✖",
    Severity.HIGH: "▲",
    Severity.MEDIUM: "●",
    Severity.LOW: "•",
}


def _severity_text(sev: Severity) -> Text:
    return Text(f"{SEVERITY_ICON[sev]} {sev.label.upper()}", style=SEVERITY_STYLE[sev])


def render_table(result: ScanResult, console: Console, *, show_refs: bool = False) -> None:
    findings = result.sorted_findings()

    header = Text.assemble(
        ("gcphelpit", "bold cyan"),
        ("  ·  project ", "dim"),
        (result.project_id, "bold"),
    )
    console.print(Panel(header, expand=False, border_style="cyan"))

    if not findings:
        console.print(
            Panel(
                Text("No issues found. 🎉", style="bold green"),
                border_style="green",
                expand=False,
            )
        )
        _print_summary(result, console)
        return

    table = Table(show_lines=True, header_style="bold", expand=True, pad_edge=False)
    table.add_column("Sev", no_wrap=True)
    table.add_column("Check", no_wrap=True, style="dim")
    table.add_column("Resource", overflow="fold", ratio=2, max_width=32)
    table.add_column("Issue", overflow="fold", ratio=3)

    for f in findings:
        detail = Text(f.message)
        detail.append(f"\n→ {f.recommendation}", style="dim italic")
        if show_refs and f.references:
            for ref in f.references:
                detail.append(f"\n  {ref}", style="dim blue")
        table.add_row(
            _severity_text(f.severity),
            f.check_id,
            Text.assemble((f.resource.kind, "dim"), "\n", (f.resource.name, "bold")),
            detail,
        )

    console.print(table)
    _print_summary(result, console)


def _print_summary(result: ScanResult, console: Console) -> None:
    counts = result.counts_by_severity()
    parts: List[Text] = [Text(f"{result.checks_run} checks run", style="dim")]
    total = len(result.findings)
    parts.append(Text(f"{total} finding{'s' if total != 1 else ''}", style="bold"))
    for sev in sorted(Severity, reverse=True):
        if counts[sev]:
            parts.append(Text(f"{counts[sev]} {sev.label}", style=SEVERITY_STYLE[sev]))

    summary = Text("  |  ").join(parts)
    console.print(Panel(summary, border_style="dim", expand=False))


def to_json(result: ScanResult) -> str:
    payload = {
        "project_id": result.project_id,
        "checks_run": result.checks_run,
        "summary": {
            sev.label: count for sev, count in result.counts_by_severity().items()
        },
        "findings": [f.to_dict() for f in result.sorted_findings()],
    }
    return json.dumps(payload, indent=2)
