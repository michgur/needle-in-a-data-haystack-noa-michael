import pandas as pd
import numpy as np


def normalize_country_name(name: str) -> str:
    name = name.strip()
    if name.lower().startswith("the "):
        name = name[4:]
    return name.title()


def z_score_normalize(col: pd.Series) -> pd.Series:
    return (col - col.mean()) / col.std()


def tukey_outliers(col: pd.Series) -> pd.Series:
    q1, q3 = col.quantile([0.25, 0.75])
    iqr = q3 - q1
    return (col < q1 - 1.5 * iqr) | (col > q3 + 1.5 * iqr)


def to_numeric_safe(col: pd.Series) -> pd.Series:
    return pd.to_numeric(  # type: ignore
        col.astype(str).str.replace(r"[^0-9.]", "", regex=True), errors="coerce"
    )


if __name__ == "__main__":
    # 3.2
    df_gdp = pd.read_csv("gdp_per_capita_2021.csv", na_values=["None"])
    df_pop = pd.read_csv("population_2021.csv", na_values=["None"])
    # b)
    expected_gdp_cols = ["Country", "GDP_per_capita_PPP"]
    missing_gdp = set(expected_gdp_cols) - set(df_gdp.columns)
    if missing_gdp:
        raise KeyError(f"Missing columns in df_gdp: {missing_gdp}")
    expected_pop_cols = ["Country", "Population"]
    missing_pop = set(expected_pop_cols) - set(df_pop.columns)
    if missing_pop:
        raise KeyError(f"Missing columns in df_pop: {missing_pop}")
    # c)
    df_gdp["GDP_per_capita_PPP"] = pd.to_numeric(
        df_gdp["GDP_per_capita_PPP"], errors="coerce"
    )
    df_pop["Population"] = pd.to_numeric(df_pop["Population"], errors="coerce")
    # d)
    print("df_gdp head before sort:")
    print(df_gdp.head(5))
    df_gdp.head(5).to_csv("output/gdp_before_sort.csv", index=False)
    print("df_pop head before sort:")
    print(df_pop.head(5))
    df_pop.head(5).to_csv("output/pop_before_sort.csv", index=False)
    df_gdp.sort_values("Country", inplace=True)
    print("\ndf_gdp head after sort:")
    print(df_gdp.head(5))
    df_gdp.head(5).to_csv("output/gdp_after_sort.csv", index=False)
    df_pop.sort_values("Country", inplace=True)
    print("\ndf_pop head after sort:")
    print(df_pop.head(5))
    df_pop.head(5).to_csv("output/pop_after_sort.csv", index=False)
    # e)
    df_gdp.describe().to_csv("output/gdp_describe.csv")
    df_pop.describe().to_csv("output/pop_describe.csv")

    print("df_gdp shape:", df_gdp.shape)
    print("df_gdp columns:", list(df_gdp.columns))

    print("df_pop shape:", df_pop.shape)
    print("df_pop columns:", list(df_pop.columns))

    # 4.1
    df_original = pd.read_csv("output/demographics_data.csv")
    df_demographics = df_original.copy()
    # b)
    invalid_life_exp = (
        (df_demographics["LifeExpectancy_Both"] > 100)
        | (df_demographics["LifeExpectancy_Both"] < 40)
        | (df_demographics["LifeExpectancy_Both"].isna())
    )
    print("Invalid life expectancy:", invalid_life_exp.sum())
    df_demographics = df_demographics[~invalid_life_exp]
    # c)
    df_demographics["UrbanPopulation_Absolute"] = df_demographics[
        "UrbanPopulation_Absolute"
    ].astype(int)
    df_demographics["PopulationDensity"] = df_demographics["PopulationDensity"].astype(
        int
    )
    invalid_pop = (
        df_demographics["UrbanPopulation_Absolute"].isna()
        | df_demographics["PopulationDensity"].isna()
    )
    print("Invalid urban population and population density:", invalid_pop.sum())
    df_demographics = df_demographics[~invalid_pop]
    # d)
    df_demographics["Country"] = df_demographics["Country"].apply(
        normalize_country_name
    )
    # e)
    df_demographics["Country"].compare(
        df_original["Country"], result_names=("New", "Old")
    ).to_csv("output/name_mismatches.csv", index=False)
    df_demographics.set_index("Country", inplace=True)

    # 4.2
    df_gdp["GDP_per_capita_PPP"] = to_numeric_safe(df_gdp["GDP_per_capita_PPP"])
    # b)
    invalid_gdp = df_gdp["GDP_per_capita_PPP"].isna()
    df_gdp[invalid_gdp].to_csv("output/dropped_gdp.csv", index=False)
    df_gdp = df_gdp[~invalid_gdp]
    # c)
    df_gdp["IsOutlier"] = tukey_outliers(df_gdp["GDP_per_capita_PPP"])
    print("GDP outliers:", df_gdp["IsOutlier"].sum())
    # d)
    print("GDP duplicates:", df_gdp["Country"].duplicated().sum())
    df_gdp.drop_duplicates("Country", inplace=True)
    df_gdp["Country"] = df_gdp["Country"].apply(normalize_country_name)
    # f)
    df_gdp.set_index("Country", inplace=True)

    # 4.3
    df_pop["Population"] = to_numeric_safe(df_pop["Population"])
    # b)
    invalid_pop = df_pop["Population"].isna()
    print("Population invalid rows:", invalid_pop.sum())
    df_pop = df_pop[~invalid_pop]
    # c)
    df_pop["IsOutlier"] = tukey_outliers(np.log10(df_pop["Population"]))
    print("Population outliers:", df_pop["IsOutlier"].sum())
    # d)
    print("Population duplicates:", df_pop["Country"].duplicated().sum())
    df_pop.drop_duplicates("Country", inplace=True)
    df_pop["Country"] = df_pop["Country"].apply(normalize_country_name)
    # e)
    df_pop.set_index("Country", inplace=True)

    # 5.1
    df_final = df_demographics.merge(
        df_gdp.merge(df_pop, how="inner", left_index=True, right_index=True),
        how="inner",
        left_index=True,
        right_index=True,
    )
    df_final["TotalGDP"] = df_final["GDP_per_capita_PPP"] * df_final["Population"]

    # 5.2
    df_final = df_final[
        (df_final[["GDP_per_capita_PPP", "Population"]] > 0).all(axis=1)
    ]
    df_final["LogGDPperCapita"] = np.log10(df_final["GDP_per_capita_PPP"])
    df_final["LogPopulation"] = np.log10(df_final["Population"])

    # 5.3
    df_final["LifeExpectancy_Both"] = z_score_normalize(df_final["LifeExpectancy_Both"])
    df_final["LogGDPperCapita"] = z_score_normalize(df_final["LogGDPperCapita"])
    df_final["LogPopulation"] = z_score_normalize(df_final["LogPopulation"])

    # 5.4
    lost = df_demographics.index.difference(df_final.index)
    lost.to_series().to_csv("output/lost_countries.csv", index=False)
    df_final["GDP_per_capita_PPP"] = df_final["GDP_per_capita_PPP"].fillna(
        df_final["GDP_per_capita_PPP"].mean()
    )
    df_final["Population"] = df_final["Population"].fillna(
        df_final["Population"].mean()
    )
    np.save(
        "output/X.npy",
        df_final[["LifeExpectancy_Both", "LogGDPperCapita", "LogPopulation"]].values,
    )
