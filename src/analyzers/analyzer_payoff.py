import pandas as pd
import yfinance as yf
import re

import plotly.graph_objects as go

from src.import_data.utils import LoadingData

from src.config.constant import PROVIDER_LIST


RANGE_UP_FACTOR = 1.8
RANGE_DW_FACTOR = 0.2

################################################################################
###  Metrics (Strats)
################################################################################ 

class StratManager:
    def __init__(self, list_options, type_strat):

        self.type_strat = type_strat
        self.list_options = list_options
        self.message = ''
        self.response = False

        if type_strat == 'simplePayoff':
            self.simplePayoff()

        if type_strat == 'openPayoff':
            self.openPayoff()

    def simplePayoff(self):

        if len(self.list_options) > 1:
            self.message = 'Simple Payoff strategie accept only one option.'
            self.response = False
        
        else:
            self.response = True
        
    def openPayoff(self):

            self.response = True

################################################################################
###  Inputs Converter
################################################################################ 

class OptionInputConverteur:
    def __init__(self, list_options, selected_option, selected_date, selected_hour, stats=False):


        print(selected_option)
        print(list_options)
        self.class_LoadingData = LoadingData()
        
        self.selected_option = selected_option
        self.stats = stats

        self.type = []
        self.pos = []
        self.strike = []
        self.premium = []
        self.expiration = []

        self.underlying, self.change, self.quotation_type, self.quotation_value, self.lot_size = self.class_LoadingData.load_st_ticker_info_json(provider='search', selected_option=selected_option)

        self.last_st = LoadingData().get_st_price_hour(None, selected_date, selected_hour, self.underlying)

        self.optionToList(list_options=list_options)

        print(self.type)
        
        self.calculatorStrat()


    def calculatorStrat(self):
        self.OptionPayoffManager = OptionPayoffManager()
  
        self.figure = self.OptionPayoffManager.payoffCalculator(self.type, self.pos, self.strike, self.premium, self.expiration, self.last_st, change=self.change, stats=self.stats)

    def optionToList(self, list_options):
         
         factor = self.premiumFactor(self.quotation_type, self.quotation_value, self.lot_size)
         
         for i in range(len(list_options)):
           
            if not isinstance(factor, (int, float)):
                print(f"Factor must be a number, but it is of type  {type(factor)}")

            self.type.append(str(list_options[i]['type']))
            self.pos.append(str(list_options[i]['pos']))
            self.strike.append(float(list_options[i]['strike']))
            self.premium.append(float(list_options[i]['premium']) * factor)
            self.expiration.append(list_options[i]['maturity'])

    def premiumFactor(self, quotation_type, quotation_value, lot_size):

        if quotation_type == 'direct_quote':
            premium_factor = int(quotation_value) * int(lot_size)
      
            return premium_factor

        elif quotation_type == 'points':
            premium_factor = int(quotation_value) * int(lot_size)

            return premium_factor

        elif quotation_type == 'nominal_value':
            premium_factor = int(quotation_value)

            return premium_factor 

################################################################################
###  Statistics
################################################################################ 

class Statistics:
    def __init__(self, list_options, selected_option, selected_date, selected_hour):
    
        self.InputConverteur = OptionInputConverteur(list_options, selected_option, selected_date, selected_hour, True)
        self.class_LoadingData = LoadingData()
       
        self.underlying, self.change, self.quotation_type, self.quotation_value, self.lot_size = self.class_LoadingData.load_st_ticker_info_json(provider='search', selected_option=selected_option)
        st_data = yf.download(self.underlying, period='1d', interval='1m')
        self.st_price = round(float(st_data['Close'].iloc[-1]), 2)
    
    def MultiPayoffStats(self):

        df = self.InputConverteur.figure
   
        max_returns = f'{max(df["Global Payoff"]):,.0f} {self.change}'
        max_losses = f'{min(df["Global Payoff"]):,.0f} {self.change}'

        price_to_match = int(self.st_price)
        if price_to_match in df.index:
            value = df['Global Payoff'].loc[price_to_match]  
          
            if isinstance(value, pd.Series): 
                pl_value = float(value.iloc[0]) 
            else: 
                pl_value = float(value)
            pl = f'{pl_value:,.0f} {self.change}'
        else:
            pl = f'Not Found {self.change}'

        break_even_list = []

        for index, value in df['Global Payoff'].items():
            if value == 0:
                break_even_list.append(index)

        if len(break_even_list) > 0:
            closest_index = min(break_even_list, key=lambda x: abs(x - self.st_price))

            min_st_var = - (self.st_price - closest_index) / self.st_price
            min_st = - (self.st_price - closest_index)
            st_var_list = [f'{round(min_st, 2):,.0f} {self.change}', f'({round(min_st_var * 100, 2)} %)']
            break_even = f'{closest_index:,.0f} {self.quotation_type} (closest)'
        else:
            break_even = 'Beyond reach'
            st_var_list = ['Beyond reach', '-- %']
    

        st_var = f'{st_var_list[0]} {st_var_list[1]}'

        return pl, max_returns, max_losses, break_even, st_var

################################################################################
###  Multi payoff
################################################################################ 

class OptionPayoffManager:
    def __init__(self):
        
        pass

    def payoffCalculator(self, list_type, list_pos, list_strike, list_premium, list_maturity, st_price, change=None, stats=False):

        df = pd.DataFrame()

        self.stats = stats
        min_strike = min(list_strike)
        max_strike = max(list_strike)

        for i in range(len(list_type)):

            if list_type[i] == 'call':

                class_ = OptionSimplePayOff(list_pos[i], list_strike[i], list_premium[i], min_strike=min_strike, max_strike=max_strike, st_price=st_price, change=change)
                payoff = class_.callOptions()
                df[f'({i + 1}) {list_pos[i]} call "{list_strike[i]:,.0f}" {list_maturity[i]}'] = payoff

            elif list_type[i] == 'put':
                class_ = OptionSimplePayOff(list_pos[i], list_strike[i], list_premium[i], min_strike=min_strike, max_strike=max_strike, st_price=st_price, change=change)
                payoff = class_.putOptions()
                df[f'({i + 1}) {list_pos[i]} put "{list_strike[i]:,.0f}" {list_maturity[i]}'] = payoff
            
            else:
                raise ValueError("analyzer_payoff -> class OpenStrategie : Position must be 'call' or 'put'.")

        df['Global Payoff'] = df.sum(axis=1)

        if not self.stats:
            plotter = PlotPayoff()
            fig = plotter.PlotOpenStrat(st_price, change, df)
        
            return fig
        
        return df

################################################################################
###  Simple payoff formula
################################################################################ 

class OptionSimplePayOff:
    def __init__(self, position, strike, premium, min_strike=None, max_strike=None, st_price=None, change=None):

        self.st_price = st_price
        self.change = change
        self.position = position
        self.strike = strike
        self.premium = premium
        self.enable_simple_stats = False
        
        self.range_dw, self.range_up = self.calculate_ranges(
            st_price=st_price,
            min_strike=min_strike,
            max_strike=max_strike,
        )
        
        self.payoff_series = None

    def callOptions(self):

        if self.position == 'Long':
            payoff = [- self.premium + max(0, St - self.strike) for St in range(self.range_dw, self.range_up)]
            name_ = 'Long Call Payoff'
        elif self.position == 'Short':
            payoff = [self.premium - max(0, St - self.strike) for St in range(self.range_dw, self.range_up)]
            name_ = 'Short Call Payoff'
        else:
            raise ValueError("Position must be 'Long' or 'Short'.")
        
        self.series_payoff = pd.Series(payoff, index=range(self.range_dw, self.range_up), name=name_)

        
        return self.series_payoff

    def putOptions(self):

        if self.position == 'Long':
            payoff = [- self.premium + max(0, self.strike - St) for St in range(self.range_dw, self.range_up)]
            name_ = 'Long Put Payoff'
        elif self.position == 'Short':
            payoff = [self.premium - max(0, self.strike - St) for St in range(self.range_dw, self.range_up)]
            name_ = 'Short Put Payoff'
        else:
            raise ValueError("Position must be 'long' or 'short'.")
        
        self.series_payoff = pd.Series(payoff, index=range(self.range_dw, self.range_up), name=name_)
        
        
        return self.series_payoff
    
    def calculate_ranges(self, st_price, min_strike, max_strike):
     
        if max_strike < st_price:

            range_up = int(RANGE_UP_FACTOR * float(st_price))
            range_dw = int(RANGE_DW_FACTOR * float(min_strike))

            return range_dw, range_up

        elif max_strike > st_price:

            if min_strike > st_price:
                range_up = int(RANGE_UP_FACTOR * float(max_strike))
                range_dw = int(RANGE_DW_FACTOR * float(st_price))

                return range_dw, range_up
            
            if min_strike < st_price:

                range_up = int(RANGE_UP_FACTOR * float(max_strike))
                range_dw = int(RANGE_DW_FACTOR * float(min_strike))

                return range_dw, range_up

################################################################################
###  Plot
################################################################################          

class PlotPayoff:
    def __init__(self):
        pass

    def PlotOpenStrat(self, st_price, change, payoff_df):

        put_list = []
        call_list = []
        spread_label = []

        for col_name in payoff_df.columns:
            if 'call' in col_name:
                call_list.append(col_name)
            elif 'put' in col_name:
                put_list.append(col_name)

        fig = go.Figure()

        int_label = 10

        for i, items in enumerate(put_list):

            intensity = int(135 * (1 - i / len(put_list)))  
            line_color = f"rgb(255, {max(0, intensity)}, {max(0, intensity)})" 

            strike = float(re.search(r'"(.*?)"', items).group(1).replace(',', ''))
            nb = items[:3]

            fig.add_trace(go.Scatter(
                x=payoff_df.index,
                y=payoff_df[items].values,  
                mode='lines',
                name=f'{items}',
                line=dict(color=line_color, width=2)
            ))

            fig.add_shape(
                type="line",
                x0=strike,
                x1=strike,  
                y0=payoff_df.values.min(),  
                y1=payoff_df.values.max(),  
                xref="x",    
                yref="y",    
                line=dict(color="#3b3b3a", width=2, dash="dot"),  
            )

            fig.add_annotation(
                x=strike,  
                y=payoff_df.values.max(),  
                text=f"{nb} {strike:,.0f}", 
                showarrow=False,  
                yshift=int_label,  
                font=dict(color="#3b3b3a", size=10),
                align="center"
            )

            int_label = int_label + 11

        for i, items in enumerate(call_list):
          
            G_intensity = int(175 + (157 - 48) * (i / len(call_list)))  
            B_intensity = int(48 + (54 - 48) * (i / len(call_list)))    
        
            line_color = f"rgb(0, {G_intensity}, {B_intensity})"

            strike = float(re.search(r'"(.*?)"', items).group(1).replace(',', ''))
            nb = items[:3]
        
            fig.add_trace(go.Scatter(
                x=payoff_df.index,
                y=payoff_df[items].values,  
                mode='lines',
                name=f'{items}',
                line=dict(color=line_color, width=2)
            ))

            fig.add_shape(
                type="line",
                x0=strike,
                x1=strike, 
                y0=payoff_df.values.min(),  
                y1=payoff_df.values.max(),  
                xref="x",   
                yref="y",    
                line=dict(color="#3b3b3a", width=2, dash="dot"), 
            )

            fig.add_annotation(
                x=strike, 
                y=payoff_df.values.max(), 
                text=f"{nb} {strike:,.2f}", 
                showarrow=False,  
                yshift=int_label,  
                font=dict(color="#3b3b3a", size=10),
                align="center"
            )

            int_label = int_label + 11


        #Global payoff
        global_line_color = 'rgb(59, 199, 241)'
        fig.add_trace(go.Scatter(
                x=payoff_df.index,
                y=payoff_df['Global Payoff'].values,  
                mode='lines',
                name='Global Payoff',
                line=dict(color=global_line_color, width=4)
            ))
        
        fig.add_shape(
                type="line",
                x0=st_price,
                x1=st_price,  
                y0=payoff_df.values.min(),  
                y1=payoff_df.values.max(),  
                xref="x",    
                yref="y",    
                line=dict(color="Black", width=2, dash="solid")  
            )
        
        fig.add_annotation(
                x=st_price,
                y=payoff_df.values.max(),  
                text=f"{st_price:,.0f} (St)",  
                showarrow=False, 
                font=dict(size=12, color="black"), 
                align="center",  
                yshift=int_label + 10  
            )

        fig.update_layout(
            title=f"Open Strategy : {len(call_list)} Call(s), {len(put_list)} Put(s),",
            xaxis_title="Underlying Price (St)",
            yaxis_title=f"Payoff ({change})",
            template="plotly_white",
            dragmode=False,
            modebar_add=[
                "v1hovermode",
                "toggleSpikelines",
            ],
            xaxis=dict(
                range=[payoff_df.index.min(), payoff_df.index.max()],
                minallowed=payoff_df.index.min(),
                maxallowed=payoff_df.index.max(),
            ),
        )
        
        return fig
    
