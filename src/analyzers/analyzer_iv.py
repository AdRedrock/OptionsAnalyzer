import numpy as np
import datetime as dt
from datetime import date, timedelta, datetime

import pandas as pd
import pytz
import yfinance as yf
import plotly.graph_objects as go

from scipy.interpolate import PchipInterpolator, griddata
from scipy.signal import savgol_filter

from src.config.constant import UTC, CBOE_CLOSE_UTC
from src.import_data.utils import LoadingData, ConvertData, CheckFileAndData


################################################################################
###  IV smile
################################################################################

class IVSmileByStrike:
    def __init__(self, selected_option, selected_date, selected_date2, selected_hour, selected_hour2, info, exp_list, exp_list2, show_day, variation_dates):
        

        self.selected_option = selected_option
        self.selected_date = selected_date
        self.selected_date2 = selected_date2
        self.info = info

        self.exp_list = exp_list
        self.exp_list2 = exp_list2
        self.show_day = show_day
        self.variation_dates = variation_dates

        underlying_ticker = info['underlying_ticker'] 

        self.last_st = LoadingData().get_last_st(info)

        self.st_date1 = LoadingData().get_st_price_hour(None, selected_date, selected_hour, underlying_ticker)

        if variation_dates:
            self.st_date2 = LoadingData().get_st_price_hour(None, selected_date2, selected_hour2, underlying_ticker)


    def get_moneyness(self, moneyness, df_pivot, current_st):

        variations = sorted(df_pivot['dataframe_type'].unique())
        
        if current_st:
            for dataframe_type in variations:

                mask = df_pivot['dataframe_type'] == dataframe_type
                df_filtered = df_pivot.loc[mask].copy()

                if 'OTM' in moneyness:
                    df_filtered['call'] = df_filtered['call'].where(df_filtered['strike'] >= self.last_st, np.nan)
                    df_filtered['put'] = df_filtered['put'].where(df_filtered['strike'] <= self.last_st, np.nan)

                elif 'ITM' in moneyness:
                    df_filtered['call'] = df_filtered['call'].where(df_filtered['strike'] <= self.last_st, np.nan)
                    df_filtered['put'] = df_filtered['put'].where(df_filtered['strike'] >= self.last_st, np.nan)

                df_pivot.loc[mask, ['call', 'put']] = df_filtered[['call', 'put']]
        else:
            i = 1
            for dataframe_type in variations:

                if i == 1:
                    price = self.st_date1
                else:
                    price = self.st_date2

                mask = df_pivot['dataframe_type'] == dataframe_type
                df_filtered = df_pivot.loc[mask].copy()

                if 'OTM' in moneyness:
                    df_filtered['call'] = df_filtered['call'].where(df_filtered['strike'] > price, np.nan)
                    df_filtered['put'] = df_filtered['put'].where(df_filtered['strike'] < price, np.nan)

                elif 'ITM' in moneyness:
                    df_filtered['call'] = df_filtered['call'].where(df_filtered['strike'] < price, np.nan)
                    df_filtered['put'] = df_filtered['put'].where(df_filtered['strike'] > price, np.nan)

                df_pivot.loc[mask, ['call', 'put']] = df_filtered[['call', 'put']]

                i = i + 1

        return df_pivot
        
        

    def smileFunction(self, global_df, var_df, plot=True, moneyness='All', smooth_methods=None, current_st=True):

        col = 'expiration' if self.show_day else 'expiration_bis'
        
        df = global_df.copy()
        df['dataframe_type'] = 'current'

        if self.show_day:
            date_list = [int(date.split()[0]) for date in self.exp_list]
            if self.variation_dates:
                date_list2 = [int(date.split()[0]) for date in self.exp_list2]
        else:
            date_list = [pd.to_datetime(item).date() for item in self.exp_list]
            df[col] = pd.to_datetime(df[col])
            if self.variation_dates:
                date_list2 = [pd.to_datetime(item).date() for item in self.exp_list2]
                var_df[col] = pd.to_datetime(var_df[col])

        mask = df[col].isin(date_list)
        filtered_df = df[mask].copy()
        filtered_df.loc[:, 'implied_volatility'] = filtered_df['implied_volatility'] * 100
        
        if self.variation_dates:
            var_df_copy = var_df.copy()
            var_df_copy['dataframe_type'] = 'compare'
            mask2 = var_df_copy[col].isin(date_list2)
            filtered_df2 = var_df_copy[mask2].copy()
            filtered_df2.loc[:, 'implied_volatility'] = filtered_df2['implied_volatility'] * 100

            combined_df = pd.concat([filtered_df, filtered_df2], ignore_index=True)
        else:
            combined_df = filtered_df
        
        self.df_pivot = combined_df.pivot_table(
            index=[col, 'strike', 'dataframe_type'],
            columns='option_type',
            values='implied_volatility'
        ).reset_index()
        
        self.df_pivot = self.df_pivot.fillna(np.nan)        

        if current_st:
            self.df_pivot = self.get_moneyness(moneyness, self.df_pivot, current_st)
        
        else:
            self.df_pivot = self.get_moneyness(moneyness, self.df_pivot, current_st)

        if self.variation_dates:
            st_list = [self.last_st, self.st_date1, self.st_date2]
        else:
            st_list = [self.last_st, self.st_date1]
        
        if plot:
            fig = ImpliedVolatilityPlot().smileByStrike(
                self.df_pivot,
                col,
                self.show_day,
                smooth_methods,
                st_list=st_list,
                variation_dates=self.variation_dates,
                selected_date1=self.selected_date,
                selected_date2=self.selected_date2
            )
            return fig
        
        return self.df_pivot


################################################################################
###  Volumes By strike Indicator
################################################################################

class IVAtmAndRealizedVolatility:
    def __init__(self, selected_option, selected_date, selected_hour, max_history, info=None, ticker=None):

        self.selected_option = selected_option
        self.selected_date = selected_date
        self.selected_hour = selected_hour
        self.max_history = max_history
        self.st_ticker = info['underlying_ticker']

    def loadHistory(self):

        converted_selected_date = pd.to_datetime(self.selected_date).date()
        converted_max_date = pd.to_datetime(self.max_history).date()
    
        list_available_dates = LoadingData().load_date_imported(self.selected_option)
        list_available_dates = [pd.to_datetime(item).date() for item in list_available_dates]

        list_available_dates = [date for date in list_available_dates if converted_max_date <= date <= converted_selected_date]

        return list_available_dates
    
    def getAvailableDate(self, list_available_dates):

        available_data = {}

        for date_obj in list_available_dates:
          
            list_available_hour = LoadingData().load_date_imported(self.selected_option, True, date_obj)
 
            if date_obj not in available_data:
                available_data[date_obj.strftime('%Y-%m-%d')] = [] 

            available_data[date_obj.strftime('%Y-%m-%d')].extend(list_available_hour)

        return available_data

    def filterOptionsAtm(self, df, option_type, get_st):
         
        df_filtered = df[df['option_type'] == option_type].copy()
        df_filtered['strike_diff'] = df_filtered['strike'].sub(get_st).abs()
        idx_min_strike = df_filtered.groupby('dte')['strike_diff'].idxmin()
        return df_filtered.loc[idx_min_strike]

    def interpolateIvATM(self, df, target_dte=30):
                
        if df.empty or 'dte' not in df.columns:
            return np.nan

        df = df.sort_values('dte')
        
        exp_test = df[df['dte'] == target_dte]

        if not exp_test.empty:
            iv_target = exp_test.iloc[0]['implied_volatility']
            return iv_target, 30, 30

        df_below = df[df['dte'] <= target_dte].tail(1)
        df_above = df[df['dte'] >= target_dte].head(1)
    

        if not df_below.empty and not df_above.empty:
            
            dte_1, iv_1 = df_below.iloc[0]['dte'], df_below.iloc[0]['implied_volatility']
            dte_2, iv_2 = df_above.iloc[0]['dte'], df_above.iloc[0]['implied_volatility']
            iv_target = iv_1 + (target_dte - dte_1) * (iv_2 - iv_1) / (dte_2 - dte_1)

        elif not df_below.empty:
            
            iv_target = df_below.iloc[0]['implied_volatility']
        elif not df_above.empty:
            
            iv_target = df_above.iloc[0]['implied_volatility']
        else: 
    
            iv_target = np.nan
        
        return iv_target, dte_1, dte_2

    def getIVandRVData(self, indicator_exp='closest'):

        iv_dict = {}

        list_available_dates = self.loadHistory()
        available_data = self.getAvailableDate(list_available_dates)

        for key, item in available_data.items():
         
            for index, element in enumerate(item):

                call_value, put_value, dte_1, dte_2, useless1, useless2  = np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

                if element == 'close':  
                    item[index] = CBOE_CLOSE_UTC 

                df = LoadingData().get_data_csv(self.selected_option, key, item[index])
                df['underlying_price'] = pd.to_numeric(df['underlying_price'], errors='coerce')
                get_st = df['underlying_price']

                df['expiration'] = pd.to_datetime(df['expiration'])

                df_call = self.filterOptionsAtm(df, 'call', get_st)
                df_put = self.filterOptionsAtm(df, 'put', get_st)

                df_call['implied_volatility'] = pd.to_numeric(df_call['implied_volatility'], errors='coerce')
                df_put['implied_volatility'] = pd.to_numeric(df_put['implied_volatility'], errors='coerce')

                if indicator_exp == 'closest':
                    if not df_call.empty and 'dte' in df_call.columns:
                        min_date_idx = df_call['dte'].idxmin()
                        df_call = df_call.loc[min_date_idx:min_date_idx + 1]
                    
                    if not df_put.empty and 'dte' in df_put.columns:
                        min_date_idx = df_put['dte'].idxmin()
                        df_put = df_put.loc[min_date_idx:min_date_idx + 1]

                    call_value = df_call['implied_volatility'].iloc[0] if not df_call.empty else np.nan
                    put_value = df_put['implied_volatility'].iloc[0] if not df_put.empty else np.nan

                    dte_1 = df_call['dte'].iloc[0]
                    dte_2 = df_put['dte'].iloc[0]

                elif indicator_exp == '30':

                    call_value, dte_1, dte_2= self.interpolateIvATM(df_call, 30)
                    put_value, useless1, useless2 = self.interpolateIvATM(df_put, 30)
                
                else:
                    return None

                mean_iv = (call_value + put_value) / 2

                date_time_str = f"{key} {item[index]}"
                date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H_%M")

                new_key = date_time_obj.strftime("%Y-%m-%d-%H-%M")

                if new_key not in iv_dict:
                    iv_dict[new_key] = [float(mean_iv), call_value, put_value, dte_1, dte_2]


        final_df = pd.DataFrame.from_dict(iv_dict, orient='index', columns=['mean_iv', 'call_iv', 'put_iv', 'dte_1', 'dte_2'])
        final_df.reset_index(inplace=True)  
        final_df.rename(columns={'index': 'datetime'}, inplace=True)

        final_df['datetime'] = pd.to_datetime(final_df['datetime'], format="%Y-%m-%d-%H-%M")
        final_df = final_df.sort_values(by='datetime')

        return final_df


    def getRealizedVolatilityNearest(self, plot=True):

        df = self.getIVandRVData(indicator_exp='closest')

        today_not_converted = pd.Timestamp.today()
        today = today_not_converted.tz_localize('UTC')
        
        df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize('UTC')

        first_df = df[df['datetime'] >= today - pd.Timedelta(days=30)]
        second_df = df[~df['datetime'].isin(first_df['datetime'])]     

        if not first_df.empty: 
            for i, date_listed in enumerate(first_df['datetime']):
                closest_day_series = first_df.loc[first_df['datetime'] == date_listed, 'dte_1'].values[0]

                if closest_day_series == 0:
                    closest_day_series = 1
        
                if date_listed.date() != datetime.now().astimezone(pytz.timezone(UTC)):
     
                    try:
                        for i in range(1, 7):
                            new_closest_day = date_listed - pd.Timedelta(days=i)
                
                            data = yf.download(
                                self.st_ticker, 
                                start=new_closest_day.strftime('%Y-%m-%d'), 
                                end=date_listed.strftime('%Y-%m-%d'),  
                                interval='1h'
                            )

                            if not data.empty:
                                break
                    except:
                        print(f"Error: yfinance can't reach data --> {new_closest_day} to {date_listed}")
                else:

                    try:
                        for i in range(0, 7):
                            day_closest_day = date_listed - pd.Timedelta(days=closest_day_series + i)

                            data = yf.download(
                                self.st_ticker, 
                                start=day_closest_day.strftime('%Y-%m-%d'), 
                                end=date_listed.strftime('%Y-%m-%d'),  
                                interval='1h'
                            )

                            if not data.empty:
                                break

                    except:
                        print(f"Error: yfinance can't reach data --> {new_closest_day} to {date_listed}")

                data.index = pd.to_datetime(data.index)
                if data.index.tz is None:
                    data.index = data.index.tz_localize('UTC').tz_convert(UTC)
                else:
                    data.index = data.index.tz_convert(UTC)

                target_time = pd.Timestamp.combine(
                    date_listed.date(), 
                    pd.to_datetime(date_listed).time()
                ).tz_localize(UTC)

                closest_hour = data.index[abs(data.index - target_time).argmin()]
                data = data.loc[data.index <= closest_hour]

                data['returns'] = np.log(data['Close'] / data['Close'].shift(1))  
                realized_vol = np.sqrt(np.sum(data['returns']**2) / len(data))  
                annualized_vol = realized_vol * np.sqrt(252 * 6.5) 

                first_df.loc[first_df['datetime'] == date_listed, 'RV'] = annualized_vol

        if not second_df.empty: 
            for i, date_listed in enumerate(second_df['datetime']):
                closest_day_series = second_df.loc[second_df['datetime'] == date_listed, 'dte_1'].values[0]

                if closest_day_series == 0:
                    day_closest_day = date_listed - pd.Timedelta(days=1)
                else:
                    day_closest_day = date_listed - pd.Timedelta(days=closest_day_series)

                data = yf.download(
                    self.st_ticker, 
                    start=day_closest_day.strftime('%Y-%m-%d'), 
                    end=date_listed.strftime('%Y-%m-%d'),  
                    interval='1d'
                )

                data.index = pd.to_datetime(data.index)
                if data.index.tz is None:
                    data.index = data.index.tz_localize('UTC').tz_convert(UTC)
                else:
                    data.index = data.index.tz_convert(UTC)

                parkinson_vol = np.sqrt(np.sum((np.log(data['High']) - np.log(data['Low']))**2) / 
                                    (4 * np.log(2) * (len(data) - 1)))
                annualized_vol = parkinson_vol * np.sqrt(252)

                second_df.loc[second_df['datetime'] == date_listed, 'RV'] = annualized_vol

        if not first_df.empty or second_df.empty:
            merged_df = pd.concat([first_df, second_df], ignore_index=True)
            merged_df = merged_df.sort_values(by='datetime')
            merged_df = merged_df.reset_index(drop=True)
            merged_df = merged_df.reset_index()

            if plot:
                class_ = ImpliedVolatilityPlot()
                fig = class_.plotIVandIVR(merged_df, 'closest')
                return fig

    def getRealizedVolatility30(self, plot=True):

        df = self.getIVandRVData(indicator_exp='30')

        today_not_converted = pd.Timestamp.today()
        today = today_not_converted.tz_localize('UTC')
        
        df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize('UTC')

        first_df = df[df['datetime'] >= today - pd.Timedelta(days=50)]
        second_df = df[~df['datetime'].isin(first_df['datetime'])]
        
        if not first_df.empty: 
            for i, date_listed in enumerate(first_df['datetime']):
                day_30_date = date_listed - pd.Timedelta(days=30)

                if date_listed.date() != datetime.now().astimezone(pytz.timezone(UTC)):
                    new_date = date_listed + pd.Timedelta(days=1)

                    data = yf.download(
                        self.st_ticker, 
                        start=day_30_date.strftime('%Y-%m-%d'), 
                        end=new_date.strftime('%Y-%m-%d'),  
                        interval='1h'
                    )

                else:

                    data = yf.download(
                        self.st_ticker, 
                        start=day_30_date.strftime('%Y-%m-%d'), 
                        end=date_listed.strftime('%Y-%m-%d'),  
                        interval='1h'
                    )


                data.index = pd.to_datetime(data.index)
                if data.index.tz is None:
                    data.index = data.index.tz_localize('UTC').tz_convert(UTC)
                else:
                    data.index = data.index.tz_convert(UTC)

                target_time = pd.Timestamp.combine(
                    date_listed.date(), 
                    pd.to_datetime(date_listed).time()
                ).tz_localize(UTC)

                closest_hour = data.index[abs(data.index - target_time).argmin()]
                data = data.loc[data.index <= closest_hour]

                data['returns'] = np.log(data['Close'] / data['Close'].shift(1))  
                realized_vol = np.sqrt(np.sum(data['returns']**2) / len(data))  
                annualized_vol = realized_vol * np.sqrt(252 * 6.5) 

                first_df.loc[first_df['datetime'] == date_listed, 'RV'] = annualized_vol

        if not second_df.empty: 
            for i, date_listed in enumerate(second_df['datetime']):
                day_30_date = date_listed - pd.Timedelta(days=30)

                data = yf.download(
                    self.st_ticker, 
                    start=day_30_date.strftime('%Y-%m-%d'), 
                    end=date_listed.strftime('%Y-%m-%d'),  
                    interval='1d'
                )

                data.index = pd.to_datetime(data.index)
                if data.index.tz is None:
                    data.index = data.index.tz_localize('UTC').tz_convert(UTC)
                else:
                    data.index = data.index.tz_convert(UTC)


                data['returns'] = np.log(data['Close'] / data['Close'].shift(1))  
                realized_vol = np.sqrt(np.sum(data['returns']**2) / len(data))  
                annualized_vol = realized_vol * np.sqrt(252) 

                second_df.loc[second_df['datetime'] == date_listed, 'RV'] = annualized_vol

        if not first_df.empty or second_df.empty:
            merged_df = pd.concat([first_df, second_df], ignore_index=True)
            merged_df = merged_df.sort_values(by='datetime')
            merged_df = merged_df.reset_index(drop=True)
            merged_df = merged_df.reset_index()

            if plot:
                class_ = ImpliedVolatilityPlot()
                fig = class_.plotIVandIVR(merged_df, '30')
                return fig
        

        return merged_df  
    

################################################################################
###  Delta Skew Asymmetry Indicator
################################################################################

class IVDeltaSkewAsymmetry:
    def __init__(self, selected_option, selected_date, selected_hour, max_history, info=None, ticker=None, show_day=True):
        pass
        self.selected_option = selected_option
        self.selected_date = selected_date
        self.selected_hour = selected_hour
        self.max_history = max_history
        self.show_day = show_day
        self.info = info
        self.ticker = info['underlying_ticker'] 

        self.class_LoadingData = LoadingData()
        self.class_ConvertData = ConvertData()
        self.class_IVAtmAndRealizedVolatility = IVAtmAndRealizedVolatility(
            selected_option=self.selected_option,
            selected_date=self.selected_date,
            selected_hour=self.selected_hour,
            max_history=self.max_history,
            info=self.info,
        )


    def interpolateIVdeltaSkew(self, df, target_dte=30, delta_targeted=0.25, option_type='call'):
                
        if df.empty or 'dte' not in df.columns:
            return np.nan

        if option_type=='put':
            df['delta'] = df['delta'].abs()

        df = df.sort_values('dte')

        def find_closest_delta(group, delta_targeted):
            idx_min = (group['delta'] - delta_targeted).abs().idxmin()
            return group.loc[idx_min]

        df_delta = df.groupby('dte').apply(find_closest_delta, delta_targeted=delta_targeted).reset_index(drop=True)

        exp_test = df_delta[df_delta['dte'] == target_dte]

        if not exp_test.empty:
            iv_target = exp_test.iloc[0]['implied_volatility']
            return iv_target, 30, 30
        
        df_below = df_delta[df_delta['dte'] <= target_dte].tail(1)
        df_above = df_delta[df_delta['dte'] >= target_dte].head(1)

        df_below = df_below[df_below['dte'] <= target_dte].tail(1)
        df_above = df_above[df_above['dte'] >= target_dte].head(1)

        if not df_below.empty and not df_above.empty:
            
            dte_1, iv_1 = df_below.iloc[0]['dte'], df_below.iloc[0]['implied_volatility']
            dte_2, iv_2 = df_above.iloc[0]['dte'], df_above.iloc[0]['implied_volatility']
            iv_target = iv_1 + (target_dte - dte_1) * (iv_2 - iv_1) / (dte_2 - dte_1)

        elif not df_below.empty:
            
            iv_target = df_below.iloc[0]['implied_volatility']
        elif not df_above.empty:
            
            iv_target = df_above.iloc[0]['implied_volatility']
        else: 
    
            iv_target, dte_1, dte_2  = np.nan, np.nan, np.nan
        
        return iv_target, dte_1, dte_2
    

    def filterOptions(self, df, option_type):
            
        df_filtered = df[df['option_type'] == option_type].copy()

        return df_filtered
    
    def getIvATM(self, df, get_st, indicator_exp):

        mean_iv = np.nan

        df_call = self.class_IVAtmAndRealizedVolatility.filterOptionsAtm(df, 'call', get_st)
        df_put = self.class_IVAtmAndRealizedVolatility.filterOptionsAtm(df, 'put', get_st)

        if indicator_exp == '30':
            
            call_value, dte_1, dte_2= self.class_IVAtmAndRealizedVolatility.interpolateIvATM(df_call, 30)
            put_value, useless1, useless2 = self.class_IVAtmAndRealizedVolatility.interpolateIvATM(df_put, 30)

            mean_iv = (call_value + put_value) / 2
        
        return mean_iv

    def getDeltaSkewOptions(self, indicator_exp='30', delta_targeted= 0.25, skew_type='classic', plot=True):
        
        iv_dict = {}

        list_available_dates = self.class_IVAtmAndRealizedVolatility.loadHistory()
        available_data = self.class_IVAtmAndRealizedVolatility.getAvailableDate(list_available_dates)

        for key, item in available_data.items():
         
            for index, element in enumerate(item):

                if element == 'close':  
                    item[index] = CBOE_CLOSE_UTC 

                df = LoadingData().get_data_csv(self.selected_option, key, item[index])
                df['underlying_price'] = pd.to_numeric(df['underlying_price'], errors='coerce')
                get_st = df.iloc[0]['underlying_price']

                df['expiration'] = pd.to_datetime(df['expiration'])
                key_date = pd.to_datetime(key)

                df_call = self.filterOptions(df, 'call')
                df_put = self.filterOptions(df, 'put')

                df_call['implied_volatility'] = pd.to_numeric(df_call['implied_volatility'], errors='coerce')
                df_put['implied_volatility'] = pd.to_numeric(df_put['implied_volatility'], errors='coerce')

                if indicator_exp == '30':
                    
                    call_value, dte_1, dte_2= self.interpolateIVdeltaSkew(df_call, target_dte=30, delta_targeted=delta_targeted, option_type='call')
                    put_value, useless1, useless2 = self.interpolateIVdeltaSkew(df_put, target_dte=30, delta_targeted=delta_targeted, option_type='put')

                if skew_type == 'classic':
                    iv_skew = (call_value - put_value)
                elif skew_type == 'butterfly':

                    iv_atm = self.getIvATM(df, get_st, indicator_exp)
                    iv_skew = ((call_value + put_value) / 2) * iv_atm

                date_time_str = f"{key} {item[index]}"
                date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H_%M")

                new_key = date_time_obj.strftime("%Y-%m-%d-%H-%M")

                if new_key not in iv_dict:
                    iv_dict[new_key] = [float(iv_skew), call_value, put_value, dte_1, dte_2]

        final_df = pd.DataFrame.from_dict(iv_dict, orient='index', columns=['iv_skew', 'call_iv', 'put_iv', 'dte_1', 'dte_2'])
        final_df.reset_index(inplace=True)  
        final_df.rename(columns={'index': 'datetime'}, inplace=True)

        final_df['iv_skew'] = final_df['iv_skew'] *100
        final_df['call_iv'] = final_df['call_iv'] *100
        final_df['put_iv'] = final_df['put_iv'] *100

        final_df['datetime'] = pd.to_datetime(final_df['datetime'], format="%Y-%m-%d-%H-%M")
        final_df = final_df.sort_values(by='datetime')

        if plot:
            class_ = ImpliedVolatilityPlot()
            fig = class_.plotDeltaSkew25(final_df, skew_type, indicator_exp, delta_targeted)

            return fig

        return final_df


################################################################################
###  IV Surface
################################################################################

class ImpliedVolatilitySurface:
    def __init__(self, selected_date, info):
        pass

    def surfaceCalculation(self, df, custom_df, strike_dw, strike_up, selected_type, option_type, selected_exp, plot=True):

        col = 'expiration'
        
        if selected_exp:
            df['expiration'] = df['expiration'].astype(int)
            selected_exp = int(selected_exp)
        
        filtered_df = df[['strike', 'implied_volatility', col, 'option_type']]

        if option_type == 'call':
            filtered_df = filtered_df[filtered_df['option_type'] == 'call']
        elif option_type == 'put':
            filtered_df = filtered_df[filtered_df['option_type'] == 'put']
        elif option_type == 'mean':
            filtered_df['implied_volatility'] = filtered_df.groupby(['strike', col])['implied_volatility'].transform('mean')
        else:
            filtered_df = filtered_df[filtered_df['option_type'] == 'call']

        filtered_df = filtered_df[(strike_dw < filtered_df['strike']) & (strike_up > filtered_df['strike'])]

        if selected_type and 'Peak' in selected_type and selected_exp is not None:
            filtered_df = filtered_df[filtered_df[col] <= selected_exp]
        
        if selected_type and 'ItemChosen' in selected_type and not custom_df.empty:
            filtered_df = filtered_df[filtered_df['contract_symbol'] == custom_df['contract_symbol']]

      
        if plot:
            fig = ImpliedVolatilityPlot().surface_iv(filtered_df, col)
            return fig
        
        return filtered_df
    
################################################################################
###  PLOT
################################################################################

class ImpliedVolatilityPlot:
    def __init__(self):
        self.min_points = 3 

    def plotIVandIVR(self, df, type_iv):
        print(df)
        if type_iv == '30':
            main_title = "ATM IV (30 days) vs RV (30 days) to Imported Date"
            name_rv = f"RV (30 days)"
            name_atm_average = f"ATM IV average (30 days expiration)" 
            name_atm_call = f"ATM Call IV (30 days expiration)"
            name_atm_put = f"ATM Put IV (30 days expiration)" 
            df['dte_1'] = 30 

        elif type_iv == 'closest':
            main_title = "ATM IV vs RV to Imported Date (Nearest expirations)"
            name_rv = 'RV (by nearest expiration)'
            name_atm_average = f"ATM IV nearest expiration"
            name_atm_call = f"ATM Call IV (by nearest expiration)"
            name_atm_put = f"ATM Put IV (by nearest expiration)"  
            
            


        fig = go.Figure()

        x_max = df['datetime'].max()
        x_min = df['datetime'].min()

        y_max = max(
            (df['RV'] * 100).max(), 
            (df['mean_iv'] * 100).max(),
            (df['call_iv'] * 100).max(),
            (df['put_iv'] * 100).max(),
            ) * 2
        
        y_max_range = max(
            (df['RV'] * 100).max(), 
            (df['mean_iv'] * 100).max(),
            (df['call_iv'] * 100).max(),
            (df['put_iv'] * 100).max(),
            ) * 1.2
        
        y_min_range = min(
            (df['RV'] * 100).min(), 
            (df['mean_iv'] * 100).min(),
            (df['call_iv'] * 100).min(),
            (df['put_iv'] * 100).min(),
            ) * 0.8

        #Plot RV
        fig.add_trace(
            go.Scatter(
                    x=df['datetime'], 
                    y=df['RV'] * 100,  
                    mode='lines+markers',  
                    name=name_rv,
                    line=dict(width=2, shape='spline'), 
                    text=df['dte_1'],
                    hoverinfo='skip',  
                    hovertemplate=(
                        '<b>Date:</b> %{x}<br>'  
                        '<b>RV:</b> %{y:.2f}%<br>'  
                        '<b>DTE:</b> %{text} days<br>'  
                        '<extra></extra>'  
                    ),
                    
                )
        )

        fig.add_trace(
            go.Scatter(
                    x=df['datetime'], 
                    y=df['mean_iv'] * 100,  
                    mode='lines+markers',  
                    line=dict(color="#8e44ad", width=2, dash="dash", shape='spline'),  
                    name=name_atm_average, 
                    text=df['dte_1'],
                    hoverinfo='skip',  
                    hovertemplate=(
                        '<b>Date:</b> %{x}<br>'  
                        '<b>ATM IV (avg):</b> %{y:.2f}%<br>' 
                        '<b>DTE:</b> %{text} days<br>'  
                        '<extra></extra>'  
                    ),
                    
                )
        )

        fig.add_trace(
            go.Scatter(
                    x=df['datetime'], 
                    y=df['call_iv'] * 100,  
                    mode='lines+markers',  
                    line=dict(color="#58d68d", width=1, dash="solid", shape='spline'), 
                    name=name_atm_call,
                    hoverinfo='skip',  
                    hovertemplate=(
                        '<b>Date:</b> %{x}<br>'  
                        '<b>ATM Call IV:</b> %{y:.2f}%<br>'  
                        '<b>DTE:</b> %{text} days<br>'  
                        '<extra></extra>'  
                    ),
                )
        )

        fig.add_trace(
            go.Scatter(
                    x=df['datetime'], 
                    y=df['put_iv'] * 100,  
                    mode='lines+markers',  
                    line=dict(color="#e74c3c", width=1, dash="solid", shape='spline'),  
                    name=name_atm_put,
                    text=df['dte_1'],
                    hoverinfo='skip',  
                    hovertemplate=(
                        '<b>Date:</b> %{x}<br>'  
                        '<b>ATM Put IV:</b> %{y:.2f}%<br>' 
                        '<b>DTE:</b> %{text} days<br>'  
                        '<extra></extra>'  
                    ),
                )
        )

        fig.update_layout(
            title=main_title,
            xaxis_title='Imported Dates',
            yaxis_title='IV & RV (% annualized)',
            legend_title="Expirations",
            template="plotly_white",
            xaxis=dict(
                fixedrange=False,
                range=[x_min, x_max],   
                autorange=True,
                maxallowed=x_max,    
                minallowed=x_min,
            ),
            yaxis=dict(
                side="left",
                range=[y_min_range, y_max_range],
                showgrid=False,
                gridcolor='lightgrey',
                fixedrange=False,    
                autorange=False,
                maxallowed=y_max,    
                minallowed=0,
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5
            ),
            modebar_add=[
                "v1hovermode",
                "toggleSpikelines",
            ],
        )

        return fig


    def plotDeltaSkew25(self, df, skew_type, indicator_exp, delta_targeted):
        print(df)

        if skew_type == 'classic':
            title_name = f'{round(delta_targeted * 100)} Risk Reversal Volatility {indicator_exp} days'
            y_name = f'{round(delta_targeted * 100)} Delta Skew (RR (%))'
            indicator_name = f'{round(delta_targeted * 100)} RR indicator'

        elif skew_type == 'butterfly':
            title_name = f'{round(delta_targeted * 100)} Butterfly Volatiliy (BF) {indicator_exp} days'
            y_name = f'{round(delta_targeted * 100)} Delta Skew (Butterfly (%))'
            indicator_name = f'{round(delta_targeted * 100)} BF indicator'

        x_max = df['datetime'].max()
        x_min = df['datetime'].min()

        fig = go.Figure()

        fig.add_trace(
                go.Scatter(
                    x=df['datetime'],  
                    y=df['call_iv'],       
                    mode='lines+markers',       
                    name=f'{round(delta_targeted * 100)} Call IV',    
                    line=dict(color="#58d68d", width=2, dash="dash", shape='spline'),          
                    marker=dict(size=8),
                    hovertemplate='%{x}<br>IV: %{y:.2f}%'         
                )
            )
        
        fig.add_trace(
                go.Scatter(
                    x=df['datetime'],  
                    y=df['put_iv'],       
                    mode='lines+markers',       
                    name=f'{round(delta_targeted * 100)} Put IV',    
                    line=dict(color="#e74c3c", width=2, dash="dash", shape='spline'),          
                    marker=dict(size=8)         
                )
            )

        fig.add_trace(
                go.Scatter(
                    x=df['datetime'],  
                    y=df['iv_skew'],       
                    mode='lines+markers',       
                    name=indicator_name,    
                    line=dict(width=3, color='#44c4ff', dash="solid", shape='spline'),          
                    marker=dict(size=8)         
                )
            )

        fig.update_layout(
            title=title_name,
            xaxis_title='Imported Dates',
            yaxis_title=y_name,
            hovermode='x unified',
            dragmode=False,
            template='plotly_white',
            xaxis=dict(
                fixedrange=False,
                range=[x_min, x_max],   
                autorange=False,
                maxallowed=x_max,    
                minallowed=x_min,
            ),
            yaxis=dict(
                side="left",
                showgrid=False,
                gridcolor='lightgrey',
                fixedrange=False,    
                autorange=True,
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5,
            ),
            modebar_add=[
                "v1hovermode",
                "toggleSpikelines",
            ],
        )

        fig.update_traces(
            hovertemplate="Imported Date: %{x}<br>Skew 25: %{y:.2f}<br>"
        )

        return fig


    def smooth_series(self, x, y, method='interpolate'):
   
        if len(x) == 0 or len(y) == 0:
            return None, None

        mask = y >= 0
        x_valid = x[mask]
        y_valid = y[mask]

        if len(x_valid) < self.min_points:
            return x_valid, y_valid
            
        try:
            if method == 'interpolate':
                f = PchipInterpolator(x_valid, y_valid, extrapolate=False)
                x_smooth = np.linspace(x_valid.min(), x_valid.max(), 100)
                y_smooth = f(x_smooth)

                y_smooth = np.clip(y_smooth, 0, None)

                return x_smooth, y_smooth
            
            elif method == 'savgol':

                mask = y > 0
                x_valid = x[mask]
                y_valid = y[mask]

                if len(y_valid) >= 3:  
                    window_length = min(5, len(y_valid) if len(y_valid) % 2 == 1 else len(y_valid)-1)
                    y_smooth = savgol_filter(y_valid, window_length, polyorder=2)
                    return x_valid, y_smooth
                else:
                    return x_valid, y_valid
        except:
            
            return x_valid, y_valid


    def smileByStrike(self, df_pivot, col, show_day=True, smooth_method=None, st_list=[], variation_dates=False, selected_date1=None, selected_date2=None):
    
        fig = go.Figure()
        
        expiries = sorted(df_pivot[col].unique())
        variations = sorted(df_pivot['dataframe_type'].unique())

        y_max = max(
            df_pivot['call'].max() if (df_pivot['call'] > 0).any() else 0,
            df_pivot['put'].max() if (df_pivot['put'] > 0).any() else 0
        ) * 1.1


        valid_strikes = df_pivot.loc[(df_pivot['call'] > 0) | (df_pivot['put'] > 0), 'strike']

        if not valid_strikes.empty:
            x_min = max(0, valid_strikes.min()) 
            x_max = valid_strikes.max()
        else:
            x_min, x_max = 0, 0

        for dataframe_type in variations:
            for i, expiry in enumerate(expiries):

                if dataframe_type == 'current':
                    intensity = int(135 * (1 - i / len(expiries)))  
                    put_color = f"rgb(255, {max(0, intensity)}, {max(0, intensity)})" 


                    G_intensity = int(175 + (157 - 48) * (i / len(expiries)))  
                    B_intensity = int(48 + (54 - 48) * (i / len(expiries)))    
                
                    call_color = f"rgb(0, {G_intensity}, {B_intensity})"

                else:

                    intensity = int(135 * (1 - i / len(expiries)))  
                    put_color = f"rgb(0, {95 + (119 - 95) * (i / len(expiries)):.0f}, {153 + (200 - 153) * (i / len(expiries)):.0f})"

                    R_intensity = int(0 + (136 - 0) * (i / len(expiries)))  
                    G_intensity = int(174 + (211 - 174) * (i / len(expiries)))  
                    B_intensity = int(239 + (240 - 239) * (i / len(expiries)))  

                    call_color = f"rgb({R_intensity}, {G_intensity}, {B_intensity})"

                if show_day:
                    
                    if variation_dates and selected_date1 and 'current' in dataframe_type:
                        plot_expiry = f'{expiry} days ({selected_date1})'

                    elif variation_dates and selected_date2 and 'compare' in dataframe_type:
                        plot_expiry = f'{expiry} days ({selected_date2})'
                    else:
                        plot_expiry = f'{expiry} days'

                else: 
                    if variation_dates and selected_date1 and 'current' in dataframe_type:
                        plot_expiry = f'{expiry} days ({selected_date1})'
                        
                    elif variation_dates and selected_date2 and 'compare' in dataframe_type:
                        plot_expiry = f'{expiry} days ({selected_date2})'
                    else:
                        plot_expiry = f'{expiry}'

                df = df_pivot[(df_pivot[col] == expiry) & (df_pivot['dataframe_type'] == dataframe_type)]
                
                if (df['call'] > 0).any():  
                    x = df['strike'].values
                    y = df['call'].values

                    if 'interpolate' in smooth_method or 'savgol' in smooth_method:
                        x_smooth, y_smooth = self.smooth_series(x, y, smooth_method)
                    
                    else:
                        x_smooth = x
                        y_smooth = y

                    if x_smooth is not None and y_smooth is not None and len(x_smooth) > 0:
                
                        fig.add_trace(
                            go.Scatter(
                                x=x_smooth,
                                y=y_smooth,
                                name=f'Call | {plot_expiry}',
                                mode='lines',
                                line=dict(color=call_color, dash='solid'),
                            )
                        )
                    
                
                if (df['put'] > 0).any():  
                    x = df['strike'].values
                    y = df['put'].values
                
                    if 'interpolate' in smooth_method or 'savgol' in smooth_method:
                        x_smooth, y_smooth = self.smooth_series(x, y, smooth_method)
                    
                    else:
                        x_smooth = x
                        y_smooth = y
                    
                    if x_smooth is not None and y_smooth is not None and len(x_smooth) > 0:
        
                        fig.add_trace(
                            go.Scatter(
                                x=x_smooth,
                                y=y_smooth,
                                name=f'Put | {plot_expiry}',
                                mode='lines',
                                line=dict(color=put_color, dash='solid'),
                            )
                        )

        int_st = 1

        for st_price in st_list:

            if int_st == 1:
                st_trace = f'{st_price:,.2f} (Last Value)'

                fig.add_trace(
                go.Scatter(
                    x=[st_price, st_price],  
                    y=[0, y_max], 
                    mode="lines",  
                    line=dict(color="#8e44ad", width=2, dash="solid"),  
                    name=st_trace,  
                    showlegend=True  
                )
            )
                
                int_st += 1
                continue

            elif int_st == 2:
                st_trace = f'{st_price:,.2f} (data)'
                color='#0fab2e'
            elif int_st ==3:
                st_trace = f'{st_price:,.2f} (compare)'
                color='#66caff'

            fig.add_trace(
                go.Scatter(
                    x=[st_price, st_price],  
                    y=[0, y_max], 
                    mode="lines",  
                    line=dict(color=color, width=1, dash="dash"),  
                    name=st_trace,  
                    showlegend=True  
                )
            )
            
            int_st += 1
            

        fig.update_layout(
            title='Volatility Smile by Strike & Expiration',
            xaxis_title='Strike',
            yaxis_title='Implied Volatility (%)',
            hovermode='x unified',
            dragmode=False,
            template='plotly_white',
            xaxis=dict(
                fixedrange=False,
                range=[x_min, x_max],   
                autorange=True,
                maxallowed=x_max,    
                minallowed=x_min,
            ),
            yaxis=dict(
                side="left",
                range=[0, y_max],
                showgrid=False,
                gridcolor='lightgrey',
                fixedrange=False,    
                autorange=False,
                maxallowed=y_max,    
                minallowed=0,
            ),
            legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=-0.2,
                    xanchor='center',
                    x=0.5
                ),
            modebar_add=[
                "v1hovermode",
                "toggleSpikelines",
            ],
        )
        
        fig.update_traces(
            hovertemplate="Strike: %{x}<br>IV: %{y:.2f}%<br>"
        )
        
        return fig
    
    def surface_iv(self, df, expiration_col):
        
        required_columns = {'strike', 'implied_volatility', expiration_col}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Le DataFrame doit contenir les colonnes suivantes : {required_columns}")
        
        grid_x, grid_y = np.meshgrid(
            np.linspace(df['strike'].min(), df['strike'].max(), 50),  
            np.linspace(df[expiration_col].min(), df[expiration_col].max(), 50) 
        )

        grid_z = griddata(
            points=(df['strike'], df[expiration_col]),  
            values=df['implied_volatility'],  
            xi=(grid_x, grid_y),  
            method='linear'  
        )

        fig = go.Figure()

        fig.add_trace(
            go.Surface(
                x=grid_x,
                y=grid_y,
                z=grid_z,
                colorscale='Viridis',
                opacity=0.9,
                colorbar=dict(title='Volatility') 
            )
        )

        fig.update_layout(
            scene=dict(
                xaxis_title='Strike',
                yaxis_title='Expiration (days)',
                zaxis_title='Implied Volatility',
            ),
            title='Implied Volatility Surface',
            template='plotly_white'
        )

        return fig
        
