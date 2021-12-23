import pandas as pd


def main():
    print("Downloading US data…")

    url = "https://healthdata.gov/api/views/g62h-syeh/rows.csv"
    df = pd.read_csv(
        url,
        usecols=[
            "date",
            "total_adult_patients_hospitalized_confirmed_covid",
            "total_pediatric_patients_hospitalized_confirmed_covid",
            "staffed_icu_adult_patients_confirmed_covid",
            "previous_day_admission_adult_covid_confirmed",
            "previous_day_admission_pediatric_covid_confirmed",
        ],
    )

    df["date"] = pd.to_datetime(df.date, format="%Y/%m/%d").astype(str)
    df = df[df.date >= "2020-07-15"]
    df = df.groupby("date", as_index=False).sum().sort_values("date")

    df["total_hospital_stock"] = df.total_adult_patients_hospitalized_confirmed_covid.fillna(0).add(
        df.total_pediatric_patients_hospitalized_confirmed_covid.fillna(0)
    )
    df["total_hospital_flow"] = df.previous_day_admission_adult_covid_confirmed.fillna(0).add(
        df.previous_day_admission_pediatric_covid_confirmed.fillna(0)
    )
    df["total_hospital_flow"] = df.total_hospital_flow.rolling(7).sum()

    df = (
        df[["date", "total_hospital_stock", "total_hospital_flow", "staffed_icu_adult_patients_confirmed_covid"]]
        .melt("date", var_name="indicator")
        .dropna(subset=["value"])
    )
    df["indicator"] = df.indicator.replace(
        {
            "total_hospital_stock": "Daily hospital occupancy",
            "staffed_icu_adult_patients_confirmed_covid": "Daily ICU occupancy",
            "total_hospital_flow": "Weekly new hospital admissions",
        }
    )

    df["entity"] = "United States"

    return df


if __name__ == "__main__":
    main()
