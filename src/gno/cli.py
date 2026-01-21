"""CLI commands for gno."""

from pathlib import Path

import click

from gno import __version__
from gno.merger import merge_gitignores
from gno.templates import TemplateManager


@click.group(
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(
    __version__,
    "-v",
    "--version",
    prog_name="gno",
)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """gno - Interactive CLI tool for building .gitignore files.

    Run without arguments to launch the interactive TUI.
    """
    if ctx.invoked_subcommand is None:
        # Launch interactive mode by default
        from gno.tui import run_tui

        ctx.exit(0 if run_tui() else 1)


@cli.command("update")
def update_cmd() -> None:
    """Update the template cache from GitHub."""
    manager = TemplateManager(progress_callback=lambda msg: click.echo(msg))
    click.echo("Fetching templates from GitHub...")

    if manager.fetch_templates():
        count = len(manager.get_all_templates())
        click.secho(f"Successfully cached {count} templates!", fg="green")
    else:
        click.secho("Failed to fetch templates from GitHub.", fg="red", err=True)
        raise SystemExit(1)


@cli.command("list")
@click.argument("query", required=False)
def list_cmd(query: str | None) -> None:
    """List available templates. Optionally filter by QUERY."""
    manager = TemplateManager()

    if not manager.ensure_templates():
        click.secho(
            "No templates available. Run 'gno update' first.", fg="red", err=True
        )
        raise SystemExit(1)

    if query:
        templates = manager.search_templates(query)
        if not templates:
            click.echo(f"No templates matching '{query}'")
            return
        click.echo(f"Templates matching '{query}':\n")
    else:
        templates = manager.get_all_templates()
        click.echo(f"Available templates ({len(templates)}):\n")

    for template in templates:
        name = click.style(template["name"], fg="cyan", bold=True)
        desc = click.style(template["description"], fg="white", dim=True)
        click.echo(f"  {name}")
        click.echo(f"    {desc}")


@cli.command("show")
@click.argument("template_name")
def show_cmd(template_name: str) -> None:
    """Show the content of a specific template."""
    manager = TemplateManager()

    if not manager.ensure_templates():
        click.secho(
            "No templates available. Run 'gno update' first.", fg="red", err=True
        )
        raise SystemExit(1)

    template = manager.get_template(template_name)

    if not template:
        click.secho(f"Template '{template_name}' not found.", fg="red", err=True)
        click.echo("\nDid you mean one of these?")
        for t in manager.search_templates(template_name)[:5]:
            click.echo(f"  - {t['name']}")
        raise SystemExit(1)

    # Header
    click.secho(f"\n{template['name']}", fg="cyan", bold=True)
    click.secho(template["description"], fg="white", dim=True)
    click.secho(f"Source: {template['url']}\n", fg="blue", dim=True)

    # Content
    click.secho("-" * 60, fg="white", dim=True)
    click.echo(template["content"])
    click.secho("-" * 60, fg="white", dim=True)


@cli.command("generate")
@click.argument("templates", nargs=-1, required=True)
@click.option(
    "--output",
    "-o",
    default=".gitignore",
    help="Output file path (default: .gitignore)",
)
@click.option(
    "--append",
    "-a",
    is_flag=True,
    help="Append to existing file instead of overwriting",
)
@click.option(
    "--preview",
    "-p",
    is_flag=True,
    help="Preview the output without saving",
)
def generate_cmd(
    templates: tuple[str, ...], output: str, append: bool, preview: bool
) -> None:
    """Generate a .gitignore file from one or more templates.

    Examples:

        gno generate python

        gno generate python node --preview

        gno generate rust go -o backend/.gitignore

        gno generate java --append
    """
    manager = TemplateManager()

    if not manager.ensure_templates():
        click.secho(
            "No templates available. Run 'gno update' first.", fg="red", err=True
        )
        raise SystemExit(1)

    # Collect template contents
    sections: list[str] = []
    found_templates: list[str] = []
    missing_templates: list[str] = []

    for name in templates:
        template = manager.get_template(name)
        if template:
            found_templates.append(template["name"])
            section = f"# {template['name']}\n"
            section += f"# {template['description']}\n"
            section += f"# Source: {template['url']}\n\n"
            section += template["content"].strip()
            sections.append(section)
        else:
            missing_templates.append(name)

    # Report missing templates
    if missing_templates:
        for name in missing_templates:
            click.secho(f"Warning: Template '{name}' not found.", fg="yellow", err=True)
            suggestions = manager.search_templates(name)[:3]
            if suggestions:
                names = ", ".join(t["name"] for t in suggestions)
                click.echo(f"  Did you mean: {names}")

    if not sections:
        click.secho("No valid templates found.", fg="red", err=True)
        raise SystemExit(1)

    # Build the content
    header = "# Generated by gno (https://github.com/OseSem/gno)\n"
    header += f"# Templates: {', '.join(found_templates)}\n\n"
    content = header + "\n\n".join(sections) + "\n"

    # Preview mode
    if preview:
        click.secho("Preview:", fg="cyan", bold=True)
        click.secho("-" * 60, fg="white", dim=True)
        click.echo(content)
        click.secho("-" * 60, fg="white", dim=True)
        return

    # Write to file
    output_path = Path(output)
    file_existed = output_path.exists()

    if append and file_existed:
        existing_content = output_path.read_text(encoding="utf-8")
        content = merge_gitignores(existing_content, content)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    action = "Appended to" if append and file_existed else "Created"
    click.secho(
        f"{action} {output} with templates: {', '.join(found_templates)}", fg="green"
    )


@cli.command("interactive")
@click.option(
    "--output",
    "-o",
    default=".gitignore",
    help="Output file path (default: .gitignore)",
)
def interactive_cmd(output: str) -> None:
    """Launch the interactive TUI for selecting templates."""
    from gno.tui import run_tui

    if not run_tui(output):
        raise SystemExit(1)
