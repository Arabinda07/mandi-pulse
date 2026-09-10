"""Command-line interface for the Food Inflation & Volatility Engine."""

from __future__ import annotations
import argparse
import sys
import io

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.warehouse import Warehouse
from src.registry import MandiRegistry
from src.ingest import IngestionEngine
from src.sources.seed import BootstrapSeedAdapter
from src.sources.datagov import DataGovInAdapter

console = Console()


def cmd_bootstrap(args: argparse.Namespace) -> None:
    """Initialize the warehouse and load historical seed data."""
    console.print(Panel.fit("[bold green]Bootstrapping Agricultural Volatility Engine[/bold green]\n"
                            "Target: [cyan]data/agri_engine.db[/cyan] (WAL Mode)"))
    wh = Warehouse()
    reg = MandiRegistry()
    source = BootstrapSeedAdapter(days_history=args.days)
    engine = IngestionEngine(wh, reg, source)

    with console.status("[bold yellow]Ingesting historical seed data and calculating corridor stress...[/bold yellow]"):
        summary = engine.bootstrap(days_history=args.days)

    console.print("[bold green][OK] Bootstrap completed successfully![/bold green]")
    table = Table(title="Bootstrap Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_row("Canonical Mandis Registered", str(summary["mandis_registered"]))
    table.add_row("Daily Market Facts Ingested", str(summary["facts_loaded"]))
    table.add_row("Corridor Stress Metrics Computed", str(summary["corridor_metrics_computed"]))
    console.print(table)


def cmd_alerts(args: argparse.Namespace) -> None:
    """Display active supply-chain stress alerts."""
    wh = Warehouse()
    alerts = wh.get_latest_alerts(limit=args.limit)

    if not alerts:
        console.print("[green]No high or severe supply-chain stress alerts active.[/green]")
        return

    table = Table(title=f"[ALERT] Active Supply-Chain Stress Alerts (Top {len(alerts)})")
    table.add_column("Date", style="dim")
    table.add_column("Commodity", style="cyan")
    table.add_column("Origin Mandi", style="yellow")
    table.add_column("Terminal Mandi", style="magenta")
    table.add_column("Spread (INR)", justify="right")
    table.add_column("Spread (%)", justify="right")
    table.add_column("Arrival Shock Z", justify="right")
    table.add_column("Stress Level", style="bold red")

    for a in alerts:
        table.add_row(
            a["reported_date"],
            a["commodity_name"],
            a["origin_mandi"],
            a["terminal_mandi"],
            f"Rs.{a['price_spread']:.2f}",
            f"{a['spread_pct']:.1f}%",
            f"{a['origin_arrival_shock_z']:.2f}",
            f"[{'red' if a['stress_level'] == 'SEVERE' else 'yellow'}]{a['stress_level']}[/]",
        )
    console.print(table)


def cmd_sync(args: argparse.Namespace) -> None:
    """Sync live daily data from data.gov.in."""
    console.print(Panel.fit("[bold blue]Syncing Live Data from data.gov.in[/bold blue]"))
    wh = Warehouse()
    reg = MandiRegistry()
    source = DataGovInAdapter(api_key=args.api_key)
    engine = IngestionEngine(wh, reg, source)

    commodities = [args.commodity] if args.commodity else ["onion", "tomato", "potato"]
    for comm in commodities:
        with console.status(f"[bold yellow]Fetching live records for {comm}...[/bold yellow]"):
            count = engine.ingest_commodity(comm)
            console.print(f"[OK] Ingested {count} live facts for [cyan]{comm}[/cyan]")

    engine.refresh_corridor_stress_metrics()
    console.print("[bold green][OK] Live sync and metric recalculation complete![/bold green]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Food Inflation & Supply-Chain Volatility Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # bootstrap
    p_boot = subparsers.add_parser("bootstrap", help="Initialize DB and load curated seed data")
    p_boot.add_argument("--days", type=int, default=180, help="Number of historical days to seed")
    p_boot.set_defaults(func=cmd_bootstrap)

    # alerts
    p_alerts = subparsers.add_parser("alerts", help="Show active supply-chain corridor stress alerts")
    p_alerts.add_argument("--limit", type=int, default=15, help="Number of alerts to show")
    p_alerts.set_defaults(func=cmd_alerts)

    # sync
    p_sync = subparsers.add_parser("sync", help="Sync latest data from data.gov.in")
    p_sync.add_argument("--commodity", type=str, help="Specific commodity to sync (onion/tomato/potato)")
    p_sync.add_argument("--api-key", type=str, help="data.gov.in API key (optional if env set)")
    p_sync.set_defaults(func=cmd_sync)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
