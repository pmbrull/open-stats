"""
Module creating the different streamlit
components to show on the app
"""

import altair as alt
import streamlit as st
from levy.config import Config

from openstats.client import Client
from openstats.data import Data


class Builder:
    """
    Component builder
    """

    def __init__(self, config: Config):
        self.config = config

        self.client = Client(self.config)
        self.data = Data(self.client)

    def stars_component(self):
        """
        Prepare the graph to show the stars evolution
        and the differences
        """
        df = self.data.stars_data().reset_index(level=0)

        if df is not None and not df.empty:
            current = int(df.iloc[-1].get("stars"))
            last_week = int(df.iloc[-2].get("stars"))
            last_month = int(df.iloc[-4].get("stars"))

        else:
            st.write("Error fetching Star data")
            return

        with st.container():

            st.subheader("Stars evolution")

            line_chart = (
                alt.Chart(df)
                .mark_line()
                .encode(
                    x=alt.X("date:T", axis=alt.Axis(tickCount=12, grid=False)),
                    y="stars:Q",
                    color=alt.value(self.config.style.primary_color),
                )
                .properties(
                    width=650,
                    height=350,
                )
            )

            st.altair_chart(line_chart)

            star_current, star_weekly, star_monthly = st.columns(3)
            star_current.metric("Current stars", current)
            star_weekly.metric("Last week inc.", last_week, current - last_week)
            star_monthly.metric("Last month inc.", last_month, current - last_month)

    def good_first_issues_component(self):
        """
        Present the good first issues
        """
        open_gfi, closed_gfi = self.data.good_first_issues_data()

        with st.container():

            st.subheader("Good first issues")

            open_issues, closed_issues = st.columns(2)
            open_issues.metric("Open good first issues", len(open_gfi))
            closed_issues.metric("Closed good first issues", len(closed_gfi))

    @staticmethod
    def clear_cache_button():
        """
        Prepare a button to clear the cached API values
        """

        with st.container():

            st.write("Clear the cache to refresh the data. It may take a few seconds.")

            if st.button("Clear cache"):
                st.experimental_memo.clear()

    def contributors_component(self):
        """
        Draw contributors data
        """

        contributors = self.data.contributors_data()

        recurrent_contributors = contributors.loc[contributors["contributions"] >= 3]

        with st.container():
            st.subheader("Contributors")

            bars = (
                alt.Chart(
                    contributors[:10],
                    title="Top 10 contributors",
                )
                .mark_bar()
                .encode(
                    x=alt.X(
                        "login",
                        axis=None,
                        sort=alt.EncodingSortField(
                            field="contributions", op="count", order="descending"
                        ),
                    ),
                    y=alt.Y("contributions"),
                    color=alt.value(self.config.style.primary_color),
                )
            )

            text = bars.mark_text(
                align="center",
                baseline="middle",
                fontSize=13,
                dy=-8,  # Nudges text to top so it doesn't appear on top of the bar
            ).encode(
                text="contributions:Q",
            )

            chart = (bars + text).properties(
                width=650,
                height=350,
            )

            st.altair_chart(chart)

            total, recurrent = st.columns(2)
            total.metric("Total contributors", contributors.shape[0])
            recurrent.metric("Recurrent contributors", recurrent_contributors.shape[0])

    def traffic_component(self):
        """
        Show clones and project views for the last 14 days
        """

        clones, views = self.data.traffic_data()

        with st.container():
            st.subheader("Traffic for the last 14 days")

            clones_col, views_col = st.columns(2)
            clones_col.metric("# Unique Clones", clones)
            views_col.metric("# Unique Views", views)

    def profile_component(self):
        percentage, desc = self.data.health_data()

        st.write(desc)
        st.markdown(self.config("social", ""))
        st.markdown("---")
        st.metric("Repository Health %", f"{percentage}%")

    def sidebar(self):

        with st.sidebar.container():
            st.image("./assets/openmetadata.png")
            st.write("\n\n")

            self.profile_component()
            st.markdown("---")
            self.clear_cache_button()
