"""
Module containing helper utilities
to handle Github API calls
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests
import streamlit as st
from levy.config import Config


class Client:
    """
    Manage API requests to extract data
    """

    def __init__(self, config: Config):
        self.root = Path(config.client.root)
        self.owner = config.client.owner
        self.repo = config.client.repo

        self.token = self._get_token()
        self.start_date = datetime.strptime("Aug 1 2021", "%b %d %Y")

        self.headers = {
            "Accept": "application/vnd.github.v3.star+json",
            "Authorization": f"token {self.token}",
        }

    @staticmethod
    def _get_token():
        """
        Retrieve API token
        """
        return os.environ.get("API_TOKEN") or st.secrets["API_TOKEN"]

    @staticmethod
    def url(path: Path) -> str:
        return "https://" + str(path)

    @staticmethod
    @st.experimental_memo
    def _get(path: str, headers: Dict[str, str]):
        return requests.get(path, headers=headers)

    def get(self, path: Path):
        """
        Prepare a HTTPS URL from the given path
        """
        return self._get(self.url(path), headers=self.headers)

    @staticmethod
    @st.experimental_memo
    def _get_all(path: str, headers: Dict[str, str], option: Optional[str] = None):

        option_str = option if option else ""

        req = path + "?simple=yes&per_page=100&page=1" + option_str

        res = requests.get(req, headers=headers)
        data = res.json()
        while "next" in res.links.keys():
            res = requests.get(res.links["next"]["url"], headers=headers)
            data.extend(res.json())

        return data

    def get_all(self, path: Path, option: Optional[str] = None):
        """
        Return all pages from a given request
        """
        return self._get_all(self.url(path), headers=self.headers, option=option)
