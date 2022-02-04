"""
Main file to run the streamlit app
"""
import streamlit as st
from levy.config import Config

from openstats.components import Builder
from openstats.theme import write_theme


def stats(cfg: Config):
    """
    Build the app
    """
    builder = Builder(cfg)

    st.title(config.title)

    builder.sidebar()
    builder.stars_component()
    st.markdown("---")
    builder.good_first_issues_component()
    st.markdown("---")
    builder.contributors_component()
    st.markdown("---")
    builder.traffic_component()


if __name__ == "__main__":

    config = Config.read_file("openstats.yaml")
    write_theme(config)
    stats(config)