"""
Functions to prepare the data for
the components
"""
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
from dateutil import parser
from loguru import logger
from pandas import DataFrame

from openstats.client import Client


class Data:
    """
    Class containing the methods to fetch data
    """

    def __init__(self, client: Client):
        self.client = client

        # Use client's Levy config
        self.config = self.client.config

    def stars_data(self) -> Optional[DataFrame]:
        """
        Extract information from stargazers.
        Prepare an accumulative sum of stars by date
        """
        today = datetime.today()
        delta = today - self.client.start_date

        try:
            stars = self.client.get_all(
                self.client.root
                / "repos"
                / self.client.owner
                / self.client.repo
                / "stargazers"
            )
            clean_stars = [
                parser.parse(user["starred_at"]).strftime("%Y/%m/%d") for user in stars
            ]
            star_counts = Counter(clean_stars)

            acc = 0
            for i in range(delta.days + 1):
                day = self.client.start_date + timedelta(days=i)
                day_str = day.strftime("%Y/%m/%d")
                if not star_counts.get(day_str):
                    star_counts[day_str] = acc

            sorted_dict = dict(sorted(star_counts.items()))
            df = pd.DataFrame(
                {"date": list(sorted_dict.keys()), "stars": list(sorted_dict.values())}
            )

            df["date"] = pd.to_datetime(df["date"])
            # This resample groups by week. Let's keep grouping by day.
            # df = df.resample("W", on="date")[["stars"]].sum()
            df["stars"] = df["stars"].cumsum()

            return df

        except Exception as err:  # pylint: disable=broad-except
            logger.error("Error trying to retrieve stars data...")
            logger.error(err)
            return None

    def health_data(self) -> Tuple[str, str]:
        """
        Obtain the health % from the community profile
        """
        profile_data = self.client.get(
            self.client.root
            / "repos"
            / self.client.owner
            / self.client.repo
            / "community"
            / "profile"
        ).json()
        percentage = profile_data.get("health_percentage", "Endpoint error")
        description = profile_data.get("description", "Error fetching description")

        return percentage, description

    @staticmethod
    def is_good_first_issue(issue: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Check if an issue is a good first issue
        """
        if isinstance(issue, dict):

            is_gfi = next(
                iter(
                    label
                    for label in issue.get("labels")
                    if isinstance(label, dict)
                    and label.get("name") == "good first issue"
                ),
                None,
            )

            return is_gfi

        return None

    @staticmethod
    def is_support_issue(issue: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Check if an issue is a support issue
        """
        if isinstance(issue, dict):
            is_support = next(
                iter(
                    label
                    for label in issue.get("labels")
                    if isinstance(label, dict) and label.get("name") == "support"
                ),
                None,
            )

            return is_support

        return None

    def _issues_data(self, filter_fn: Callable) -> Tuple[List[dict], List[dict]]:
        """
        Return issue data with callable filtering.

        filter_fn should return True / False from a list of issues
        """

        open_issues = self.client.get_all(
            self.client.root / "repos" / self.client.owner / self.client.repo / "issues"
        )

        open_filtered_issues = [issue for issue in open_issues if filter_fn(issue)]

        closed_issues = self.client.get_all(
            self.client.root
            / "repos"
            / self.client.owner
            / self.client.repo
            / "issues",
            "&state=closed",
        )

        closed_filtered_issues = [issue for issue in closed_issues if filter_fn(issue)]

        return open_filtered_issues, closed_filtered_issues

    def good_first_issues_data(self) -> Tuple[List[dict], List[dict]]:
        """
        Analyze issues data for open and closed good
        first issues.
        """

        return self._issues_data(filter_fn=self.is_good_first_issue)

    def support_issues_data(self) -> Tuple[List[dict], List[dict]]:
        """
        Analyzes issues data for open and closed support issues
        """

        return self._issues_data(filter_fn=self.is_support_issue)

    def contributors_data(self):
        """
        Get all project contributors.

        Return them sorted by contributions
        """

        data = self.client.get_all(
            self.client.root
            / "repos"
            / self.client.owner
            / self.client.repo
            / "contributors"
        )
        sorted_contrib = sorted(data, key=lambda d: d["contributions"], reverse=True)

        df = pd.DataFrame(sorted_contrib)

        # df.reset_index(inplace=True)
        # df.set_index("index", drop=False, inplace=True)

        return df

    def traffic_data(self):
        """
        Cook traffic data and views
        for the last 14 days
        """
        clones = self.client.get_all(
            self.client.root
            / "repos"
            / self.client.owner
            / self.client.repo
            / "traffic"
            / "clones"
        ).get("uniques")
        views = self.client.get_all(
            self.client.root
            / "repos"
            / self.client.owner
            / self.client.repo
            / "traffic"
            / "views",
            option="&per=week",
        ).get("uniques")

        return clones, views

    def get_participation(self, owner: str, repo: str):
        """
        Get all participation data for the last 52 weeks
        as a reversed list
        """
        return self.client.get(
            self.client.root / "repos" / owner / repo / "stats" / "participation"
        ).json()["all"]

    def competitors_data(self) -> DataFrame:
        """
        Compare your project stats vs. a list
        of competitors.

        Return my activity a list of competitor's activity
        """
        my_activity = {
            self.client.repo: self.get_participation(
                self.client.owner, self.client.repo
            )
        }

        activity = {
            competitor.repo: self.get_participation(competitor.owner, competitor.repo)
            for competitor in self.config.competitors
        }

        return pd.DataFrame({**my_activity, **activity})

    def weekly_commits(self) -> DataFrame:
        """
        Get weekly commits for the last 52 weeks
        with its date
        """

        my_activity = {
            "commits": self.get_participation(self.client.owner, self.client.repo)
        }

        # Today minus days from Sunday
        last_sunday = datetime.today() - timedelta(
            days=datetime.today().isoweekday() % 7
        )

        # Prepare dates
        dates = [
            (last_sunday - timedelta(weeks=1 * i)).strftime("%Y/%m/%d")
            for i in range(52)
        ]
        dates.reverse()

        return pd.DataFrame({**my_activity, "date": dates})
