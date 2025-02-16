import pandas as pd
import requests
from io import BytesIO
import asyncio

from datetime import datetime

"""
The source code below has been taken from the open source library openbb and adapted to the needs of this program.
"""



CBOE_COMPANY_URL = "https://www.cboe.com/us/options/symboldir/equity_index_options/?download=csv"
CBOE_INDEX_URL = "https://cdn.cboe.com/api/global/us_indices/definitions/all_indices.json"

TICKER_EXCEPTIONS = ["NDX", "RUT"]

COLUMNS_ORDER = [
        'underlying_symbol',
        'underlying_price',
        'contract_symbol',
        'expiration',
        'dte',
        'strike',
        'option_type',
        'open_interest',
        'volume',
        'theoretical_price',
        'last_trade_price',
        'tick',
        'bid',
        'bid_size',
        'ask',
        'ask_size',
        'open',
        'high',
        'low',
        'prev_close',
        'change',
        'change_percent',
        'implied_volatility',
        'delta',
        'gamma',
        'theta',
        'vega',
        'rho'
        ]

class GetCboeData:
    def __init__(self):
        pass

    async def get_company_directory(self) -> pd.DataFrame:
        
        response = requests.get(CBOE_COMPANY_URL)
        if response.status_code != 200:
            raise Exception()

        directory = pd.read_csv(BytesIO(response.content))

        directory = directory.rename(
            columns={
                " Stock Symbol": "symbol",
                " DPM Name": "dpm_name",
                " Post/Station": "post_station",
                "Company Name": "name",
            }
        ).set_index("symbol")

        directory = directory.astype(str)

        return directory


    async def get_index_directory(self) -> pd.DataFrame:

        response = requests.get(CBOE_INDEX_URL)
        if response.status_code != 200:
            raise Exception(f"CBOE error: {response.status_code}")

        results = response.json()

        for result in results:
            for key in ["featured", "featured_order", "display"]:
                result.pop(key, None)

        results = pd.DataFrame(results)

        results = results[results["source"] != "morningstar"]

        return results.set_index("index_symbol")


    async def cboe_request(self, selected_symbol: str):

        
        indexes = await self.get_index_directory()
        listed_symbols = await self.get_company_directory()

        if selected_symbol not in listed_symbols.index:
            print(f"{selected_symbol} not found in CBOE symbols directory")
            return None

        quotes_url = (
            f"https://cdn.cboe.com/api/global/delayed_quotes/options/_{selected_symbol}.json"
            if selected_symbol in indexes.index or selected_symbol in TICKER_EXCEPTIONS
            else f"https://cdn.cboe.com/api/global/delayed_quotes/options/{selected_symbol}.json"
        )

        response = requests.get(quotes_url) 
        
        return response.json()


async def run_cboe_data_process(options_ticker):
    cboe_data = GetCboeData()
    result = await cboe_data.cboe_request(options_ticker)  # Utilisation de await pour exécuter la fonction asynchrone
    return result


def transform_data(data):
   
    from pandas import DataFrame, DatetimeIndex, Series, to_datetime
    from datetime import datetime

    options = data.get("data", {}).pop("options", [])
    
    options_df = DataFrame.from_records(options)
    options_df = options_df.rename(
        columns={
            "option": "contract_symbol",
            "iv": "implied_volatility",
            "theo": "theoretical_price",
            "percent_change": "change_percent",
            "prev_day_close": "prev_close",
        }
    )
    
    option_df_index = options_df["contract_symbol"].str.extractall(
        r"^(?P<Ticker>\D*)(?P<expiration>\d*)(?P<option_type>\D*)(?P<strike>\d*)"
    )
    option_df_index = option_df_index.reset_index().drop(
        columns=["match", "level_0"]
    )
    
    option_df_index.option_type = option_df_index.option_type.str.replace(
        "C", "call"
    ).str.replace("P", "put")
    
    option_df_index.strike = [ele.lstrip("0") for ele in option_df_index.strike]
    option_df_index.strike = Series(option_df_index.strike).astype(float)
    option_df_index.strike = option_df_index.strike * (1 / 1000)
    option_df_index.strike = option_df_index.strike.to_list()
    
    option_df_index.expiration = [
        ele.lstrip("1") for ele in option_df_index.expiration
    ]
    option_df_index.expiration = DatetimeIndex(
        option_df_index.expiration, yearfirst=True
    ).astype(str)
    
    option_df_index = option_df_index.rename(
        columns={"Ticker": "underlying_symbol"}
    )
    
    quotes = option_df_index.join(options_df)
    
    now = datetime.now()
    temp = DatetimeIndex(quotes.expiration)
    temp_ = (temp - now).days + 1
    quotes["dte"] = temp_
    
    quotes["last_trade_time"] = (
        to_datetime(quotes["last_trade_time"], format="%Y-%m-%dT%H:%M:%S")
        .fillna(value="-")
        .replace("-", None)
    )
    
    quotes = quotes.set_index(
        keys=["expiration", "strike", "option_type"]
    ).sort_index()
    
    if data.get("data", {}).get("current_price"):
        quotes["underlying_price"] = data["data"]["current_price"]
    
    quotes["open_interest"] = quotes["open_interest"].astype("int64")
    quotes["volume"] = quotes["volume"].astype("int64")
    quotes["bid_size"] = quotes["bid_size"].astype("int64")
    quotes["ask_size"] = quotes["ask_size"].astype("int64")
    quotes["prev_close"] = quotes["prev_close"]
    quotes["change_percent"] = quotes["change_percent"] / 100

    quotes = quotes.reset_index()[COLUMNS_ORDER]


    return quotes, now


