import pandas as pd


def normalize_country_name(name: str) -> str:
    name = name.strip()
    if name.lower().startswith("the "):
        name = name[4:]
    return name.title()


if __name__ == "__main__":
    # 4.1
    df_original = pd.read_csv("output/demographics_data.csv")
    df = df_original.copy()

    # b)
    invalid_life_exp = (
        (df["LifeExpectancy_Both"] > 100)
        | (df["LifeExpectancy_Both"] < 40)
        | (df["LifeExpectancy_Both"].isna())
    )
    print("Countries with missing / invalid life expectancy:", invalid_life_exp.sum())
    df = df[~invalid_life_exp]
    # c)
    df["UrbanPopulation_Absolute"] = df["UrbanPopulation_Absolute"].astype(int)
    df["PopulationDensity"] = df["PopulationDensity"].astype(int)
    invalid_pop = df["UrbanPopulation_Absolute"].isna() | df["PopulationDensity"].isna()
    print(
        "Countries with missing / invalid urban population or population density:",
        invalid_pop.sum(),
    )
    df = df[~invalid_pop]
    # d)
    df["Country"] = df["Country"].apply(normalize_country_name)
    # e)
    diff = df["Country"].compare(df_original["Country"])
    diff.to_csv("output/name_mismatches.csv")
    df.set_index("Country", inplace=True)

    pass
