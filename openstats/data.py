"""
Functions to prepare the data for
the components
"""
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

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
            df = df.resample("W", on="date")[["stars"]].sum()
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

    def good_first_issues_data(self) -> Tuple[List[dict], List[dict]]:
        """
        Analyze issues data for open and closed good
        first issues.
        """

        open_issues = self.client.get_all(
            self.client.root / "repos" / self.client.owner / self.client.repo / "issues"
        )

        open_first_issues = [
            issue for issue in open_issues if self.is_good_first_issue(issue)
        ]

        closed_issues = self.client.get_all(
            self.client.root
            / "repos"
            / self.client.owner
            / self.client.repo
            / "issues",
            "&state=closed",
        )

        closed_first_issues = [
            issue for issue in closed_issues if self.is_good_first_issue(issue)
        ]

        return open_first_issues, closed_first_issues

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
