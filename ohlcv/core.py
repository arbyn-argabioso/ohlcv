"""Module containing the main OHLCV fetcher function."""

from __future__ import annotations

from functools import lru_cache
from functools import partial
from pathlib import Path
import asyncio
import collections
import datetime as dtlib
import os
import hmac
import hashlib
import time

from datetimerange import DateTimeRange
from ratelimiter import RateLimiter
from tqdm import tqdm
import ccxt.async_support as ccxt  # noqa: E402
import pandas as pd
import requests

from etl.ohlcv import logging
from etl.ohlcv.timeframe import Timeframe
from etl.ohlcv.util.datetime_util import get_milliseconds
from etl.ohlcv.util.datetime_util import get_valid_start_end
from etl.ohlcv.util.datetime_util import get_datetime_now
from etl.ohlcv.util.datetime_util import get_datetime
from etl.ohlcv.util.string_util import generate_id
from etl.ohlcv.util.string_util import lowerstrip


BTC_START = "2009-01-01 00:00:00+00:00"

OHLCV_COLUMNS = ["datetime", "open", "high", "low", "close", "volume"]
OHLCV_LIMITS = {
    # 10% of indicated CCXT limits
    "binance": 900,
    "bitmex": 450,
    "bitstamp": 900,
    "ftx": 4500,
}
TIMESTAMP_DIVIDERS = {
    "1m": 1_000 * 60,
    "1h": 1_000 * 60 * 60,
    "1d": 1_000 * 60 * 60 * 24,
}


# Create local logger
logger = logging.get_logger()


async def fetch(
    exchange: str | ccxt.Exchange,
    symbol: str,
    timeframe: str,
    *,
    start: dtlib.datetime | str | int | None = None,
    end: dtlib.datetime | str | int | None = None,
    now: dtlib.datetime | None = None,
    include_latest: bool = False,
    show_progress: bool = False,
) -> pd.DataFrame:
    """Returns a set of OHLCV data given certain parameters.

    Arguments:
        exchange_name: Exchange name
        symbol: The trading pair symbol
        timeframe: Timeframe of the data to fetch. Some
            examples of valid timeframe strings are `"2h"` for two
            hour, `"1d"` for one day, and `"1w"` for 1 week.
        start: Starting datetime of the data to be fetched.
            The input argument can be a string indicating a
            valid datetime-like string or a number indicating the
            timestamp in milliseconds. Defaults to `None`.
        end: Ending timestamp of the data to be fetched.
            The input argument can be a string indicating a
            valid datetime-like string or a number indicating the
            timestamp in milliseconds. Defaults to `None`.
        include_latest: Determines if we include the latest, unfinished,
            OHLCV or not. Defaults to `False`.
    """
    exchange_is_str = isinstance(exchange, str)
    if exchange_is_str:
        exchange_name = lowerstrip(exchange)
        exchange = getattr(ccxt, exchange_name)(
            {
                "enableRateLimit": True,
                "timeout": 60_000,
            }
        )
    else:
        exchange_name = lowerstrip(exchange.name)

    # Standardize the timeframe object and limit value
    timeframe = Timeframe(timeframe)
    limit = OHLCV_LIMITS.get(exchange_name, 500)

    # Make sure that the start and end times are valid
    start, end = get_valid_start_end(
        start,
        end,
        timeframe,
        now=now,
        timeframe_multiplier=limit,
        include_latest=include_latest,
    )

    # Create a datetime range from the initial start and end
    # datetimes and create a limit-based timedelta to generate a
    # list of new start and end timedates for the async OHLCV fetch
    time_range = DateTimeRange(start, end)
    time_range_tf = Timeframe(
        interval=(timeframe.interval * limit - 1),
        unit=timeframe.unit,
    )
    time_ranges = time_range.range(time_range_tf.to_timedelta())
    time_range_tf.interval = time_range_tf.interval + 2

    # Create a standard Pandas datetime index
    # this is also used for estimating the progress bar total
    ohlcv_indices = pd.period_range(
        start, end, freq=timeframe.unit.to_pandas()
    ).to_timestamp()

    pbar = None
    if show_progress:
        pbar = tqdm(total=len(ohlcv_indices), ncols=79, unit=" OHLCV")

    coroutines = []
    ohlcvs = []

    for batch_start in reversed(list(time_ranges)):
        coroutines.append(
            _fetch(
                exchange,
                ohlcvs,
                symbol,
                str(timeframe),
                since=get_milliseconds(batch_start),
                limit=limit,
                pbar=pbar,
            )
        )

    await asyncio.gather(*coroutines)

    if exchange_is_str:
        await exchange.close()

    # Remove extra milliseconds from exchange returns. For example
    # the exact millisecond should be 1590436800000 but the exchange
    # returns 1590436800043, we want to remove that extra 43 ms
    ohlcvs = pd.DataFrame(ohlcvs, columns=OHLCV_COLUMNS)
    divider = TIMESTAMP_DIVIDERS[str(timeframe)]
    ohlcvs["datetime"] = ohlcvs["datetime"].apply(
        lambda x: int(x / divider) * divider,
    )
    ohlcvs = indexify(ohlcvs, ohlcv_indices)

    # Finish progress bar
    if show_progress:
        pbar.total = len(ohlcvs)
        pbar.n = pbar.total

    return ohlcvs


def indexify(
    ohlcvs: pd.DataFrame,
    ohlcv_indices: list | None = None,
) -> pd.DataFrame:
    ohlcvs = ohlcvs[OHLCV_COLUMNS].set_index("datetime")

    # Remove duplicates and sort the raw datetime indices
    ohlcvs.index = pd.to_datetime(ohlcvs.index, unit="ms")
    are_there_duplicates = ohlcvs.index.duplicated(keep="last")
    if any(are_there_duplicates):
        ohlcvs = ohlcvs[~are_there_duplicates]
    ohlcvs = ohlcvs.sort_index()

    # Apply standardized index and then do a forward-fill filter
    if ohlcv_indices is not None:
        ohlcvs = ohlcvs.reindex(ohlcv_indices, method="ffill")

    # Remove any remaining null values
    ohlcvs.dropna(inplace=True)

    return ohlcvs


async def _fetch(
    exchange: ccxt.Exchange,
    ohlcvs: list,
    symbol: str,
    timeframe: str,
    since: dtlib.datetime,
    limit: int,
    pbar: tqdm | None = None,
):
    ohlcv = None

    # Exponential retry
    for i in [0, 2, 4, 8, 16, 32, 64]:
        try:
            ohlcv = await exchange.fetch_ohlcv(
                symbol,
                timeframe,
                since=since,
                limit=limit,
            )

            # Break out of the retry loop
            break

        except ccxt.NetworkError as error:
            await asyncio.sleep(i)

        except ccxt.ExchangeError as error:
            print('ohlcv.fetch failed due to an exchange error:', str(error))
            raise

        except Exception as error:
            print('ohlcv.fetch failed with:', str(error))
            raise

    if ohlcv is None:
        return

    if pbar is not None:
        pbar.update(len(ohlcv))

    ohlcvs += ohlcv


async def get_oldest_datetime(exchange: "ccxt.Exchange", symbol: str):
    exchange_name = lowerstrip(exchange.name)
    mid = exchange.markets[symbol]["id"]

    methods = {
        "binance": partial(_get_binance_oldest_datetime, symbol),
        "ftx": partial(_get_ftx_oldest_datetime, symbol),
        "bitmex": partial(_get_bitmex_oldest_datetime, mid),
        "bitstamp": partial(_get_bitstamp_oldest_datetime, mid),
    }

    try:
        return methods[exchange_name]()
    except KeyError:
        pass

    now = get_datetime_now()
    ohlcvs = await fetch(
        exchange,
        symbol,
        "1d",
        start=BTC_START,
        end=now,
        now=now,
        show_progress=False,
        include_latest=False,
    )

    # If the OHLCV is empty, don't even bother proceeding
    if ohlcvs.empty:
        return None

    datetime_oldest = ohlcvs.index[0]
    return datetime_oldest


@RateLimiter(max_calls=1_000, period=60)
def _get_binance_oldest_datetime(mid: str):
    api_url = (
        f"https://api.binance.com/api/v3/klines?symbol={mid}&"
        f"interval=1m&startTime=1230739200000&limit=1"
    )

    response = requests.get(api_url)
    try:
        timestamp = int(response.json()[0][0])
        return dtlib.datetime.fromtimestamp(
            timestamp / 1_000.0, tz=dtlib.timezone.utc
        )
    except Exception:
        return None


def _get_ftx_oldest_datetime(symbol: str):
    api_url = (
        f"https://ftx.com/api/markets/{symbol}/candles?resolution=2592000"
    )

    response = requests.get(api_url)

    try:
        datetime = response.json()["result"][0]["startTime"]
        return get_datetime(datetime)
    except Exception:
        return None


@RateLimiter(max_calls=120, period=60)
def _get_bitmex_oldest_datetime(mid: str):
    api_path = (
        f"/api/v1/trade/bucketed?binSize=1d&partial=false&"
        f"symbol={mid}&columns=timestamp&count=1&reverse=false"
    )
    api_url = f"https://www.bitmex.com{api_path}"

    expires = int(round(time.time()) + 3_600)
    key = "yVCkIp4n0ZeW6paILb1Y8YLz"
    secret = "z-0LdeSdATgW7ESbuqeltArJK4ioxhEgR88ni_fwNw2Kys4e"

    response = requests.get(
        api_url,
        headers={
            "api-expires": str(expires),
            "api-key": key,
            "api-signature": hmac.new(
                secret.encode("utf-8"),
                f"GET{api_path}{expires}".encode("utf-8"),
                digestmod=hashlib.sha256,
            ).hexdigest()
        }
    )

    try:
        datetime = response.json()[0]["timestamp"]
        return get_datetime(datetime)
    except Exception:
        return None


def _get_bitstamp_oldest_datetime(mid: str):
    starts = [1230739200, 1489680000, 1748620800]
    for start in starts:
        api_url = (
            f"https://www.bitstamp.net/api/v2/ohlc/{mid.lower()}/?"
            f"step=259200&limit=999&start={start}"
        )

        response = requests.get(api_url)

        try:
            timestamp = int(response.json()["data"]["ohlc"][0]["timestamp"])
            return dtlib.datetime.fromtimestamp(
                timestamp, tz=dtlib.timezone.utc
            )

        except Exception:
            continue

    return None


def unique(ohlcvs: pd.DataFrame) -> pd.DataFrame:
    are_there_duplicates = ohlcvs.index.duplicated(keep="last")

    if any(are_there_duplicates):
        output = ohlcvs[~are_there_duplicates]
    else:
        output = ohlcvs

    return output.sort_index()
