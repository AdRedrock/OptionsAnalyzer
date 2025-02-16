import os
import json
import numpy as np

from datetime import datetime, date
from pathlib import Path

import pandas as pd
import pytz
import dask.dataframe as dd
import yfinance as yf

from src.import_data.import_data import ImportOptionSymbol

from src.config.constant import PROVIDER_LIST, UTC, CBOE_CLOSE_UTC, UTC_NAME
from system.file_paths import get_data_dir_imported, get_global_dir


###############################################################
###############################################################
### Class -> Check JSON, St...
###############################################################
###############################################################

class CheckFileAndData:
    def __init__(self):
     
        self.current_dir = get_data_dir_imported()

    def check_st_yfinance(self, st):
        try:
            ticker = yf.Ticker(st)
            info = ticker.info  

            if 'symbol' in info and info['symbol'] == st:
                return True
            else:
                return False
        except Exception as e:
            print(f"Error fetching data for {st}: {e}")
            return False
        
    def check_json(self, provider, selected_option):

        json_path = None   

        symbol_dir = symbol_dir = (Path(self.current_dir) / provider / selected_option).resolve()
        json_path = f'{symbol_dir}/{selected_option}_info.json'
        
        if not json_path or not os.path.exists(json_path):
            print(f"File does not exist at path: {json_path}")
            return False
        
        return True
    

###############################################################
###############################################################
### Class -> Loading Data, St
###############################################################
###############################################################

class LoadingData:
    def __init__(self):
     
        self.current_dir = get_data_dir_imported()


    ###############################################################
    ### Get the most Recent Date (for date picker Range Montecarlo)
    ###############################################################

    def get_max_start_date(self, ticker):

        underlying_ticker, change, quotation_type, quotation_type_value, lot_size = self.load_st_ticker_info_json(provider='search', selected_option=ticker)
 
        stock = yf.Ticker(underlying_ticker)
        
        historical_data = stock.history(period="max")  

        if not historical_data.empty:
            max_start_date = historical_data.index.min() 
            return max_start_date.date()  
        else:
            return None


    ###############################################################
    ### Import CSV data Already imported
    ###############################################################

    def get_data_csv(self, selected_option, selected_date, selected_hour):

        utc_value = UTC_NAME[UTC]

        print(selected_date)
        print(selected_hour)
        print(utc_value)
        print(selected_option)

        if selected_hour == CBOE_CLOSE_UTC:
            selected_hour = 'close'
      
        utc_value = utc_value.replace(":", "_")

        file_name = f'{selected_date}_{selected_hour}_{utc_value}_{selected_option}.csv'
    
        symbol_dirs = (
            (Path(self.current_dir) / provider / selected_option / selected_date).resolve()
            for provider in PROVIDER_LIST
        )
        
        for symbol_dir in symbol_dirs:
            if symbol_dir.exists():
                file_path = symbol_dir / file_name
                
                try:
                    ddf = dd.read_csv(str(file_path), assume_missing=True)
                
                    df = ddf.compute()
                    return df
                except FileNotFoundError:
                    print(f"File not found : {file_path}")
                except pd.errors.EmptyDataError:
                    print(f"Empty file : {file_path}")
                except Exception as e:
                    print(f"Error : {e}")
        
        raise ValueError(f"File not found {selected_option} to date {selected_date}")
    
    ###############################################################
    ### Get St price with Hour  
    ###############################################################

    def get_st_price_hour(self, info=None, selected_date='', selected_hour='', ticker=None):
        """
        function has improved. Important for VR calculations
        """

        if info:
            underlying_ticker = info['underlying_ticker']
        elif info is None and ticker is not None:
            underlying_ticker = ticker
        else:
            print("No Ticker")
            return 0.0

        try:
            selected_date = pd.to_datetime(selected_date)
            selected_hour = pd.to_datetime(selected_hour, format='%H_%M').time()
            end_date = selected_date + pd.Timedelta(days=1)
        except Exception as e:
            print(f"Error (date): {e}")
            return 0.0

    
        def localize_timezone(df):
            if df.empty:
                return df
            try:
                if df.index.tz is not None:
                    df.index = df.index.tz_convert(UTC)
                else:
                    df.index = df.index.tz_localize('UTC').tz_convert(UTC)
            except Exception:
                pass  
            return df

        def calculate_median_price(df_row):
            try:
                if df_row.empty:
                    return None
                    
                price_columns = ['Open', 'High', 'Low', 'Close']
                available_columns = [col for col in price_columns if col in df_row.columns]
                
                if not available_columns:
                    return None

                all_prices = df_row[available_columns].values.flatten()
                value = round(float(np.median(all_prices)), 2)
                
                return value
                
            except Exception as e:
                print(f"Erreur median: {e}")
                return None

        def get_1m_data():
            try:
                if selected_date == datetime.now().astimezone(pytz.timezone(UTC)):
                    data = yf.download(underlying_ticker, period='1d', interval='1m', multi_level_index=False)
                else:
                    data = yf.download(underlying_ticker,
                                    start=selected_date.strftime('%Y-%m-%d'),
                                    end=end_date.strftime('%Y-%m-%d'),
                                    interval='1m',
                                    multi_level_index=False)
                data = localize_timezone(data)
                if not data.empty:
                    data_filtered = data[data.index.time == selected_hour]

                    if not data_filtered.empty and 'Close' in data_filtered.columns:
          
                        return round(float(data_filtered['Close'].iloc[0]), 2)
                    
            except Exception as e:
                print(f"Error 1m data: {e}")
            return None

        def get_1h_data():
            try:

                data = yf.download(underlying_ticker,
                                start=selected_date.strftime('%Y-%m-%d'),
                                end=end_date.strftime('%Y-%m-%d'),
                                interval='1h',
                                multi_level_index=False)
                
                if data.empty:
                    return None

                data.index = pd.to_datetime(data.index)
                if data.index.tz is None:
                    data.index = data.index.tz_localize('UTC').tz_convert(UTC)
                else:
                    data.index = data.index.tz_convert(UTC)

                target_time = pd.Timestamp.combine(selected_date.date(), selected_hour).tz_localize(UTC)
                
                closest_hour = data.index[abs(data.index - target_time).argmin()]
                row = data.loc[closest_hour:closest_hour]
                
                return calculate_median_price(row)
                
            except Exception as e:
                print(f"Error 1H data: {e}")
                return None

        def get_1d_data():
            try:

                data = yf.download(underlying_ticker,
                                start=selected_date.strftime('%Y-%m-%d'),
                                end=end_date.strftime('%Y-%m-%d'),
                                interval='1d',
                                multi_level_index=False)
                
                if data.empty:
                    return None

                if selected_hour == '21:59':
                    return data['Close'].iloc[0]

                data.index = pd.to_datetime(data.index)
                if data.index.tz is None:
                    data.index = data.index.tz_localize('UTC').tz_convert(UTC)
                else:
                    data.index = data.index.tz_convert(UTC)
                    
                target_time = pd.Timestamp.combine(selected_date.date(), selected_hour).tz_localize(UTC)

                closest_hour = data.index[abs(data.index - target_time).argmin()]
                row = data.loc[closest_hour:closest_hour]
                
                return calculate_median_price(row)
                
            except Exception as e:
                return None
        
        try:
          
            result = get_1m_data()
            if result is not None and result > 0:
                return result

            result = get_1h_data()
            if result is not None and result > 0:
                return result

            result = get_1d_data()
            if result is not None and result > 0:
                return result

        except Exception as e:
            print(f"Global Error: {e}")
            return 0.0

    ###############################################################
    ### get last underlying price
    ###############################################################

    def get_last_st(self, info=None, to_date=False, selected_date='', ticker=None):
            """
            Retrieves the latest share price for a given ticker.
            """
            try:
                # Déterminer le ticker
                if info:
                    underlying_ticker = info['underlying_ticker']
                elif ticker:
                    underlying_ticker = ticker
                else:
                    print("Error: info or ticker must be supplied")
                    return 0.0

                now = datetime.now().astimezone(pytz.timezone('UTC'))

                if not to_date:
                    return self._fetch_recent_data(underlying_ticker, now)
                else:
                    return self._fetch_historical_data(underlying_ticker, selected_date, now)

            except Exception as e:
                print(f"Data recovery error for {underlying_ticker}: {str(e)}")
                return 0.0

    def _fetch_recent_data(self, ticker, now):
 
        day_range = now - pd.Timedelta(days=3)
        last_data = yf.download(
            ticker,
            start=day_range.strftime('%Y-%m-%d'),
            end=now.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if last_data.empty:
            return 0.0
            
        self.last_st = round(last_data['Close'].iloc[-1].to_numpy()[0], 2)
        return self.last_st

    def _fetch_historical_data(self, ticker, selected_date, now):
 
        try:
            selected_date = pd.to_datetime(selected_date)
   
            if selected_date.date() == now.date():
                last_data = yf.download(ticker, period='1d', interval='1m')
            else:
       
                end_date = selected_date - pd.Timedelta(days=1)
                last_data = self._download_data(ticker, end_date, selected_date)
                
                if last_data.empty:
                    end_date = selected_date - pd.Timedelta(days=3)
                    last_data = self._download_data(ticker, end_date, selected_date)

            if not last_data.empty:
                self.last_st = round(last_data['Close'].iloc[-1].to_numpy()[0], 2)
            else:
                self.last_st = 0.0

            return self.last_st

        except Exception as e:
            print(f"Error in retrieving historical data for {ticker}: {str(e)}")
            return 0.0

    def _download_data(self, ticker, start_date, end_date):

        try:
            return yf.download(
                ticker,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1d'
            )
        except Exception as e:
            print(f"Download failed for {ticker}: {str(e)}")
            return pd.DataFrame()
    

    ###############################################################
    ### Load Settings JSON File
    ###############################################################

    def load_settings_json(self):

        json_filename = f'settings.json'

        symbol_dir = (get_global_dir() / 'user_config').resolve()

        json_path = symbol_dir / json_filename

        if not json_path or not os.path.exists(json_path):
            print(f"File does not exist at path: {json_path}")
            return None

        try:
            with open(json_path, 'r') as json_file:
                data = json.load(json_file)
                user_utc = data.get('timezone', 'Europe/Paris')
                print('user utc -->', user_utc)
                return user_utc

        except KeyError as e:
            print(f"KeyError: Missing key {e} in JSON file: {json_path}")
        except Exception as e:
            print(f"Error loading JSON file: {e}")

        return None
    
    def change_settings_json(self, value):

        json_filename = f'settings.json'

        symbol_dir = (Path(__file__).resolve().parent.parent.parent / 'user_config').resolve()

        json_path = symbol_dir / json_filename

        if not json_path or not os.path.exists(json_path):
            print(f"File does not exist at path: {json_path}")
            return None

        try:
            with open(json_path, 'r') as json_file:
                data = json.load(json_file)
            
            data['timezone'] = value
                
            with open(json_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)

            print(f"Timezone successfully updated to: {value}")
        

        except KeyError as e:
            print(f"KeyError: Missing key {e} in JSON file: {json_path}")
        except Exception as e:
            print(f"Error loading JSON file: {e}")

        return None

    ###############################################################
    ### Load underlying info JSON File
    ###############################################################

    def load_st_ticker_info_json(self, provider, selected_option):

        json_path = None
        json_filename = f'{selected_option}_info.json'
       
        if provider == 'search':
            for listed_provider in PROVIDER_LIST:
            
                symbol_dir = (Path(self.current_dir) / listed_provider / selected_option).resolve()

                if os.path.exists(symbol_dir):
                    
                    json_path = os.path.join(symbol_dir, json_filename)
                    break
        else:
          
            symbol_dir = (Path(self.current_dir) / provider / selected_option).resolve()
        
            json_path = symbol_dir / f"{selected_option}_info.json"
        

        print(f"Checking JSON path: {json_path}")
        if not json_path or not os.path.exists(json_path):
            print(f"File does not exist at path: {json_path}")
            return selected_option, None, [], [], []

        try:
            with open(json_path, 'r') as json_file:
                data = json.load(json_file)
                underlying_ticker = data.get('underlying_ticker', None)
                change = data.get('change', 0)
                quotation_type = data.get('quotation_type', None)
                quotation_type_value = data.get('quotation_type_value', None)
                lot_size = data.get('lot_size', None)

                print(f"Data loaded for {selected_option}:")

                return underlying_ticker, change, quotation_type, quotation_type_value, lot_size

        except KeyError as e:
            print(f"KeyError: Missing key {e} in JSON file: {json_path}")
        except Exception as e:
            print(f"Error loading JSON file: {e}")

        return selected_option, None, [], [], []
    
    ###############################################################
    ### Load Dates Already Imported
    ###############################################################
    
    def load_date_imported(self, option_ticker, hour=False, selected_date=None):
        date_list = []

        if selected_date and isinstance(selected_date, date):
       
            selected_date = selected_date.strftime('%Y-%m-%d')

        for provider in PROVIDER_LIST:

            if not hour:

                symbol_dir = (Path(self.current_dir) / provider / option_ticker).resolve()

                if not symbol_dir.exists():
                    continue

                try:
              
                    date_list = sorted(set(
                        file[:10] 
                        for file in os.listdir(symbol_dir) 
                        if not file.endswith(".json") and len(file) >= 10
                    ))
                    
                    return date_list

                except OSError as e:
                    print(f"Error accessing {symbol_dir}: {e}")
                
            elif hour and selected_date:
                
                symbol_dir = (Path(self.current_dir) / provider / option_ticker / selected_date).resolve()
            
                if not symbol_dir.exists():
                    continue
            
                try:
    
                    hour_list = sorted(set(
                        file[11:16] 
                        for file in os.listdir(symbol_dir) 
                        if not file.endswith(".json") and len(file) >= 10
                    ))
                    
                    return hour_list

                except OSError as e:
                    print(f"Error accessing {symbol_dir}: {e}")
            
        return []
    
    
    ###############################################################
    ### Load Symbol Already Imported
    ###############################################################

    def load_existing_symbols(self):
        class_ImportOptionSymbol = ImportOptionSymbol()
        ALL_SYMBOL_LIST = class_ImportOptionSymbol.load_all_symbol_json()

        SYMBOL_LIST = []  

        for provider in PROVIDER_LIST:

            symbol_dir = (Path(self.current_dir) / provider).resolve()

            if not os.path.exists(symbol_dir):
                print(f"Directory does not exist: {symbol_dir}")
                continue

            existing_symbols = [
                entry.name for entry in os.scandir(symbol_dir) if entry.is_dir()
            ]

            SYMBOL_LIST.extend(symbol for symbol in existing_symbols if symbol in ALL_SYMBOL_LIST)

        return SYMBOL_LIST
    
    
###############################################################
###############################################################
### Class -> Convert Data,
###############################################################
###############################################################

class ConvertData:
    def __init__(self):
     
        self.current_dir = get_data_dir_imported()


    ###############################################################
    ### Convert Hour Format
    ###############################################################

    def format_hours_for_dropdown(self, hours_list):
        formatted_options = []
        close_option = {}
        
        user_utc = LoadingData().load_settings_json()
        
        for hour in hours_list:
            if hour != 'close':

                
          
                today = datetime.now()
            
                time_obj = datetime.strptime(f"{today.date()} {hour}", "%Y-%m-%d %H_%M")
                
                time_obj = pytz.UTC.localize(time_obj)

                print(today)
                print(time_obj)
                print(hour)
                
                utc_convert = time_obj.astimezone(pytz.timezone(user_utc))
                
                am_pm_format = utc_convert.strftime("%I:%M %p").lstrip("0")
                
                formatted_options.append({
                    "label": am_pm_format,
                    "value": hour
                })
            elif hour == 'close':
                close_option = {
                    "label": 'Close',
                    "value": '21_59'
                }
        
        if close_option:
            formatted_options.append(close_option)

        sorted_hour_list = sorted(formatted_options,
                                key=lambda x: datetime.strptime(x["value"], "%H_%M"),
                                reverse=True)
        
        return sorted_hour_list

     ###############################################################
    ### Convert expiration to day & expiration_bis to date of imported DataFrame
    ###############################################################

    def convert_expiration_to_day(self, df, current_date_str, day_string=True, expiration_bis=False):
      
        if isinstance(current_date_str, str):
            current_date = pd.Timestamp(current_date_str)
        else:
            current_date = pd.Timestamp(current_date_str)
        
        col = 'expiration_bis' if expiration_bis else 'expiration'
        
        if isinstance(df, pd.DataFrame):
        
            df[col] = pd.to_datetime(df[col])
            
            df['expiration_in_day'] = (df[col] - current_date).dt.days
            
            if day_string:
                return df['expiration_in_day'].apply(lambda x: f"{x} days")
            return df['expiration_in_day'] 
            
        elif isinstance(df, list):
    
            converted_df = []
            for entry in df:
                expiration_date = pd.Timestamp(entry)
                expiration_in_days = (expiration_date - current_date).days
                
                if day_string:
                    converted_df.append(f"{expiration_in_days} days")
                else:
                    converted_df.append(expiration_in_days)
            return converted_df
        
        else:
            raise TypeError("Input data must be a DataFrame or a list.")


        