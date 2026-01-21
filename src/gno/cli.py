"""CLI commands for gno."""

import click

from gno import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="gno")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """gno - Interactive CLI tool for building .gitignore files."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
