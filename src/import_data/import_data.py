import os
import requests
import json
import asyncio

from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytz

from src.config.constant import CBOE_URL, PROVIDER_LIST, UTC, UTC_NAME
from system.file_paths import get_data_dir_imported, get_data_dir
from src.import_data.provider.cboe.cboe_data import GetCboeData, transform_data

###############################################################
###############################################################
### Class -> Refresh Options Symbols, JSON files
###############################################################
###############################################################


class ImportOptionSymbol:
    def __init__(self, symbol_dir='cboe_symbols'):

        self.symbol_dir = get_data_dir()  / symbol_dir
        self.current_dir = get_data_dir_imported()
        self.ALL_SYMBOL_LIST = []

        if not os.path.exists(self.symbol_dir):
            os.makedirs(self.symbol_dir)

    ###############################################################
    ### Import CBOE Symbol and Convert it to JSON
    ###############################################################

    def download_csv(self):
        try:
            response = requests.get(CBOE_URL, stream=True)
            response.raise_for_status() 
            
            return pd.read_csv(BytesIO(response.content))
        except requests.exceptions.RequestException as e:
            print(f"Error -> downloading: {e}")
            return pd.DataFrame()

    def download_symbol_json(self):
        data = self.download_csv()
        if not data.empty:

            data_symbol = sorted(data['Underlying'].unique().tolist(), key=len)
            file_path = os.path.join(self.symbol_dir, 'all_options_symbol.json')
            
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Old JSON file deleted : {file_path}")
            
            with open(file_path, 'w') as f:
                json.dump(data_symbol, f)
            print(f"Symbols saved in -> {file_path}")
            status = True
        else:
            print("Error: DataFrame empty, check URL or data retrieval.")
            status = False

        return status


    ###############################################################
    ### Create JSON file All Symbol existing in provider from json (CBOE)
    ###############################################################


    def create_json_info(self, dict_info, provider, selected_option):

        json_filename = f'{selected_option}_info.json'
        json_path = None  

        if provider == 'search':
            for listed_provider in PROVIDER_LIST:

                symbol_dir = (Path(self.current_dir) / listed_provider / selected_option).resolve()

                if os.path.exists(symbol_dir):
                    dict_info['provider'] = provider
                    dict_info['market_place'] = provider
                    print(f"Directory selected: {symbol_dir}")

                    json_path = os.path.join(symbol_dir, json_filename)
                    break

                else:
                    
                    return False
        else:
        
            symbol_dir = (Path(self.current_dir) / provider / selected_option).resolve()
            
            if not os.path.exists(symbol_dir):
                os.makedirs(symbol_dir) 
            
            json_path = os.path.join(symbol_dir, json_filename)  

        if json_path is not None:
            if os.path.exists(json_path):
                os.remove(json_path)
                print(f"Old JSON file deleted: {json_path}")

            with open(json_path, 'w', encoding='utf-8') as file:
                json.dump(dict_info, file, ensure_ascii=False, indent=4)

            return True
        else:
            print("Error: json_path is None.")
            return False


    ###############################################################
    ### Load All Symbol existing in provider from json (CBOE)
    ###############################################################

    def load_all_symbol_json(self):

        file_path = os.path.join(self.symbol_dir, 'all_options_symbol.json')

        if not os.path.exists(file_path):
            print(f"File {file_path} not found. Creating the file...")
            return []  

        try:
            with open(file_path, 'r') as f:
                data_symbol = json.load(f)
                
                if isinstance(data_symbol, list):
                    print(f"Symbols loaded from {file_path}")

                    return data_symbol
                else:
                    print("Error decoding JSON file. Content may be corrupted..")

                    return []  
        except json.JSONDecodeError:
            print("Error decoding JSON file. Content may be corrupted.")
            return []  
        except Exception as e:
            print(f"Unknown error : {e}")
            return []  


###############################################################
###############################################################
### Class -> Import data from Provider
###############################################################
###############################################################

class OptionsDataFetcher:
    def __init__(self):
     
        self.current_dir = get_data_dir_imported()
        self.nombre_demo = 5
        self.options_ticker = None
        self.boolean_save = None

    def get_last_weekday(self, today):
        week_day = today.weekday()  
        
        if week_day == 5:  
            return today - timedelta(days=1), week_day
        elif week_day == 6:  
            return today - timedelta(days=2), week_day
        return today, week_day

    def create_daily_folder(self, now, ticker_dir, df):

        hour_time = "close"

        if now.hour < 15 or (now.hour == 15 and now.minute < 30):
            today = now - timedelta(days=1)
            hour_time = 'close'

        elif now.hour > 22 or (now.hour == 22):
            today = now
            hour_time = 'close'

        else:
            today = now
            hour_time = now.strftime('%H:%M')

        date_folder, week_day = self.get_last_weekday(today)
        if week_day ==6 or week_day == 5:
            hour_time = 'close'

        date_str = date_folder.strftime("%Y-%m-%d")

        df['dte'] = (pd.to_datetime(df['expiration']).dt.tz_localize('UTC').dt.tz_convert(UTC) - date_folder).dt.days + 1

        folder_path = (Path(ticker_dir) / date_str).resolve()

        os.makedirs(folder_path, exist_ok=True)
        
        return date_str, hour_time, df
    


    def get_options_data_cboe(self, options_ticker, boolean_save):

        self.options_ticker = options_ticker
        self.boolean_save = boolean_save

        df = pd.DataFrame()

        async def run_cboe_data_process(ticker):
            cboe_data = GetCboeData()
            result = await cboe_data.cboe_request(ticker)  
            return result

        try:
            
            ticker_dir = (Path(self.current_dir) / 'CBOE' / self.options_ticker).resolve()
            
            if not os.path.exists(ticker_dir):
                os.makedirs(ticker_dir)
        
            json_data = asyncio.run(run_cboe_data_process(self.options_ticker))

            df, now_ = transform_data(json_data)
    
          
        except Exception as e:
            pass
        
        if self.boolean_save:
      
            now = now_.astimezone(pytz.timezone(UTC))
            date_str, hour_time, df_filtered = self.create_daily_folder(now, ticker_dir, df)

            utc_value = UTC_NAME[UTC]

            utc_value = utc_value.replace(':', '_')
            hour_time = hour_time.replace(':', '_')
            
            file_path = Path(ticker_dir) / date_str / f'{date_str}_{hour_time}_{utc_value}_{self.options_ticker}.csv'
            
            print(f"Saving to path: {file_path}")
            
            if file_path.exists():
                file_path.unlink()  
                
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            df_filtered.to_csv(file_path)
            print(f"Data saved successfully to {file_path}")
        
        else:
            return df_filtered
