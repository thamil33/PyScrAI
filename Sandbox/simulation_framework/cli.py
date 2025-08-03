"""
Basic CLI interface placeholder for the simulation framework.
"""

import click
from .core.config import get_config
from .utils.logging_config import setup_logging


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config', type=click.Path(), help='Configuration file path')
def main(debug, config):
    """LangGraph Multi-Agent Simulation Framework CLI."""
    # Setup logging
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(level=log_level)
    
    # Load configuration
    if config:
        click.echo(f"Loading config from: {config}")
    
    click.echo("LangGraph Multi-Agent Simulation Framework")


@main.command()
def version():
    """Show framework version."""
    from . import __version__
    click.echo(f"Version: {__version__}")


@main.command()
@click.option('--simulation-id', help='Simulation ID to check')
def status(simulation_id):
    """Show framework and simulation status."""
    click.echo("Framework Status: Active")
    if simulation_id:
        click.echo(f"Simulation {simulation_id}: Not implemented yet")


if __name__ == '__main__':
    main()
