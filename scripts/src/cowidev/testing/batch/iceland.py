import re
import json

import pandas as pd

from cowidev.testing import CountryTestBase
from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_date_series, clean_count


class Iceland(CountryTestBase):
    location: str = "Iceland"
    units: str = "tests performed"
    source_label: str = "Government of Iceland"
    source_url_ref: str = "https://www.covid.is/data"
    source_url: str = "https://e.infogram.com/"
    regex: dict = {
        "title_test": r"Fjöldi sýna eftir dögum",
        "title_positive": r"Fjöldi smita innanlands",
        "element": r"window\.infographicData=({.*})",
    }
    rename_columns: dict = {
        "Symptomatic tests": "t1",
        "Sympotmatic tests": "t1",
        "Quarantine- and random tests": "t2",
        "deCODE Genetics screening": "t3",
        "Border tests 1 and 2": "t4",
        "Border tests": "t4",
        "Domestic infections": "p1",
        "Symptomatic screening": "p1",
        "Quarantine- and random screening": "p2",
        "Screening by deCODE Genetics": "p3",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        data_id = self._get_data_id_from_source(self.source_url_ref)
        data = self._load_data(data_id)
        df = self._build_df(data)
        return df

    def _get_data_id_from_source(self, source_url: str) -> str:
        """Get Data ID from source"""
        soup = get_soup(source_url)
        data_id = soup.find(class_="infogram-embed")["data-id"]
        return data_id

    def _load_data(self, data_id):
        """Load data from source"""
        url = f"{self.source_url}{data_id}"
        soup = get_soup(url)
        match = re.search(self.regex["element"], str(soup))
        if not match:
            raise ValueError("Website Structure Changed, please update the script")
        data = json.loads(match.group(1))
        return data

    def _build_df(self, data: dict) -> pd.DataFrame:
        """Create dfs from raw data"""
        data = data["elements"]["content"]["content"]["entities"]
        data_test = [v for v in data.values() if re.search(self.regex["title_test"], str(v))][0]
        data_positive = [v for v in data.values() if re.search(self.regex["title_positive"], str(v))][0]
        data_list = data_test["props"]["chartData"]["data"] + data_positive["props"]["chartData"]["data"]

        df222 = pd.DataFrame(data_list[0], columns=data_list[0][0]).drop(0)
        df222 = df222[df222.iloc[:, 0] != ""]
        df222.columns = df222.columns.fillna("")

        df221 = pd.DataFrame(data_list[1], columns=data_list[1][0]).drop(0)
        df221 = df221[df221.iloc[:, 0] != ""]

        df21 = pd.DataFrame(data_list[2], columns=data_list[2][0]).drop(0)
        df21 = df21[df21.iloc[:, 0] != ""]

        df20 = pd.DataFrame(data_list[3], columns=data_list[3][0]).drop(0)
        df20 = df20[df20.iloc[:, 0] != ""]

        df = pd.concat([df222, df221, df21, df20])

        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean date"""
        return df.assign(Date=clean_date_series(df.iloc[:, 0], "%d.%m.%y")).sort_values("Date")

    def pipe_row_sum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sum rows"""
        df["Daily change in cumulative total"] = df[["t1", "t2", "t3"]].applymap(clean_count).sum(axis=1)
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_date).pipe(self.pipe_row_sum).pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, float_format="%.5f")


def main():
    Iceland().export()
