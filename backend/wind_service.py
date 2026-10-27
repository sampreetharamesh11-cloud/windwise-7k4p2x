
from datetime import date, datetime, timedelta, timezone
from collections import defaultdict

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


def hour_key(timestamp):
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    dt = dt.astimezone(timezone.utc)
    dt = dt.replace(minute=0, second=0, microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


async def get_wind_analysis(start_date: str, end_date: str):
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if start > end:
        raise ValueError("start_date must be before or equal to end_date")

    async with httpx.AsyncClient(timeout=90.0) as client:
        # Fetch actual national wind generation.
        actual_response = await client.get(
            f"{BASE_URL}/datasets/FUELHH",
            params={
                "settlementDateFrom": start_date,
                "settlementDateTo": end_date,
                "fuelType": "WIND",
            },
        )
        actual_response.raise_for_status()
        actual_body = actual_response.json()
        actuals = (
            actual_body.get("data", [])
            if isinstance(actual_body, dict)
            else actual_body
        )

        # Fetch historical forecast versions.
        forecast_from = start - timedelta(days=3)
        forecast_response = await client.get(
            f"{BASE_URL}/datasets/WINDFOR",
            params={
                "publishDateTimeFrom": (
                    f"{forecast_from.isoformat()}T00:00:00Z"
                ),
                "publishDateTimeTo": f"{end_date}T00:00:00Z",
            },
        )
        forecast_response.raise_for_status()
        forecast_body = forecast_response.json()
        forecasts = (
            forecast_body.get("data", [])
            if isinstance(forecast_body, dict)
            else forecast_body
        )

    # Group half-hour actual readings into complete hourly averages.
    actual_groups = defaultdict(list)

    for record in actuals:
        if record.get("startTime") and record.get("generation") is not None:
            key = hour_key(record["startTime"])
            actual_groups[key].append(float(record["generation"]))

    actual_hourly = {
        key: sum(values) / 2
        for key, values in actual_groups.items()
        if len(values) == 2
    }

    # Select the latest forecast published before each delivery day.
    selected_by_day = {}

    current_day = start
    while current_day <= end:
        day_string = current_day.isoformat()
        cutoff = f"{day_string}T00:00:00Z"

        candidates = [
            record for record in forecasts
            if record.get("startTime", "").startswith(day_string)
            and record.get("publishTime", "") < cutoff
        ]

        if candidates:
            latest_publish = max(
                record["publishTime"] for record in candidates
            )
            selected_by_day[day_string] = [
                record for record in candidates
                if record["publishTime"] == latest_publish
            ]

        current_day += timedelta(days=1)

    # Match forecasts and actuals using the same UTC hour.
    comparisons = []

    for day_records in selected_by_day.values():
        for forecast in day_records:
            if (
                not forecast.get("startTime")
                or forecast.get("generation") is None
            ):
                continue

            key = hour_key(forecast["startTime"])

            if key not in actual_hourly:
                continue

            actual = actual_hourly[key]
            predicted = float(forecast["generation"])

            comparisons.append({
                "time": key,
                "actual": round(actual, 2),
                "forecast": predicted,
                "error": round(predicted - actual, 2),
            })

    comparisons.sort(key=lambda row: row["time"])

    if not comparisons:
        return {
            "startDate": start_date,
            "endDate": end_date,
            "metrics": None,
            "records": [],
            "message": "No matching actual and forecast intervals found.",
        }

    errors = [row["error"] for row in comparisons]
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = (sum(error ** 2 for error in errors) / len(errors)) ** 0.5

    percentage_errors = [
        abs(row["error"] / row["actual"]) * 100
        for row in comparisons
        if row["actual"] != 0
    ]
    mape = (
        sum(percentage_errors) / len(percentage_errors)
        if percentage_errors else None
    )

    return {
        "startDate": start_date,
        "endDate": end_date,
        "metrics": {
            "maeMW": round(mae, 2),
            "rmseMW": round(rmse, 2),
            "mapePercent": round(mape, 2) if mape is not None else None,
            "matchedHours": len(comparisons),
            "actualRecords": len(actuals),
        },
        "records": comparisons,
        "message": None,
    }
