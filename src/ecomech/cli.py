"""EcoMech command-line interface."""

from pathlib import Path

import typer

app = typer.Typer(help="EcoMech: Ecological Process Mechanisms Knowledge Base")


@app.command()
def validate(
    file: Path = typer.Argument(..., help="Path to process YAML file"),
    schema: Path = typer.Option(
        Path("src/ecomech/schema/ecomech.yaml"),
        help="Path to LinkML schema",
    ),
) -> None:
    """Validate a process YAML file against the EcoMech schema."""
    import subprocess

    result = subprocess.run(
        ["linkml-validate", "-s", str(schema), "-C", "EcologicalProcess", str(file)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        typer.echo(f"OK: {file}")
    else:
        typer.echo(result.stderr, err=True)
        raise typer.Exit(1)


@app.command()
def list_processes(
    kb_dir: Path = typer.Option(Path("kb/processes"), help="Path to processes directory"),
) -> None:
    """List all curated ecological process entries."""
    files = sorted(kb_dir.glob("*.yaml"))
    if not files:
        typer.echo("No process entries found.")
        return
    for f in files:
        typer.echo(f.stem.replace("_", " "))
    typer.echo(f"\n{len(files)} process(es) total")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
