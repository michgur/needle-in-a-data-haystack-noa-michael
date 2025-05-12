from typing import Any
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd


def get_country_urls(hub_url: str) -> dict[str, str]:
    soup = BeautifulSoup(requests.get(hub_url).text, "html.parser")
    country_links = soup.select("[data-country]")
    countries = {
        link.text: urljoin(hub_url, str(link.attrs["href"]))
        for link in country_links
        if link.attrs.get("href")
    }
    return countries


def get_country_demographic_data(country_url: str) -> dict[str, Any]:
    # field -> (selector, pattern, dtype)
    data_points = {
        "life_exp_both": ("#life-exp + p + div", r"Both Sexes\s+(\d*\.?\d+)", float),
        "life_exp_female": ("#life-exp + p + div", r"Females\s+(\d*\.?\d+)", float),
        "life_exp_male": ("#life-exp + p + div", r"Males\s+(\d*\.?\d+)", float),
        "urban_pop": ("#urb + p", r"\(([0-9,]+) people in \d*\)", int),
        "urban_pop_percent": ("#urb + p > strong", r"(\d*\.?\d+)", float),
        "pop_density": ("#population-density + p", r"(\d+) people per Km2", int),
    }
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
        data["country"] = country
        rows.append(data)
    df_demographics = pd.DataFrame(rows)
    Path("output").mkdir(exist_ok=True)
    df_demographics.to_csv("output/demographics_data.csv", index=False)

    df_before_sort = df_demographics.head(10)
    print(df_before_sort)
    df_before_sort.to_csv("output/demographics_before_sort.csv", index=False)

    df_demographics.sort_values("country", inplace=True)
    df_after_sort = df_demographics.head(10)
    print(df_after_sort)
    df_after_sort.to_csv("output/demographics_after_sort.csv", index=False)
