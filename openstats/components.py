"""
Module creating the different streamlit
components to show on the app
"""

from datetime import datetime

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

        if self.config("style", None):
            self.color = self.config.style("primary_color", "#7147E8")
        else:
            self.color = "#7147E8"

    def stars_component(self):
        """
        Prepare the graph to show the stars evolution
        and the differences
        """
        df = self.data.stars_data()

        if df is not None and not df.empty:
            current = int(df.iloc[-1].get("stars"))
            last_week = int(df.iloc[-7].get("stars"))
            last_month = int(df.iloc[-30].get("stars"))

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
                    color=alt.value(self.color),
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

    def support_issues_component(self):
        """
        Present the good first issues
        """
        open_supp, closed_supp = self.data.support_issues_data()

        with st.container():
            st.subheader("Support issues")

            open_issues, closed_issues = st.columns(2)
            open_issues.metric("Open support issues", len(open_supp))
            closed_issues.metric("Closed support issues", len(closed_supp))

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
                    color=alt.value(self.color),
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
        """
        Prepare the sidebar information with
        logo, profile and social
        """

        with st.sidebar.container():

            logo_file = self.config("logo_file", None)
            if logo_file:
                st.image(logo_file)
                st.write("\n\n")

            self.profile_component()
            st.markdown("---")
            self.clear_cache_button()

            st.write("\n\n")
            st.markdown(
                "Powered by [OpenStats](https://github.com/pmbrull/open-stats) 🚀"
            )

    def competitors_component(self):
        """
        Prepare a bar chart with commit activity
        if we are comparing competitors
        """

        if self.config("competitors", None):

            activity = self.data.competitors_data()

            last_month = activity[-4:].sum().to_frame(name="commits")
            last_month["repo"] = last_month.index

            with st.container():
                st.subheader("Competitors")

                bars = (
                    alt.Chart(
                        last_month,
                        title="Last month commit activity",
                    )
                    .mark_bar()
                    .encode(
                        x=alt.X(
                            "repo",
                            title="Repository",
                            sort=alt.EncodingSortField(
                                field="commits", op="count", order="descending"
                            ),
                            axis=alt.Axis(labelAngle=-45),
                        ),
                        y=alt.Y("commits", title="#Commits"),
                        color=alt.value(self.color),
                    )
                )

                text = bars.mark_text(
                    align="center",
                    baseline="middle",
                    fontSize=13,
                    dy=-8,  # Nudges text to top so it doesn't appear on top of the bar
                ).encode(
                    text="commits:Q",
                )

                chart = (bars + text).properties(
                    width=650,
                    height=350,
                )

                st.altair_chart(chart)

                button_col, desc_col = st.columns(2)
                button_col.download_button(
                    label="Download CSV",
                    data=activity.to_csv(index=False).encode("utf-8"),
                    file_name=f"commit_activity_{datetime.now().strftime('%Y%m%d')}",
                    mime="text/csv",
                )
                desc_col.write(
                    "Download the last 52 weeks of commit activity as a CSV file."
                )

    def weekly_commits_component(self):
        """
        Print line chart with weekly commits
        """

        commits = self.data.weekly_commits()

        with st.container():

            st.subheader("Weekly commits")

            lines = (
                alt.Chart(commits[30:])
                .mark_line()
                .encode(
                    x=alt.X("date", axis=alt.Axis(labelAngle=-45)),
                    y="commits:Q",
                    color=alt.value(self.color),
                )
            )

            text = lines.mark_text(
                align="center",
                baseline="middle",
                fontSize=13,
                dy=-13,  # Nudges text to top so it doesn't appear on top of the bar
            ).encode(
                text="commits:Q",
            )

            chart = (lines + text).properties(
                width=800,
                height=350,
            )

            st.altair_chart(chart)
