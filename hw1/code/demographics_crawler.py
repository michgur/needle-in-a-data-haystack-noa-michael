import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


# all country links in the hub have the `data-country` attribute.
# we utilize this fact to find all countries
def get_country_urls(hub_url: str) -> dict[str, str]:
    soup = BeautifulSoup(requests.get(hub_url).text, "html.parser")
    country_links = soup.select("[data-country]")
    countries = {
        link.text: urljoin(hub_url, str(link.attrs["href"]))
        for link in country_links
        if link.attrs.get("href")
    }
    return countries


# exctraction strategy: for each field:
# 1. find the matching element using html selectors
# 2. extract the value from the element's text content using regex patterns
# 3. cast the value to a numeric data type
def get_country_demographic_data(country_url: str) -> dict[str, Any]:
    # field -> (selector, pattern, dtype)
    data_points = {
        "LifeExpectancy_Both": ("#life-exp + p + div", r"Both Sexes\s+(\d*\.?\d+)", float),
        "LifeExpectancy_Female": ("#life-exp + p + div", r"Females\s+(\d*\.?\d+)", float),
        "LifeExpectancy_Male": ("#life-exp + p + div", r"Males\s+(\d*\.?\d+)", float),
        "UrbanPopulation_Absolute": ("#urb + p", r"\(([0-9,]+) people in \d*\)", int),
        "UrbanPopulation_Percentage": ("#urb + p > strong", r"(\d*\.?\d+)", float),
        "PopulationDensity": ("#population-density + p", r"(\d+) people per Km2", int),
    }  # fmt: skip
    result = {}
    soup = BeautifulSoup(requests.get(country_url).text, "html.parser")
    for field, (selector, pattern, dtype) in data_points.items():
        if elt := soup.select_one(selector):
            if match := re.search(pattern, elt.text):
                try:
                    numeric_str = match.group(1).replace(",", "")
                    result[field] = dtype(numeric_str)
                    continue
                except:
                    pass
        result[field] = None
    return result


if __name__ == "__main__":
    print("Extracting country list")
    countries = get_country_urls("https://www.worldometers.info/demographics/")
    rows = []
    for i, (country, url) in enumerate(countries.items()):
        print(f"Extracting {country}'s data ({i + 1}/{len(countries)})")
        data = get_country_demographic_data(url)
        data["Country"] = country
        rows.append(data)
    df_demographics = pd.DataFrame(rows)
    Path("output").mkdir(exist_ok=True)
    df_demographics.to_csv("output/demographics_data.csv", index=False)

    df_before_sort = df_demographics.head(10)
    print(df_before_sort)
    df_before_sort.to_csv("output/demographics_before_sort.csv", index=False)

    df_demographics.sort_values("Country", inplace=True)
    df_after_sort = df_demographics.head(10)
    print(df_after_sort)
    df_after_sort.to_csv("output/demographics_after_sort.csv", index=False)

    df_demographics = pd.read_csv("output/demographics_data.csv")
    for column in df_demographics.columns:
        if not pd.api.types.is_numeric_dtype(df_demographics[column]):
            continue
        print(f"\nCrawled stats of {column}")
        print(df_demographics[column].describe().apply("{0:.2f}".format))
        print(f"Missing (or zero) values of {column}: ", end="")
        print((df_demographics[column] == 0 | df_demographics[column].isna()).sum())

    print(
        f"\nCorrelation between LifeExpectancy_Both and PopulationDensity is {
            df_demographics['LifeExpectancy_Both'].corr(
                df_demographics['PopulationDensity'], method='pearson'
            )
        }"
    )
