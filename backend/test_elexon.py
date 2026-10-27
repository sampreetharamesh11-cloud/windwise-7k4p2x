
import asyncio
import httpx
from collections import defaultdict
from datetime import datetime, timezone

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


def hour_key(timestamp):
    """Normalize a UTC timestamp to the start of its hour."""
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    dt = dt.astimezone(timezone.utc)
    dt = dt.replace(minute=0, second=0, microsecond=0)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:

        # Fetch actual wind generation for January 15.
        actual_url = f"{BASE_URL}/datasets/FUELHH"
        actual_params = {
            "settlementDateFrom": "2026-01-15",
            "settlementDateTo": "2026-01-15",
            "fuelType": "WIND",
        }

        print("\nFetching actual generation...")
        response = await client.get(actual_url, params=actual_params)
        print("Actual status:", response.status_code)
        response.raise_for_status()

        body = response.json()
        actuals = body.get("data", []) if isinstance(body, dict) else body
        print("Actual records:", len(actuals))

        # Fetch forecasts published before and during January 15.
        forecast_url = f"{BASE_URL}/datasets/WINDFOR"
        forecast_params = {
            "publishDateTimeFrom": "2026-01-13T00:00:00Z",
            "publishDateTimeTo": "2026-01-17T00:00:00Z",
        }

        print("\nFetching historical forecasts...")
        response = await client.get(forecast_url, params=forecast_params)
        print("Forecast status:", response.status_code)
        response.raise_for_status()

        body = response.json()
        forecasts = body.get("data", []) if isinstance(body, dict) else body
        print("Forecast records:", len(forecasts))

        # Choose the latest forecast published before January 15 UTC.
        delivery_day = "2026-01-15"
        cutoff = "2026-01-15T00:00:00Z"

        day_records = [
            record for record in forecasts
            if record.get("startTime", "").startswith(delivery_day)
            and record.get("publishTime", "") < cutoff
        ]

        if not day_records:
            print("No day-ahead forecast found.")
            return

        latest_publish = max(
            record["publishTime"] for record in day_records
        )
        selected = [
            record for record in day_records
            if record["publishTime"] == latest_publish
        ]

        # Group actual half-hour readings by their UTC hour.
        actual_groups = defaultdict(list)

        for record in actuals:
            if record.get("startTime") and record.get("generation") is not None:
                key = hour_key(record["startTime"])
                actual_groups[key].append(float(record["generation"]))

        # Use only complete hours: exactly two half-hour actual readings.
        actual_hourly = {
            key: sum(values) / 2
            for key, values in actual_groups.items()
            if len(values) == 2
        }

        # Match forecast and actual values at the same UTC hour.
        comparisons = []

        for forecast in selected:
            if forecast.get("startTime") is None or forecast.get("generation") is None:
                continue

            key = hour_key(forecast["startTime"])

            if key not in actual_hourly:
                continue

            actual = actual_hourly[key]
            predicted = float(forecast["generation"])

            comparisons.append({
                "time": key,
                "actual": actual,
                "forecast": predicted,
                "error": predicted - actual,
            })

        comparisons.sort(key=lambda row: row["time"])

        print("\nDelivery day:", delivery_day)
        print("Forecast publication:", latest_publish)
        print("Selected forecast records:", len(selected))
        print("Matched complete hours:", len(comparisons))

        if not comparisons:
            print("No matching hours; accuracy metrics cannot be calculated.")
            return

        mae = sum(abs(row["error"]) for row in comparisons) / len(comparisons)
        rmse = (
            sum(row["error"] ** 2 for row in comparisons)
            / len(comparisons)
        ) ** 0.5

        nonzero = [
            row for row in comparisons if row["actual"] != 0
        ]
        mape = (
            sum(abs(row["error"] / row["actual"]) * 100 for row in nonzero)
            / len(nonzero)
            if nonzero else None
        )

        print(f"MAE: {mae:.2f} MW")
        print(f"RMSE: {rmse:.2f} MW")
        print(f"MAPE: {mape:.2f}%" if mape is not None else "MAPE: unavailable")

        print("\nFirst three matched hours:")
        for row in comparisons[:3]:
            print(row)


if __name__ == "__main__":
    asyncio.run(main())
