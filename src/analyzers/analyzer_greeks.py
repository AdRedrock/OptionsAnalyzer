import numpy as np
import datetime as dt
from datetime import date, timedelta, datetime

import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy.stats import norm

from src.import_data.utils import LoadingData

################################################################################
###  Dataframe filtering
################################################################################

class DataFilter:
    def __init__(self, df, show_day, exp_selected, exp_type, strike_dw, strike_up):

        self.df = df
        self.show_day = show_day
        self.exp_selected = exp_selected
        self.exp_type = exp_type

        self.strike_dw = strike_dw
        self.strike_up = strike_up

        pass

    def dataFilter(self):

        df = self.df
        exp_selected = self.exp_selected

        if self.show_day:
            col = 'expiration'
        else:
            col = 'expiration_bis'

        if exp_selected and self.exp_type == "Specific":
            
            if self.show_day:
                exp_selected = [int(exp) for exp in exp_selected]
                
            else:
                exp_selected = [pd.to_datetime(exp) for exp in exp_selected]
                self.df[col] = pd.to_datetime(df[col])

            df = df[df[col].isin(exp_selected)].copy()

        if exp_selected and self.exp_type == "Peak":
    
            if self.show_day:
                exp_selected = int(exp_selected) 
                
            else:
                exp_selected = pd.to_datetime(exp_selected)
                df[col] = pd.to_datetime(df[col])
            
            df = df[df[col] <= exp_selected].copy()

        df = df[(self.strike_dw < df['strike']) & (self.strike_up > df['strike'])].copy()

        return df

################################################################################
###  Gamma Exposure
################################################################################

class GammaExposure:
    def __init__(self, selected_date, selected_hour, info, show_day):

        self.selected_date = selected_date
        self.info = info
        self.show_day = show_day
        self.st_ticker = info['underlying_ticker']

        self.last_st = LoadingData().get_st_price_hour(None, selected_date, selected_hour, self.st_ticker)

        self.lot_size = float(self.info['lot_size'])

    def gammaExposureCalcul(self, dataframe, gex_type, vol_type, strike_dw, strike_up, exp_type, exp_selected, plot=True):

        df = DataFilter(dataframe, self.show_day, exp_selected, exp_type, strike_dw, strike_up).dataFilter()

     
        df.loc[:, 'open_interest'] = pd.to_numeric(df['open_interest'], errors='coerce')
        df.loc[:, 'gamma'] = pd.to_numeric(df['gamma'], errors='coerce')

        df.loc[:, 'base_gex'] = df['open_interest'].astype(float) * df['gamma'].astype(float) * float(self.lot_size) * float(self.last_st)
    

        df.loc[df['option_type'] == 'call', 'gex'] = df['base_gex']
        df.loc[df['option_type'] != 'call', 'gex'] = -df['base_gex']

        df.loc[df['option_type'] == 'call', 'abs_gex'] = df['base_gex']
        df.loc[df['option_type'] != 'call', 'abs_gex'] = df['base_gex']

        df.loc[:, 'gex'] = df['gex'].fillna(0)
        df.loc[:, 'abs_gex'] = df['abs_gex'].fillna(0)

        df['adj_volume'] = df['open_interest'] + df['volume']

        df_base = df.groupby(['strike', 'option_type'], as_index=False).agg({
            'volume': 'sum',
            'open_interest': 'sum',
            'adj_volume': 'sum',
            'gex': 'sum',
            'abs_gex': 'sum'
        })

        df_all = df.groupby('strike', as_index=False).agg({
            'volume': 'sum',
            'open_interest': 'sum',
            'adj_volume': 'sum',
            'gex': 'sum',
            'abs_gex': 'sum'
        })
        df_all['option_type'] = 'All'  

        df_final = pd.concat([df_base, df_all], ignore_index=True)
        
        df_pivot = pd.pivot_table(
            data=df_final,
            index='strike',
            values=['adj_volume', 'volume', 'open_interest', 'gex', 'abs_gex'],
            columns=['option_type'],
            aggfunc='sum',
        )

        st_imported_data = df['underlying_price'].iloc[0]

        if plot:
            fig = PlotGreeks().plotNetGex(df_pivot, gex_type, vol_type, self.last_st, st_imported_data)
            return fig

        return None

################################################################################
###  Delta Exposure
################################################################################

class DeltaExposure:
    def __init__(self, selected_date, selected_hour, info, show_day):

        self.selected_date = pd.to_datetime(selected_date)
        self.info = info
        self.show_day = show_day
        self.st_ticker = info['underlying_ticker']

        self.lot_size = float(self.info['lot_size'])
     
        self.last_st = LoadingData().get_st_price_hour(None, selected_date, selected_hour, self.st_ticker)

    def getDeltaExposure(self, dataframe, strike_dw, strike_up, exp_type, exp_selected, plot=True):

        df = DataFilter(dataframe, self.show_day, exp_selected, exp_type, strike_dw, strike_up).dataFilter()
        
        df['strike'] = pd.to_numeric(df['strike'], errors='coerce')
        df['delta'] = pd.to_numeric(df['delta'], errors='coerce')
        
        df.loc[:, 'open_interest'] = pd.to_numeric(df['open_interest'], errors='coerce')
        df.loc[:, 'delta'] = pd.to_numeric(df['delta'], errors='coerce')


        df['dex'] = df['open_interest'].astype(float) * df['delta'].astype(float) * float(self.lot_size) 

        df_base = df.groupby(['strike', 'option_type'], as_index=False).agg({
            'dex': 'sum',
        })

        df_all = df.groupby('strike', as_index=False).agg({
            'dex': 'sum',
        })

        df_all['option_type'] = 'All'  

        df_final = pd.concat([df_base, df_all], ignore_index=True)
        
        df_pivot = pd.pivot_table(
            data=df_final,
            index='strike',
            values=['dex'],
            columns=['option_type'],
            aggfunc='sum',
        )

        st_imported_data = df['underlying_price'].iloc[0]

        if plot:
            fig = PlotGreeks().plotDex(df_pivot, self.last_st, st_imported_data)
            return fig

        return df_pivot

################################################################################
###  Vanna Exposure
################################################################################

class VannaCumulative:
    def __init__(self, selected_date, selected_hour, info, show_day):
        
        self.selected_date = pd.to_datetime(selected_date)
        self.info = info
        self.show_day = show_day
        self.st_ticker = info['underlying_ticker']

        self.lot_size = float(self.info['lot_size'])
     
        self.last_st = LoadingData().get_st_price_hour(None, selected_date, selected_hour, self.st_ticker)
        self.rf = float(LoadingData().get_last_st(None, True, self.selected_date, '^IRX'))

    def vanna(self, S: float, K: float, T: float, r: float, q: float, sigma: float) -> float:

        S = float(S)
        K = float(K)
        T = float(T)
        r = float(r)
        q = float(q)
        sigma = float(sigma)
        
        if T <= 0 or sigma <= 0:
            return 0.0
            
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        N_prime_d1 = norm.pdf(d1)
        
        return np.exp(-q * T) * N_prime_d1 * d2 / sigma

    def getVannaExposure(self, dataframe, strike_dw, strike_up, exp_type, exp_selected, plot=True) -> pd.DataFrame:
        
        df = DataFilter(dataframe, self.show_day, exp_selected, exp_type, strike_dw, strike_up).dataFilter()
        
        df['strike'] = pd.to_numeric(df['strike'], errors='coerce')
        df['implied_volatility'] = pd.to_numeric(df['implied_volatility'], errors='coerce')
        
        mask = (df['dte'].notna() & 
               df['strike'].notna() & 
               df['implied_volatility'].notna())
        
        
        df['vanna'] = 0.0  

        df.loc[mask, 'vanna'] = df[mask].apply(
            lambda row: self.vanna(
                S=self.last_st,
                K=float(row['strike']),  
                T=float(row['dte'])/252,
                r=self.rf/100,
                q=0,
                sigma=float(row['implied_volatility'])
            ),
            axis=1
        )

        base_vex = df['open_interest'].astype(float) * \
               df['vanna'].astype(float) * \
               float(self.lot_size) * \
               float(self.last_st) * \
               df['implied_volatility'].astype(float) * \
               self.last_st
    
        df['vex'] = np.where(
            df['option_type'] == 'call',
            +base_vex,
            base_vex * -1
        )

        df['abs_vex'] = np.where(
            df['option_type'] == 'call',
            base_vex,
            base_vex 
        )

        df['vex'] = df['vex'].fillna(0)
        df['abs_vex'] = df['abs_vex'].fillna(0)

 

        df_base = df.groupby(['strike', 'option_type'], as_index=False).agg({
            'vex': 'sum',
            'abs_vex': 'sum'
        })

        df_all = df.groupby('strike', as_index=False).agg({
            'vex': 'sum',
            'abs_vex': 'sum'
        })
        df_all['option_type'] = 'All'  

        df_final = pd.concat([df_base, df_all], ignore_index=True)
        
        df_pivot = pd.pivot_table(
            data=df_final,
            index='strike',
            values=['vex', 'abs_vex'],
            columns=['option_type'],
            aggfunc='sum',
        )
        
        st_imported_data = df['underlying_price'].iloc[0]

        if plot:
            fig_vanna = PlotGreeks().plotVex(df_pivot, self.last_st, st_imported_data)
            return fig_vanna

        return df_pivot

##########################################################################################
###    Plot
##########################################################################################

class PlotGreeks:
    def __init__(self):
        pass

    
    def plotDex(self, df_pivot, last_st, st_imported):

        fig = go.Figure()

        dex_pos_color = '#00AEEF'
        dex_neg_color = '#0077C8'   
        call_color = '#01ac2d'  
        put_color = '#E74C3C'

        df_pivot[('dex', 'put')] = df_pivot[('dex', 'put')] * -1

        fig.add_trace(
            go.Bar(
                x=df_pivot.index,
                y=df_pivot[('dex', 'All')],
                name='Net Dex',
                marker=dict(
                    color=np.where(df_pivot[('dex', 'All')] > 0, dex_pos_color, dex_neg_color)  
                ),
                yaxis='y',
                zorder=1,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df_pivot.index,
                y=df_pivot[('dex', 'call')],
                name=f'abs. Call Dex',
                mode='lines',
                line=dict(
                    width=1,
                    shape='spline'
                ),
                marker=dict(color=call_color),
                yaxis='y',
                showlegend=True,
                zorder=2,
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=df_pivot.index,
                y=df_pivot[('dex', 'put')],
                name=f'abs. Put Dex',
                mode='lines',
                line=dict(
                    width=1,
                    shape='spline'
                ),
                marker=dict(color=put_color),
                yaxis='y',
                showlegend=True,
                zorder=2,
            )
        )


        min_y_st = min(df_pivot[('dex', 'put')].min(), df_pivot[('dex', 'call')].min(), df_pivot[('dex', 'All')].min()) * 0.7
        max_y_st = max(df_pivot[('dex', 'put')].max(), df_pivot[('dex', 'call')].max(), df_pivot[('dex', 'All')].max()) * 1.4

        fig.add_shape(
            type="line",
            x0=last_st,
            x1=last_st,
            y0=min_y_st,
            y1=max_y_st,
            xref="x",
            yref="y",
            line=dict(color="#8e44ad", width=2, dash="dash"),
            layer="below",
            showlegend=True,
            name=f"{last_st:,.2f} (last St)"
        )

        fig.add_shape(
            type="line",
            x0=st_imported,
            x1=st_imported,
            y0=min_y_st,
            y1=max_y_st,
            xref="x",
            yref="y",
            line=dict(color="#8e44ad", width=1, dash="solid"),
            layer="below",
            showlegend=True,
            name=f"{last_st:,.2f} (data St)"
        )
        
        fig.update_layout(
            title=f"Delta Exposure",
            xaxis=dict(
                title="Strike Price",
                zeroline=True,
                zerolinecolor="black",
                zerolinewidth=1,
                showgrid=False,
                fixedrange=True
            ),
            yaxis=dict(
                title='Delta Exposure',
                side="left",
                showgrid=False,
                fixedrange=False,   
                autorange=True,   
                maxallowed=max_y_st,
                minallowed=min_y_st,
            ),
            showlegend=True,
            template="plotly_white",
            dragmode=False,
            hovermode="x",
            modebar_add=[
                "v1hovermode",
                "toggleSpikelines",
            ],
            legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=-0.2,
                    xanchor='center',
                    x=0.5
                ),
            margin=dict(l=50, r=50, t=50, b=50)
        )

        return fig

    def plotNetGex(self, df, gex_type, vol_type, last_st, st_imported):
     
        vol_type_map = {
            'volume': ('volume', 'Volume'),
            'oi': ('open_interest', 'OI'),
            'volAndOI': ('adj_volume', 'Vol. & OI')
        }

        if vol_type not in vol_type_map:
            raise ValueError("Invalid vol_type. Choose from ['volume', 'oi', 'volAndOI']")

        col_vol_type, vol_label = vol_type_map[vol_type]

        gex_pos_color = '#00AEEF'
        gex_neg_color = '#0077C8'   
        call_color = '#01ac2d'  
        put_color = '#E74C3C'

        fig = go.Figure()

        y_min = min(df[('gex', 'All')].min(), 0)
        if gex_type == 'abs':
            y_max = max(df[('gex', 'All')].max(), df[('abs_gex', 'All')].max())
        else:
            y_max = max(df[('gex', 'All')].max(), df[(col_vol_type, 'call')].max(), df[(col_vol_type, 'put')].max())

        margin = (y_max - y_min) * 0.1
        y_min_with_margin = y_min - margin
        y_max_with_margin = y_max + margin

        if gex_type == 'abs':
            y_min_vol = min(df[('abs_gex', 'All')].min(), 0)
            y_max_vol = df[('abs_gex', 'All')].max()  
        else:
            y_min_vol = min(df[(col_vol_type, 'call')].min(), df[(col_vol_type, 'put')].min(), 0)
            y_max_vol = max(df[(col_vol_type, 'call')].max(), df[(col_vol_type, 'put')].max())
        margin_vol = (y_max_vol - y_min_vol) * 0.1
        
        y_min_gex = min(df[('gex', 'All')].min(), 0)
        y_max_gex = max(df[('gex', 'All')].max(), 0)
        margin_gex = (y_max_gex - y_min_gex) * 0.1

        fig.add_shape(
            type="line",
            x0=st_imported,
            x1=st_imported,
            y0=y_min_with_margin,
            y1=y_max_with_margin,
            xref="x",
            yref="y",
            line=dict(color="#8e44ad", width=1, dash="solid"),
            layer="below",
            showlegend=True,
            name=f"{last_st:,.2f} (data St)"
        )

        fig.add_shape(
            type="line",
            x0=last_st,
            x1=last_st,
            y0=y_min_with_margin,
            y1=y_max_with_margin,
            xref="x",
            yref="y",
            line=dict(color="#8e44ad", width=2, dash="dash"),
            layer="below",
            showlegend=True,
            name=f"{last_st:,.2f} (last St)"
        )

        # Plot GEX
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df[('gex', 'All')],
                name='Net GEX',
                marker=dict(
                    color=np.where(df[('gex', 'All')] > 0, gex_pos_color, gex_neg_color)  
                ),
                yaxis="y2",
                zorder=3,
            )
        )


        if gex_type == 'net':
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[(col_vol_type, 'call')],
                    name=f'Call {vol_label} Area',
                    mode='lines',
                    line=dict(
                        width=1,
                        shape='spline' 
                    ),
                    marker=dict(color=call_color),
                    yaxis='y',
                    showlegend=True,
                    zorder=2,
                    fill='tonexty',
                    fillcolor='rgba(1, 172, 45, 0.3)',
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[(col_vol_type, 'put')],
                    name=f'Put {vol_label} Area',
                    mode='lines',
                    line=dict(
                        width=1,
                        shape='spline' 
                    ),
                    marker=dict(color=put_color),
                    yaxis='y',
                    showlegend=True,
                    zorder=1,
                    fill='tonexty',
                    fillcolor='rgba(231, 76, 60, 0.3)',
                )
            )
        
        elif gex_type == 'abs':

            vol_label = 'Abs. GEX'
            abs_gex_color = '#ad02d6'

            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[('abs_gex', 'All')],
                    name=f'Absolute Gex Area',
                    mode='lines',
                    line=dict(
                        width=1,
                        shape='spline'  
                    ),
                    marker=dict(color=abs_gex_color),
                    yaxis='y',
                    showlegend=True,
                    zorder=1,
                    fill='tonexty',
                    fillcolor='rgba(173, 2, 214, 0.3)',
                )
            )
        
        fig.update_layout(
            title=f"Net GEX & {vol_label}",
            xaxis=dict(
                title="Strike Price",
                zeroline=True,
                zerolinecolor="black",
                zerolinewidth=1,
                showgrid=False,
                fixedrange=True
            ),
            yaxis=dict(
                title=vol_label,
                side="left",
                range=[y_min_vol - margin_vol, y_max_vol + margin_vol],
                showgrid=False,
                gridcolor='lightgrey',
                fixedrange=False,    
                autorange=False,    
                minallowed=y_min_vol - margin_vol,
            ),
            yaxis2=dict(
                title="Net GEX",
                overlaying="y",
                side="right",
                range=[y_min_gex - margin_gex, y_max_gex + margin_gex],
                showgrid=False,
                fixedrange=False,
                autorange=False,
                minallowed=y_min_gex - margin_gex,
            ),
            barmode="relative",
            showlegend=True,
            template="plotly_white",
            dragmode=False,
            hovermode="x",
            modebar_add=[
                "v1hovermode",
                "toggleSpikelines",
            ],
            legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=-0.2,
                    xanchor='center',
                    x=0.5
                ),
            margin=dict(l=50, r=50, t=50, b=50)
        )

        return fig
    
    def plotVex(self, df_pivot_vanna, last_st, st_imported):
     
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df_pivot_vanna.index,
                y=df_pivot_vanna[('abs_vex', 'All')],
                name=f'Sum Vanna',
                mode='lines',
                line=dict(
                    width=1,
                    shape='spline' 
                ),
                marker=dict(color='blue'),
                yaxis='y',
                showlegend=True,
                zorder=4,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df_pivot_vanna.index,
                y=df_pivot_vanna[('abs_vex', 'call')],
                name=f'Call Vanna',
                mode='lines',
                line=dict(
                    width=1,
                    shape='spline' 
                ),
                marker=dict(color='green'),
                yaxis='y',
                showlegend=True,
                zorder=4,
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df_pivot_vanna.index,
                y=df_pivot_vanna[('abs_vex', 'put')],
                name=f'Put Vanna',
                mode='lines',
                line=dict(
                    width=1,
                    shape='spline' 
                ),
                marker=dict(color='red'),
                yaxis='y',
                showlegend=True,
                zorder=4,
            )
        )

        min_y_st = min(df_pivot_vanna[('abs_vex', 'put')].min(), df_pivot_vanna[('abs_vex', 'call')].min(), df_pivot_vanna[('abs_vex', 'All')].min(), df_pivot_vanna[('vex', 'All')].min())
        max_y_st = max(df_pivot_vanna[('abs_vex', 'put')].max(), df_pivot_vanna[('abs_vex', 'call')].max(), df_pivot_vanna[('abs_vex', 'All')].max(), df_pivot_vanna[('vex', 'All')].max())

        fig.add_shape(
            type="line",
            x0=last_st,
            x1=last_st,
            y0=min_y_st,
            y1=max_y_st,
            xref="x",
            yref="y",
            line=dict(color="#8e44ad", width=2, dash="dash"),
            layer="below",
            showlegend=True,
            name=f"{last_st:,.2f} (last St)"
        )

        fig.add_shape(
            type="line",
            x0=st_imported,
            x1=st_imported,
            y0=min_y_st,
            y1=max_y_st,
            xref="x",
            yref="y",
            line=dict(color="#8e44ad", width=1, dash="solid"),
            layer="below",
            showlegend=True,
            name=f"{last_st:,.2f} (data St)"
        )
        
        fig.update_layout(
            title=f"Vanna Exposure",
            xaxis=dict(
                title="Strike Price",
                zeroline=True,
                zerolinecolor="black",
                zerolinewidth=1,
                showgrid=False,
                fixedrange=True
            ),
            yaxis=dict(
                title='Vanna Exposure',
                side="left",
                showgrid=False,
                fixedrange=False,   
                autorange=True,    
            ),
            showlegend=True,
            template="plotly_white",
            dragmode=False,
            hovermode="x",
            modebar_add=[
                "v1hovermode",
                "toggleSpikelines",
            ],
            legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=-0.2,
                    xanchor='center',
                    x=0.5
                ),
            margin=dict(l=50, r=50, t=50, b=50)
        )

        return fig