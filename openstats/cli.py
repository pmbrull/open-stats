"""
Helper CLI
"""
import typer
from levy.config import Config

from openstats.theme import write_theme

app = typer.Typer()


YAML_FILE = "openstats.yaml"


@app.command()
def write():
    """
    Write the streamlit theme
    """
    typer.echo("Writing theme file under ./streamlit")

    config = Config.read_file(YAML_FILE)
    write_theme(config)


if __name__ == "__main__":
    app()
