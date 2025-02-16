import re

from datetime import datetime

import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

from src.import_data.utils import LoadingData

class MetricsUtils:

    def __init__(self):

        pass

    def getStInfo(self, info_data):

        st_ticker = info_data['underlying_ticker']
        change = info_data['change']
        quotation_type= info_data['quotation_type']
        quotation_type_value= info_data['quotation_type_value']
        lot_size = info_data['lot_size']

        return st_ticker, change, quotation_type, quotation_type_value, lot_size

    def getStPrice(self, st_ticker):
        
        try:
            st_data = yf.download(st_ticker, period='1d', interval='1m')
            st_price = float(round(st_data['Close'].iloc[-1], 2))

        except:
            print(f"Error: can't reach {st_ticker}")
            return 0

        return st_price


################################################################################
###  OI Volumes by Exp
################################################################################ 

class VolumesExpirations:
    def __init__(self, show_day):

        self.show_day = show_day

    def getVolumeByExpiration(self, df, vol_type, option_type, plot=True):
        if self.show_day:
            col = 'expiration'
        else:
            col = 'expiration_bis'

        df['adj_volume'] = df['open_interest'] + df['volume']

        df_base = df.groupby([col, 'option_type'], as_index=False).agg({
            'volume': 'sum',
            'open_interest': 'sum',
            'adj_volume': 'sum'
        })

        df_all = df.groupby(col, as_index=False).agg({
            'volume': 'sum',
            'open_interest': 'sum',
            'adj_volume': 'sum'
        })
        df_all['option_type'] = 'All'  

        df_final = pd.concat([df_base, df_all], ignore_index=True)

        df_pivot = pd.pivot_table(
            data=df_final,
            index=col,
            values=['volume', 'open_interest', 'adj_volume'],
            columns=['option_type'],
            aggfunc='sum'
        )

        df_plot = df_pivot.reset_index()

        if plot:
            fig = PlotMetrics().plot_volumesByExpiration(df_plot, vol_type, option_type, col, self.show_day)
            return fig
        
        return df_pivot

################################################################################
###  OI Variations
################################################################################ 

class VariationsOI:

    def __init__(self, info_data, df1, df2, date1, date2, selected_hour1, selected_hour2, show_day):

        self.df1 = df1
        self.df2 = df2
        self.date1 = date1
        self.date2 = date2
        self.show_day = show_day
        self.info_data = info_data

        underlying_ticker = info_data['underlying_ticker']

        self.st_date1 = LoadingData().get_st_price_hour(None, date1, selected_hour1, underlying_ticker)
        self.st_date2 = LoadingData().get_st_price_hour(None, date1, selected_hour2, underlying_ticker)
    
    def get_closest_date(self, expiration_value):
 
            filtered_df = self.df1[self.df1['expiration'] == expiration_value]
            
            if not filtered_df.empty:
            
                date_max = filtered_df['expiration_bis'].iloc[0]  
                return date_max
            
    def statVariation(self, df, st_price1, st_price2):
                
        variations = pd.to_numeric(df['variations'], errors='coerce').values
        
        valid_mask = ~np.isinf(variations) & ~np.isnan(variations)
        
        clean_variations = variations[valid_mask]
        clean_strikes = df['strike'].values[valid_mask]
        
        max_var_idx = np.argmax(clean_variations)
        min_var_idx = np.argmin(clean_variations)
        
        stats = {
            "max_var": clean_variations[max_var_idx],
            "max_var_strike": clean_strikes[max_var_idx],
            "min_var": clean_variations[min_var_idx],
            "min_var_strike": clean_strikes[min_var_idx],
            "mean": np.mean(clean_variations),
            "median": np.median(clean_variations),
            "std": np.std(clean_variations),
            "st_var": (st_price1 - st_price2) / st_price1 if st_price1 != 0 else float('inf')
        }
        
        return stats

    def variation(self, strike_dw_factor, strike_up_factor, option_type, plot=True, type="All", vol_type='volAndOI', exp_selected=None):

        if option_type not in ['call', 'put']:
            option_type = 'call'
        
        df1 = self.df1[self.df1['option_type'] == option_type].copy()
        df2 = self.df2[self.df2['option_type'] == option_type].copy()
   
        df2 = df2[df2['contract_symbol'].isin(df1['contract_symbol'])]
        df1 = df1[df1['contract_symbol'].isin(df2['contract_symbol'])]

        if exp_selected and type == "Specific":

            if self.show_day:
                exp_selected = [int(exp) for exp in exp_selected]

                filtered_df_exp = df1[df1['expiration'].isin(exp_selected)]

                convert_expected_list = filtered_df_exp['expiration_bis'].unique()
                convert_expected_list = list(convert_expected_list)

                exp_selected = [pd.to_datetime(exp) for exp in convert_expected_list]
                
            else:
                exp_selected = [pd.to_datetime(exp) for exp in exp_selected]

            df1['expiration_bis'] = pd.to_datetime(df1['expiration_bis'])
            df2['expiration_bis'] = pd.to_datetime(df2['expiration_bis'])

            df1 = df1[df1['expiration_bis'].isin(exp_selected)]
            df2 = df2[df2['expiration_bis'].isin(exp_selected)]

        if exp_selected and type == "Peak":

            if self.show_day:
                exp_selected = int(exp_selected)

                filtered_value = df1.loc[df1['expiration'] == exp_selected, 'expiration_bis'].values[0]

                exp_selected = pd.to_datetime(filtered_value) 
                
            else:
                exp_selected = pd.to_datetime(exp_selected)

            df1['expiration_bis'] = pd.to_datetime(df1['expiration_bis'])
            df2['expiration_bis'] = pd.to_datetime(df2['expiration_bis'])

            df1 = df1[df1['expiration_bis'] <= exp_selected]
            df2 = df2[df2['expiration_bis'] <= exp_selected]


        df1 = df1[(strike_dw_factor < df1['strike']) & (strike_up_factor > df1['strike'])]
        df2 = df2[(strike_dw_factor < df2['strike']) & (strike_up_factor > df2['strike'])]

        df_global = pd.DataFrame()
        df_global['strike'] = df1['strike']

        if isinstance(vol_type, str) and 'volume' in vol_type:
            df1['revised_volumes'] = df1['volume']
            df2['revised_volumes'] = df2['volume']

        elif isinstance(vol_type, str) and 'volAndOI' in vol_type:
            df1['revised_volumes'] = df1['volume'] + df1['open_interest']
            df2['revised_volumes'] = df2['volume'] + df2['open_interest']

        elif isinstance(vol_type, str) and 'oi' in vol_type:
            df1['revised_volumes'] = df1['open_interest']
            df2['revised_volumes'] = df2['volume']

        df1_sum = df1.pivot_table(index='strike', columns='option_type', values='revised_volumes', aggfunc='sum')
        df1_converted = df1_sum.reset_index()
        df1_converted['strike'] = df1_converted['strike']  

        df2_sum = df2.pivot_table(index='strike', columns='option_type', values='revised_volumes', aggfunc='sum')
        df2_converted = df2_sum.reset_index()
        df2_converted['strike'] = df2_converted['strike']  
        
        df_global = pd.merge(df1_converted, df2_converted, on='strike', how='outer', suffixes=('_df1', '_df2'))

        df_global.rename(columns={
            f'{option_type}_df1': f'df1_{option_type}',
            f'{option_type}_df2': f'df2_{option_type}'
        }, inplace=True)

        df_global['variations'] = ((df_global[f'df1_{option_type}'] - df_global[f'df2_{option_type}']) 
                                / df_global[f'df2_{option_type}'] * 100)
    
        df_global['variations'] = df_global['variations'].fillna(0)
        df_global = df_global.replace([float('inf'), -float('inf')], float('nan'))
        df_global = df_global.dropna()


        if plot:
            fig = PlotMetrics().plot_OIVariations(df_global, option_type, vol_type, self.date1, self.date2, self.st_date1, self.st_date2)
            listed = self.statVariation(df_global, self.st_date1, self.st_date2)
            return fig, listed
        
        return df_global

################################################################################
###  Metrics (Stats)
################################################################################ 

class MetricsOI:

    def __init__(self, df, info_data, show_day, selected_date, selected_hour):

        self.df = df
        self.show_day = show_day

        if not show_day:
            self.df['expiration'] = pd.to_datetime(df['expiration']).dt.date

        self.info_data = info_data

        self.st_ticker, self.change, self.quotation_type, self.quotation_type_value, self.lot_size = (
            MetricsUtils().getStInfo(self.info_data)
        )

        self.st_price = LoadingData().get_st_price_hour(None, selected_date, selected_hour, self.st_ticker)
     
        self.col_exp = 'expiration'

    def statVolume(self, df):
        """
        Calculates volume statistics for calls and puts
        """
  
        required_columns = ['call', 'put', 'strike']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "max_call": 0,
                "max_call_strike": 0,
                "min_call": 0,
                "min_call_strike": 0,
                "call_median": 0,
                "max_put": 0,
                "max_put_strike": 0,
                "min_put": 0,
                "min_put_strike": 0,
                "put_median": 0,
                "put_call_ratio": 0
            }

        try:
    
            max_call_idx = df['call'].idxmax() if not df['call'].empty else 0
            min_call_idx = df['call'].idxmin() if not df['call'].empty else 0
            
            call_stats = {
                'max_call': df['call'].max() if not df['call'].empty else 0,
                'max_call_strike': df.loc[max_call_idx, 'strike'] if max_call_idx != 0 else 0,
                'min_call': df['call'].min() if not df['call'].empty else 0,
                'min_call_strike': df.loc[min_call_idx, 'strike'] if min_call_idx != 0 else 0,
                'total_call': df['call'].sum() if not df['call'].empty else 0
            }

            max_put_idx = df['put'].idxmax() if not df['put'].empty else 0
            min_put_idx = df['put'].idxmin() if not df['put'].empty else 0
            
            put_stats = {
                'max_put': df['put'].max() if not df['put'].empty else 0,
                'max_put_strike': df.loc[max_put_idx, 'strike'] if max_put_idx != 0 else 0,
                'min_put': df['put'].min() if not df['put'].empty else 0,
                'min_put_strike': df.loc[min_put_idx, 'strike'] if min_put_idx != 0 else 0,
                'total_put': df['put'].sum() if not df['put'].empty else 0
            }

            if not df.empty:
                sorted_data = df.reset_index().sort_values('strike')
                
                if call_stats['total_call'] > 0:
                    call_cumsum = np.cumsum(sorted_data['call'].values)
                    call_median_idx = np.searchsorted(call_cumsum, call_stats['total_call'] / 2)
                    strikes = sorted_data['strike'].values
                    call_median = strikes[min(call_median_idx, len(strikes) - 1)]
                else:
                    call_median = 0

                if put_stats['total_put'] > 0:
                    put_cumsum = np.cumsum(sorted_data['put'].values)
                    put_median_idx = np.searchsorted(put_cumsum, put_stats['total_put'] / 2)
                    strikes = sorted_data['strike'].values
                    put_median = strikes[min(put_median_idx, len(strikes) - 1)]
                else:
                    put_median = 0
            else:
                call_median = put_median = 0

            put_call_ratio = (put_stats['total_put'] / call_stats['total_call'] 
                            if call_stats['total_call'] != 0 else float('inf'))

            return {
                "max_call": call_stats['max_call'],
                "max_call_strike": call_stats['max_call_strike'],
                "min_call": call_stats['min_call'],
                "min_call_strike": call_stats['min_call_strike'],
                "call_median": call_median,
                "max_put": put_stats['max_put'],
                "max_put_strike": put_stats['max_put_strike'],
                "min_put": put_stats['min_put'],
                "min_put_strike": put_stats['min_put_strike'],
                "put_median": put_median,
                "put_call_ratio": put_call_ratio
            }

        except Exception as e:
       
            return {
                "max_call": 0,
                "max_call_strike": 0,
                "min_call": 0,
                "min_call_strike": 0,
                "call_median": 0,
                "max_put": 0,
                "max_put_strike": 0,
                "min_put": 0,
                "min_put_strike": 0,
                "put_median": 0,
                "put_call_ratio": 0
            }


    def OIByVolumeAndStrike(self, strike_dw_factor, strike_up_factor, plot=True, type="All", vol_type='volAndOI', exp_selected=None):

        expiration = None

        if self.show_day:
            col = 'expiration'
        else:
            col = 'expiration_bis'


        df_filtered = self.df[(strike_dw_factor < self.df['strike']) & (strike_up_factor > self.df['strike'])]


        if type == "All" or type == "ItemChosen":
            pass

        elif exp_selected and type == "Peak":
    
            if self.show_day:
                exp_selected = int(exp_selected) 
                
            else:
                exp_selected = pd.to_datetime(exp_selected)
                self.df[col] = pd.to_datetime(self.df[col])
            
            df_filtered = self.df[self.df[col] <= exp_selected].copy()

        elif exp_selected and type == "Specific":
            
            if self.show_day:
                exp_selected = [int(exp) for exp in exp_selected]
                
            else:
                exp_selected = [pd.to_datetime(exp) for exp in exp_selected]
                self.df[col] = pd.to_datetime(self.df[col])

            df_filtered = self.df[self.df[col].isin(exp_selected)].copy()

        if isinstance(vol_type, str) and 'volume' in vol_type:
            df_filtered['revised_volumes'] = df_filtered['volume']

        elif isinstance(vol_type, str) and 'volAndOI' in vol_type:
            df_filtered['revised_volumes'] = df_filtered['volume'] + df_filtered['open_interest']

        elif isinstance(vol_type, str) and 'oi' in vol_type:
            df_filtered['revised_volumes'] = df_filtered['open_interest']

        
        df = df_filtered[['revised_volumes', 'strike', 'option_type']].copy()
        df_sum = df.pivot_table(index='strike', columns='option_type', values='revised_volumes', aggfunc='sum')
        
        listed_dict = self.statVolume(df_sum)

        if plot:
            fig = PlotMetrics().plot_OIByVolumeAndStrike(df_sum, self.st_price, vol_type)
            return fig, listed_dict
            
        return df_sum
    
################################################################################
###  PLOT
################################################################################

class PlotMetrics:

    def __init__(self):
        pass


    def plot_volumesByExpiration(self, df, vol_type, option_type, col, show_day):

        fig = go.Figure()
    
        if col == 'expiration_bis':

            df[(col, '')] = pd.to_datetime(df[(col, '')])
            
        df = df.sort_values(by=(col, ''))

        x_axis_label = 'Expirations in Days' if show_day else 'Expirations'

        vol_type_map = {
            'volume': ('volume', 'Traded Volume'),
            'oi': ('open_interest', 'Open Interest'),
            'volAndOI': ('adj_volume', 'Volume & Open Interest')
        }

        if vol_type not in vol_type_map:
            raise ValueError("Invalid vol_type. Choose from ['volume', 'oi', 'volAndOI']")

        col_vol_type, vol_label = vol_type_map[vol_type]

        call_color = '#00AEEF'  
        put_color = '#0077C8' 
        combined_color = '#005F99'  

        if option_type == 'All':
            max_y = df[(col_vol_type, 'All')].max()
            fig.add_trace(
                go.Bar(
                    x=df[(col, '')],
                    y=df[(col_vol_type, 'All')],
                    name=f'Total {vol_label}',
                    marker=dict(color=combined_color, opacity=0.7)
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=df[(col, '')],
                    y=df[(col_vol_type, 'call')],
                    mode='lines+markers',
                    name=f'Call {vol_label}',
                    line=dict(color=call_color, width=2),
                    marker=dict(symbol='circle', size=6)
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=df[(col, '')],
                    y=df[(col_vol_type, 'put')],
                    mode='lines+markers',
                    name=f'Put {vol_label}',
                    line=dict(color=put_color, width=2, dash='dash'),
                    marker=dict(symbol='square', size=6)
                )
            )

        elif option_type == 'call' or option_type == 'put':

            max_y = df[(col_vol_type, option_type)].max(skipna=True)

            fig.add_trace(
                go.Bar(
                    x=df[(col, '')],
                    y=df[(col_vol_type, option_type)],
                    name=f'{option_type.capitalize()} {vol_label}',
                    marker=dict(color=call_color if option_type == 'call' else put_color)
                )
            )

        max_expiration = df[(col, '')].max()
        min_expiration = df[(col, '')].min()

        if col == 'expiration':
            median_date = df[(col, '')].median()
            max_expiration_range = df[df[(col, '')] <= median_date].max()
        else:
            median_date = df[(col, '')].median()
            max_expiration_range = df[df[(col, '')] <= median_date].max()

        fig.update_layout(
            title=f"{vol_label} by Expiration",
            xaxis_title=x_axis_label,
            yaxis_title=vol_label,
            legend_title="Option Type",
            template="plotly_white",
            dragmode=False,
            xaxis=dict(
                range=[min_expiration, max_expiration_range],
                showgrid=False,
                fixedrange=False,
                minallowed=-2,
                maxallowed=max_expiration 
            ),
            yaxis=dict(
                side="left",
                zeroline=True,
                zerolinewidth=1,
                zerolinecolor="black",
                showgrid=False,
                fixedrange=False,
                autorange=False,
                range=[0, max_y * 1.2],
                minallowed=0,
            ),
            modebar_add=["v1hovermode", "toggleSpikelines"]
        )

        return fig


    def plot_emptyVariations(self):
        fig = go.Figure()

        fig.add_annotation(
            text=(),
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=18, color="darkgray", family="Arial"),
            xref="paper",
            yref="paper",
            align="center",
            bordercolor="lightgray",
            borderwidth=1,
            borderpad=10,
            bgcolor="white",
            opacity=0.95,
        )

        fig.update_layout(
            xaxis=dict(
                visible=False,
                showline=False,
                zeroline=False,
                showgrid=False,
                fixedrange=True
            ),
            yaxis=dict(
                visible=False,
                showline=False,
                zeroline=False,
                showgrid=False,
                fixedrange=True
            ),
            title=dict(
                text="<b>No Data Available</b>",
                font=dict(size=20, color="black", family="Arial"),
                x=0.5,
                xanchor="center",
            ),
            template="plotly_white",
            plot_bgcolor="rgba(245, 245, 245, 1)",  
            margin=dict(l=50, r=50, t=70, b=50),  
        )

        fig.add_shape(
            type="rect",
            x0=0,
            y0=0,
            x1=1,
            y1=1,
            xref="paper",
            yref="paper",
            line=dict(color="lightgray", width=1),
        )

        return fig

    def plot_OIVariations(self, df, type, vol_type, date1, date2, st_date1, st_date2):

        if vol_type == 'volume':
            named_vol_type = 'Volumes'

        elif vol_type == 'oi':
            named_vol_type = 'OI'

        elif vol_type == 'volAndOI':
            named_vol_type = 'Volumes + OI'

        x_min = df['strike'].min()
        x_max = df['strike'].max()

        fig = go.Figure()

        color_call_1 = '#00aeff'
        color_call_2 = '#52ddff'

        if type == 'put':
            color = '#e74c3c'
            custom_title = f"Put ({date1} (initial) (1) vs {date2} (compare) (2)"
            named_type = 'Put'
        else:
            color = '#58d68d'  
            custom_title = f"Call ({date1} (initial) (1) vs {date2} (compare) (2)"
            named_type = 'Call'

        fig.add_trace(go.Bar(
            x=df['strike'],  
            y=df[f'df1_{type}'], 
            marker=dict(
                color=color_call_1,  
                opacity=0.75,  
                line=dict(
                    color=color_call_1, 
                    width=2
                )
            ),
            hovertemplate= named_type + ' ' + named_vol_type + ' variation: %{y:.2f} %<br>Strike: %{x}<extra></extra>',
            name=f"{named_vol_type} ({named_type} {date1})", 
        ))

        fig.add_trace(go.Bar(
            x=df['strike'],  
            y=df[f'df2_{type}'], 
            marker=dict(
                color=color_call_2,  
                opacity=0.5,  
                line=dict(
                    color=color_call_2, 
                    width=2  
                )
            ),
            hovertemplate='Put ' +  named_vol_type + ' ' + date2 + ': %{y:,.2f}<br>Strike: %{x}<extra></extra>',
            name=f"{named_vol_type} ({named_type} {date2})", 
        ))

        fig.add_trace(go.Bar(
            x=df['strike'],  
            y=df['variations'],  
            marker=dict(
                color=color,  
                opacity=1,  
                line=dict(
                    color=color,  
                    width=1 
                ),
            ),
            hovertemplate= named_type + ' ' + named_vol_type + ' variation: %{y:.2f} %<br>Strike: %{x}<extra></extra>',
            name=f"{named_vol_type} Variations ({named_type})",  
        ))

        y_min = df['variations'].min()
        y_max = df['variations'].max()
        margin = (y_max - y_min) * 0.1
        y_min_with_margin = y_min - margin
        y_max_with_margin = y_max + margin

        st_list = [st_date1, st_date2]
        int_label = 7
        int_st = 1

        for st_price in st_list:
            fig.add_shape(
                type="line",
                x0=st_price,
                x1=st_price,
                y0=y_min_with_margin,
                y1=y_max_with_margin,
                xref="x",
                yref="y",
                line=dict(color="#8e44ad", width=2, dash="dash"),
                layer="below"
            )
            
            fig.add_annotation(
                x=st_price,
                y=y_max_with_margin,
                text=f"{st_price:,.2f} (St {int_st})",
                showarrow=False,
                font=dict(size=12, color="black"),
                align="center",
                yshift=int_label
            )
            
            int_label += 20
            int_st += 1

        y1_max = max(abs(y_min_with_margin), abs(y_max_with_margin))
        y2_max = max(
            abs(df[f'df1_{type}'].min()),
            abs(df[f'df1_{type}'].max()),
            abs(df[f'df2_{type}'].min()),
            abs(df[f'df2_{type}'].max())
        )

        fig.update_layout(
            title=custom_title,
            template="plotly_white",
            dragmode=False,
            xaxis=dict(
                fixedrange=False,
                maxallowed=x_max,
                minallowed=x_min,
            ),
            yaxis=dict(
                range=[-y1_max, y1_max],  
                autorange=False,
                title=f"{named_vol_type} Variations (%)",
                zeroline=True,  
                zerolinewidth=1,  
                zerolinecolor='black',
            ),
            yaxis2=dict(
                range=[-y2_max, y2_max],  
                autorange=False,
                title=f"{named_vol_type} Variations (%)",
                overlaying='y',
                side='right',
                zeroline=True,
                zerolinewidth=1,
                zerolinecolor='black',
            ),
            barmode='group',
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

        fig.data[0].update(yaxis='y2')  
        fig.data[1].update(yaxis='y2') 

        return fig
    


    def plot_OIByVolumeAndStrike(self, df, st_price, vol_type):
  
        if vol_type == 'volume':
            named_vol_type = 'Volumes'

        elif vol_type == 'oi':
            named_vol_type = 'OI'

        elif vol_type == 'volAndOI':
            named_vol_type = 'Volumes + OI'

        st_price_color = "#8e44ad"

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=[None],  
            y=[None],
            mode='lines',
            line=dict(color=st_price_color, width=1, dash="dash"), 
            name=f"St price", 
            showlegend=True  
        ))

        if not 'put' in df.columns:
            df['put'] = 0
            min_volume = 0
        else:
            min_volume = -max(df['put']) * 1 

        if not 'call' in df.columns:
            df['call'] = 0
            max_volume = 0
        else: 
            max_volume = max(df['call']) * 1


        # min_volume = -max(df['put']) * 1 
        # max_volume = max(df['call']) * 1  

        fig.add_shape(
            type="line",
            x0=min_volume, x1=max_volume,  
            y0=st_price, y1=st_price,  
            xref="x",
            yref="y",    
            line=dict(color=st_price_color, width=1, dash="dash") 
        )

        fig.add_annotation(
            x=df['call'].max(),
            y=st_price,
            xref="x",
            yref="y",
            text=f"{st_price:,.2f} (St)",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40,
            font=dict(color=st_price_color, size=12)
        )

        fig.add_trace(go.Bar(
            y=df.index,
            x=df['call'],
            orientation='h',
            name='Call OI volume',
            marker=dict(
                color='#58d68d',  
                opacity=1,  
                line=dict(
                    color='#58d68d',  
                    width=1  
                )
            ),
            hovertemplate='Call ' + named_vol_type + ': %{customdata}<br>Strike Price: %{y}<extra></extra>',
            customdata=df['call']
        ))
       

        fig.add_trace(go.Bar(
            y=df.index,
            x=-df['put'], 
            orientation='h',
            name='Put OI volume',
            marker=dict(
                color='#e74c3c', 
                opacity=1,  
                line=dict(
                    color='#e74c3c', 
                    width=1
                )
            ),
            hovertemplate='Put ' + named_vol_type + ': %{customdata}<br>Strike Price: %{y}<extra></extra>',
            customdata=df['put']
        ))

        fig.update_layout(
            yaxis_title="Strike Price",
            xaxis_title=named_vol_type,
            xaxis=dict(
                zeroline=True,
                zerolinecolor="black",
                zerolinewidth=1,
                showgrid=True,
                title="Volume",
                tickvals=[-max(df['put']), 0, max(df['call'])],
                fixedrange=True,
            ),
            yaxis=dict(
                title="Strike Price",
            ),
            title=f"{named_vol_type} on Call & Put",
            barmode='relative',
            showlegend=True,
            template="plotly_white",
            dragmode=False,
            hovermode="x",
            modebar_add=[
                "v1hovermode",
                "toggleSpikelines",
            ],
        )

        return fig


