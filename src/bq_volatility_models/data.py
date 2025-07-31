"""Ingest and prepare the data."""

import json
from datetime import date

import pandas as pd
import yfinance as yf  # type: ignore[import-untyped]

from bq_volatility_models import utils


def _get_data_name(ticker: str, maturities: list[date], call_put: str = "call") -> str:
    """Generate name for data file."""
    return f"{ticker}_{'_'.join(m.strftime('%Y%m%d') for m in maturities)}_{call_put}"


def ingest(
    ticker: str,
    maturities: list[date],
    call_put: str = "call",
) -> tuple[pd.DataFrame, object]:
    """Ingest the data.

    :param ticker: The ticker symbol for the asset.
    :param maturities: A list of maturity dates for the options.
    :param call: Whether to get call options (True) or put options (False).
    :return: The data.
    """
    data_path_core = utils.DATA_DIR / _get_data_name(ticker, maturities, call_put)
    data_path_core.mkdir(parents=True, exist_ok=True)
    data_path_options = data_path_core / "options.csv"
    data_path_underlying = data_path_core / "underlying.json"
    try:
        options_df: pd.DataFrame = pd.read_csv(
            data_path_options,
            index_col=0,
            parse_dates=True,
        )
        with data_path_underlying.open("r") as f:
            underlying = json.load(f)
    except FileNotFoundError:
        yf_ticker = yf.Ticker(ticker)
        options_dict: dict[date, pd.DataFrame] = {}
        for maturity in maturities:
            mo = yf_ticker.option_chain(maturity.strftime("%Y-%m-%d"))
            mo_ = mo.calls if call_put == "call" else mo.puts
            options_dict[maturity] = mo_.set_index("strike")
        options_df = pd.concat(options_dict, axis="index", names=["maturity", "strike"])
        underlying = mo.underlying
        options_df.to_csv(data_path_options)
        with data_path_underlying.open("w") as f:
            json.dump(underlying, f)
    return options_df, underlying


def prepare(options: pd.DataFrame) -> pd.DataFrame:
    """Prepare the data."""
    options.loc[:, "price"] = (options.loc[:, "bid"] + options.loc[:, "ask"]) / 2
    return options
