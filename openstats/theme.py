"""
Generate streamlit theme data
"""
from pathlib import Path
from textwrap import dedent

from levy.config import Config


def write_theme(config: Config) -> None:
    """
    Write the .streamlit/config.toml file
    """
    path = ".streamlit"

    theme = dedent(
        f"""
        [theme]
        primaryColor="{config.style.primary_color}"
        backgroundColor="{config.style.background_color}"
        secondaryBackgroundColor="{config.style.secondary_background_color}"
        textColor="{config.style.text_color}"
        font="{config.style.font}"
        """
    )

    # Create path if not exists
    if not Path(path).is_dir():
        Path(path).mkdir(exist_ok=True)

    # Save file
    with open(Path(path) / "config.toml", "w") as file:
        file.write(theme)
