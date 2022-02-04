"""
Main file to run the streamlit app
"""
import streamlit as st
from levy.config import Config

from openstats.components import Builder


def stats(cfg: Config):
    """
    Build the app
    """
    builder = Builder(cfg)

    st.title(cfg.title)

    builder.sidebar()
    builder.stars_component()
    st.markdown("---")
    builder.good_first_issues_component()
    st.markdown("---")
    builder.contributors_component()
    st.markdown("---")
    builder.traffic_component()


def run():
    config = Config.read_file("openstats.yaml")
    stats(config)
