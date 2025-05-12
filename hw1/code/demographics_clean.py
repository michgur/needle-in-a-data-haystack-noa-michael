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
        (df["life_exp_both"] > 100)
        | (df["life_exp_both"] < 40)
        | (df["life_exp_both"].isna())
    )
    print("Countries with missing / invalid life expectancy:", invalid_life_exp.sum())
    df = df[~invalid_life_exp]
    # c)
    df["urban_pop"] = df["urban_pop"].astype(int)
    df["pop_density"] = df["pop_density"].astype(int)
    invalid_pop = df["urban_pop"].isna() | df["pop_density"].isna()
    print(
        "Countries with missing / invalid urban population or population density:",
        invalid_pop.sum(),
    )
    df = df[~invalid_pop]
    # d)
    df["country"] = df["country"].apply(normalize_country_name)
    # e)
    diff = df["country"].compare(df_original["country"])
    diff.to_csv("output/name_mismatches.csv")
    df.set_index("country", inplace=True)

    pass
