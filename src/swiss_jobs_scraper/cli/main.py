"""
Swiss Jobs Scraper CLI.

Command-line interface for searching and retrieving Swiss job listings.

Usage:
    swiss-jobs search "Software Engineer" --location Zurich
    swiss-jobs detail <job-id>
    swiss-jobs providers
    swiss-jobs health
    swiss-jobs serve --port 8000
"""

import asyncio
import csv
import json
import sys
from enum import Enum
from io import StringIO
from typing import Any, Literal, cast

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from swiss_jobs_scraper import __version__
from swiss_jobs_scraper.core.models import (
    ContractType,
    JobListing,
    JobSearchRequest,
    JobSearchResponse,
    SortOrder,
    WorkForm,
)
from swiss_jobs_scraper.core.session import ExecutionMode
from swiss_jobs_scraper.providers import get_provider, list_providers

console = Console()


class OutputFormat(str, Enum):
    """Output format options."""

    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    TABLE = "table"


# =============================================================================
# Helper Functions
# =============================================================================


def format_output(
    data: Any,
    format_type: OutputFormat,
    fields: list[str] | None = None,
) -> str:
    """
    Format data for output.

    Args:
        data: Data to format (dict, list, or Pydantic model)
        format_type: Output format
        fields: Fields to include (for CSV/table)

    Returns:
        Formatted string
    """
    # Convert Pydantic models to dict
    if hasattr(data, "model_dump"):
        data = data.model_dump(mode="json", exclude_none=True)

    if format_type == OutputFormat.JSON:
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)

    elif format_type == OutputFormat.JSONL:
        if isinstance(data, list):
            return "\n".join(
                json.dumps(item, ensure_ascii=False, default=str) for item in data
            )
        return json.dumps(data, ensure_ascii=False, default=str)

    elif format_type == OutputFormat.CSV:
        return _format_csv(data, fields)

    elif format_type == OutputFormat.TABLE:
        return _format_table(data, fields)

    return str(data)


def _format_csv(data: Any, fields: list[str] | None = None) -> str:
    """Format data as CSV."""
    if isinstance(data, dict) and "items" in data:
        items = data["items"]
    elif isinstance(data, list):
        items = data
    else:
        items = [data]

    if not items:
        return ""

    # Default fields for job listings
    if fields is None:
        fields = ["id", "title", "company_name", "location_city", "workload", "posted"]

    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(fields)

    # Rows
    for item in items:
        row = []
        for field in fields:
            value = _extract_field(item, field)
            row.append(value)
        writer.writerow(row)

    return output.getvalue()


def _format_table(data: Any, fields: list[str] | None = None) -> str:
    """Format data as rich table (returns empty string, prints directly)."""
    if isinstance(data, dict) and "items" in data:
        items = data["items"]
        total = data.get("total_count", len(items))
        page = data.get("page", 0)
        page_size = data.get("page_size", len(items))
    elif isinstance(data, list):
        items = data
        total = len(items)
        page = 0
        page_size = len(items)
    else:
        items = [data]
        total = 1
        page = 0
        page_size = 1

    if not items:
        console.print("[yellow]No results found.[/yellow]")
        return ""

    # Create table
    table = Table(
        title=f"Job Search Results ({len(items)} of {total})",
        show_header=True,
        header_style="bold cyan",
    )

    # Add columns
    table.add_column("Title", style="bold white", max_width=40)
    table.add_column("Company", style="green", max_width=25)
    table.add_column("Location", style="blue")
    table.add_column("Workload", justify="right")
    table.add_column("Posted", style="dim")
    table.add_column("ID", style="dim", max_width=15)

    # Add rows
    for item in items:
        title = _extract_field(item, "title")
        company = _extract_field(item, "company_name")
        location = _extract_field(item, "location_city")
        workload_min = _extract_field(item, "workload_min")
        workload_max = _extract_field(item, "workload_max")
        workload = (
            f"{workload_min}-{workload_max}%"
            if workload_min != workload_max
            else f"{workload_min}%"
        )
        posted = _extract_field(item, "created_at")
        if posted:
            posted = posted[:10]  # Just the date part
        job_id = _extract_field(item, "id")
        if job_id and len(job_id) > 15:
            job_id = job_id[:12] + "..."

        table.add_row(
            title or "-",
            company or "-",
            location or "-",
            workload,
            posted or "-",
            job_id or "-",
        )

    console.print(table)

    # Pagination info
    if total > page_size:
        console.print(
            f"\n[dim]Page {page + 1} of {(total + page_size - 1) // page_size}. "
            f"Use --page N to see more results.[/dim]"
        )

    return ""


def _extract_field(item: dict[str, Any], field: str) -> str:
    """Extract a field value from a nested dict."""
    if not isinstance(item, dict):
        return str(item)

    # Handle common field mappings
    if field == "company_name":
        company = item.get("company", {})
        return company.get("name", "") if isinstance(company, dict) else ""

    elif field == "location_city":
        location = item.get("location", {})
        return location.get("city", "") if isinstance(location, dict) else ""

    elif field == "workload_min":
        emp = item.get("employment", {})
        return str(emp.get("workload_min", 100)) if isinstance(emp, dict) else "100"

    elif field == "workload_max":
        emp = item.get("employment", {})
        return str(emp.get("workload_max", 100)) if isinstance(emp, dict) else "100"

    elif field == "posted":
        return item.get("created_at", "")[:10] if item.get("created_at") else ""

    elif field == "created_at":
        return str(item.get("created_at", ""))

    # Direct field access
    value = item.get(field, "")
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value) if value is not None else ""
    # Add an explicit return match for static analysis if needed, though the above covers it
    return ""


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
@click.version_option(__version__, prog_name="swiss-jobs")
def cli() -> None:
    """
    Swiss Jobs Scraper - Search Swiss job listings from multiple sources.

    \b
    Examples:
        swiss-jobs search "Software Engineer" --location Zurich
        swiss-jobs search "Data Scientist" --canton ZH --workload-min 80
        swiss-jobs detail abc123-uuid --provider job_room
        swiss-jobs providers
        swiss-jobs serve --port 8000
    """

    pass


@cli.command()
@click.argument("query", required=False)
@click.option("-l", "--location", help="City name or postal code")
@click.option(
    "-c", "--canton", "cantons", multiple=True, help="Canton code (e.g., ZH, BE)"
)
@click.option("-k", "--keyword", "keywords", multiple=True, help="Additional keywords")
@click.option(
    "--workload-min", type=int, default=0, help="Minimum workload percentage (0-100)"
)
@click.option(
    "--workload-max", type=int, default=100, help="Maximum workload percentage (0-100)"
)
@click.option(
    "--contract",
    type=click.Choice(["permanent", "temporary", "any"]),
    default="any",
    help="Contract type filter",
)
@click.option(
    "--work-form",
    "work_forms",
    multiple=True,
    type=click.Choice(["HOME_WORK", "SHIFT_WORK", "NIGHT_WORK", "SUNDAY_AND_HOLIDAYS"]),
    help="Work arrangement filter",
)
@click.option("--company", help="Filter by company name")
@click.option("--days", type=int, default=30, help="Jobs posted within N days")
@click.option(
    "--profession-code", "profession_codes", multiple=True, help="AVAM profession codes"
)
@click.option("--page", type=int, default=0, help="Page number (0-indexed)")
@click.option("--page-size", type=int, default=20, help="Results per page")
@click.option(
    "--sort",
    type=click.Choice(["date_desc", "date_asc", "relevance"]),
    default="date_desc",
    help="Sort order",
)
@click.option(
    "--lang",
    type=click.Choice(["en", "de", "fr", "it"]),
    default="en",
    help="Response language",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["json", "jsonl", "csv", "table"]),
    default="table",
    help="Output format",
)
@click.option(
    "--mode",
    type=click.Choice(["fast", "stealth", "aggressive"]),
    default="stealth",
    help="Execution mode (affects speed/stealth tradeoff)",
)
@click.option("-p", "--provider", default="job_room", help="Job provider to use")
@click.option("--raw", is_flag=True, help="Include raw API response data")
def search(
    query: str | None,
    location: str | None,
    cantons: tuple[str, ...],
    keywords: tuple[str, ...],
    workload_min: int,
    workload_max: int,
    contract: str,
    work_forms: tuple[str, ...],
    company: str | None,
    days: int,
    profession_codes: tuple[str, ...],
    page: int,
    page_size: int,
    sort: str,
    lang: str,
    output_format: str,
    mode: str,
    provider: str,
    raw: bool,
) -> None:
    """
    Search for jobs matching the given criteria.

    \b
    Examples:
        swiss-jobs search "Python Developer"
        swiss-jobs search --location Zurich --workload-min 80
        swiss-jobs search "Engineer" -c ZH -c BE --contract permanent
        swiss-jobs search --work-form HOME_WORK --days 7
    """
    # Build request
    request = JobSearchRequest(
        query=query,
        keywords=list(keywords),
        location=location,
        canton_codes=list(cantons),
        workload_min=workload_min,
        workload_max=workload_max,
        contract_type=ContractType(contract),
        work_forms=[WorkForm(wf) for wf in work_forms],
        company_name=company,
        posted_within_days=days,
        profession_codes=list(profession_codes),
        page=page,
        page_size=page_size,
        sort=SortOrder(sort),
        language=cast(Literal["en", "de", "fr", "it"], lang),
    )

    # Get execution mode
    exec_mode = ExecutionMode(mode)

    async def _search() -> JobSearchResponse:
        provider_cls = get_provider(provider)
        async with provider_cls(mode=exec_mode, include_raw_data=raw) as p:
            return await p.search(request)

    # Execute search with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description="Searching...", total=None)
        try:
            result = asyncio.run(_search())
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)


    # Format and output result
    fmt = OutputFormat(output_format)
    if fmt == OutputFormat.TABLE:
        format_output(result, fmt)
    else:
        output = format_output(result, fmt)
        click.echo(output)


@cli.command()
@click.argument("job_id")
@click.option("-p", "--provider", default="job_room", help="Job provider")
@click.option("--lang", type=click.Choice(["en", "de", "fr", "it"]), default="en")
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["json", "table"]),
    default="json",
    help="Output format",
)
@click.option(
    "--mode",
    type=click.Choice(["fast", "stealth", "aggressive"]),
    default="stealth",
)
def detail(
    job_id: str, provider: str, lang: str, output_format: str, mode: str
) -> None:
    """
    Get full details for a specific job.

    \b
    Example:
        swiss-jobs detail abc123-def456-uuid
    """
    exec_mode = ExecutionMode(mode)

    async def _get_detail() -> JobListing:
        provider_cls = get_provider(provider)
        async with provider_cls(mode=exec_mode, include_raw_data=True) as p:
            return await p.get_details(
                job_id, language=cast(Literal["en", "de", "fr", "it"], lang)
            )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description="Fetching details...", total=None)
        try:
            result = asyncio.run(_get_detail())
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    # Output
    if output_format == "table":
        _print_job_detail(result)
    else:
        data = result.model_dump(mode="json", exclude_none=True)
        click.echo(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def _print_job_detail(job: Any) -> None:
    """Print job details in a nice format."""
    console.print(
        Panel(
            f"[bold cyan]{job.title}[/bold cyan]\n"
            f"[green]{job.company.name}[/green] • [blue]{job.location.city}[/blue]",
            title="Job Details",
        )
    )

    # Description
    if job.descriptions:
        desc = job.descriptions[0].description
        if len(desc) > 500:
            desc = desc[:500] + "..."
        console.print(f"\n[bold]Description:[/bold]\n{desc}\n")

    # Employment details
    emp = job.employment
    console.print("[bold]Employment:[/bold]")
    console.print(f"  • Workload: {emp.workload_min}-{emp.workload_max}%")
    console.print(f"  • Permanent: {'Yes' if emp.is_permanent else 'No'}")
    if emp.start_date:
        console.print(f"  • Start: {emp.start_date}")

    # Application
    if job.application:
        console.print("\n[bold]How to Apply:[/bold]")
        if job.application.email:
            console.print(f"  • Email: {job.application.email}")
        if job.application.form_url:
            console.print(f"  • URL: {job.application.form_url}")

    # ID for reference
    console.print(f"\n[dim]ID: {job.id}[/dim]")


@cli.command("providers")
def list_providers_cmd() -> None:
    """List all available job providers."""
    providers = list_providers()

    table = Table(
        title="Available Providers", show_header=True, header_style="bold cyan"
    )
    table.add_column("Name", style="bold white")
    table.add_column("Display Name")
    table.add_column("Status")

    for name in providers:
        provider_cls = get_provider(name)
        # Create a temp instance to get display name
        display = provider_cls().display_name
        table.add_row(name, display, "[green]Available[/green]")

    console.print(table)


@cli.command()
@click.option("-p", "--provider", default=None, help="Specific provider to check")
def health(provider: str | None) -> None:
    """Check health status of job providers."""
    providers_to_check = [provider] if provider else list_providers()

    async def _check_health() -> (
        list[Any]
    ):  # using Any because ProviderHealth might not be imported or circular
        results = []
        for name in providers_to_check:
            provider_cls = get_provider(name)
            async with provider_cls() as p:
                health = await p.health_check()
                results.append(health)
        return results

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description="Checking health...", total=None)
        results = asyncio.run(_check_health())

    # Display results
    table = Table(title="Provider Health", show_header=True, header_style="bold cyan")
    table.add_column("Provider")
    table.add_column("Status")
    table.add_column("Latency")
    table.add_column("Message")

    status_colors = {
        "healthy": "green",
        "degraded": "yellow",
        "unavailable": "red",
    }

    for h in results:
        color = status_colors.get(h.status.value, "white")
        latency = f"{h.latency_ms}ms" if h.latency_ms else "-"
        table.add_row(
            h.provider,
            f"[{color}]{h.status.value.upper()}[/{color}]",
            latency,
            h.message or "-",
        )

    console.print(table)


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the REST API server."""
    try:
        import uvicorn
    except ImportError:
        console.print(
            "[red]Error:[/red] uvicorn not installed. Run: pip install uvicorn"
        )
        sys.exit(1)

    console.print(f"[green]Starting API server at http://{host}:{port}[/green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    uvicorn.run(
        "swiss_jobs_scraper.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )



if __name__ == "__main__":
    cli()
