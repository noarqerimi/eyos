import logging
import sys
from pathlib import Path

import typer
import uvicorn

from eyos.config import get_settings
from eyos.utils.helpers import configure_logging

cli_app = typer.Typer(help="NewStore to Hail API Integration CLI")


@cli_app.command()
def run(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info",
) -> None:
    """Run the API server."""
    configure_logging(log_level)

    # Add src to the Python path if not already there
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Get settings
    settings = get_settings()

    # Log startup information
    logging.info(f"Starting {settings.api_title} v{settings.api_version}")
    logging.info(f"Listening on http://{host}:{port}")

    if reload:
        logging.info("Hot reload enabled")

    # Run the server
    uvicorn.run(
        "eyos.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
    )


@cli_app.command()
def simulate(event_file: str = "newstore_sample_payload.json") -> None:
    """Simulate a NewStore webhook event."""
    import json
    from pathlib import Path

    import httpx

    # Load the event from file
    try:
        event_path = Path(event_file)
        if not event_path.exists():
            # Try to find it in the project root
            event_path = Path(__file__).parent.parent.parent.parent / event_file

        if not event_path.exists():
            typer.echo(f"Error: Event file not found: {event_file}")
            raise typer.Exit(1)

        with open(event_path, "r") as f:
            event_data = json.load(f)

        # Send the event to the API
        url = "http://localhost:8000/webhooks/newstore/simulate"
        typer.echo(f"Sending event to {url}")

        response = httpx.post(url, json=event_data)

        if response.status_code == 202:
            typer.echo("Event accepted for processing")
            typer.echo(json.dumps(response.json(), indent=2))
        else:
            typer.echo(f"Error: {response.status_code} - {response.text}")
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"Error: {e!s}")
        raise typer.Exit(1) from e


@cli_app.command()
def scripts() -> None:
    """List available Rye scripts."""
    typer.echo("Available Rye scripts:")
    typer.echo("")

    try:
        # Try to extract scripts from pyproject.toml
        import tomli

        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomli.load(f)

            scripts = data.get("tool", {}).get("rye", {}).get("scripts", {})

            if scripts:
                max_name_len = max(len(name) for name in scripts.keys())

                for name, command in scripts.items():
                    if isinstance(command, dict) and "chain" in command:
                        cmd_str = " && ".join(command["chain"])
                    else:
                        cmd_str = str(command)

                    typer.echo(f"  rye run {name:{max_name_len}}  -  {cmd_str}")
            else:
                typer.echo("  No scripts found in pyproject.toml")
        else:
            typer.echo("  pyproject.toml not found")

    except ImportError:
        # If tomli is not available, show a simplified list
        typer.echo("  dev                -  Start the development server with hot reload")
        typer.echo("  start              -  Start the server in production mode")
        typer.echo("  test               -  Run all tests")
        typer.echo("  test-cov           -  Run tests with coverage report")
        typer.echo("  simulate           -  Simulate a webhook event using the default payload")
        typer.echo("  simulate-newstore  -  Simulate a NewStore webhook event")
        typer.echo("  format             -  Format code with Black and isort")
        typer.echo("  lint               -  Run static type checking with mypy")

    typer.echo("")
    typer.echo("Run scripts with: rye run <script-name>")


if __name__ == "__main__":
    cli_app()
