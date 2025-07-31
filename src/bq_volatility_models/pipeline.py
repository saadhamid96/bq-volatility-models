"""Pipeline for data ingestion and model calibration."""

from datetime import datetime, timedelta, timezone

from bq_volatility_models import data


def run_pipeline() -> None:
    """Run the data ingestion and model calibration pipeline."""
    # Define parameters
    ticker = "^SPX"
    maturities = [
        datetime.now(tz=timezone.utc).date() + timedelta(days=i) for i in range(1, 11)
    ]
    call_put = "call"

    # Ingest data
    options_df, underlying = data.ingest(
        ticker=ticker,
        maturities=maturities,
        call_put=call_put,
    )

    # Prepare data
    options_df = data.prepare(options_df)
