from datetime import datetime, date, timedelta

import dash
from dash import html, Input, Output, State, callback_context, ALL

import pandas as pd
import plotly.graph_objects as go

from src.gui.pages.payoff import SetOptions
from src.import_data.utils import LoadingData, ConvertData

from src.analyzers.analyzer_monte_carlo import Simulation, GetDataAndCalculation
from src.analyzers.analyzer_payoff import Statistics, OptionInputConverteur, StratManager

##########################################################################################
##########################################################################################
###    Layout SetUpLayout CALL-BACK
##########################################################################################
##########################################################################################

class SetUpLayoutCallBack:
    def __init__(self):
        
        pass

    @dash.callback(
        Input('strategy-selection', 'value')     
    )
    def update_tickerDropDown(selected_strategy):
        global STRAT
        STRAT = selected_strategy


##########################################################################################
###   Refresh Options Tickers
##########################################################################################

    @dash.callback(
        Output('option-selection', 'options'),
        Input('import-already-imported-options-ticker-store', 'data'),
    )
    def refresh_optionsTickers(current):
        already_imported = LoadingData().load_existing_symbols()

        dropdown_options = [{"label": option, "value": option} for option in already_imported]
    
        return dropdown_options

##########################################################################################
###   DataFrame Date Imported
##########################################################################################
    @dash.callback(
        Output('imported-date-selection', 'disabled'), 
        Output('imported-date-selection', 'className'),
        Output('imported-date-selection', 'options'),
        Input('option-selection', 'value'),     
    )
    def update_dateTickerDropDown(selected_option):

        if selected_option is None:
            
            className='drop_down_disabled'
            options = []  
            return True, className, options
        

        class_import = LoadingData()

        dates = class_import.load_date_imported(selected_option, hour=False, selected_date=None)

        sorted_dates = sorted(dates, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=True)

        options = [{"label": date, "value": date} for date in sorted_dates]

        className='drop_down'

        return False, className, options


##########################################################################################
###    CALL-BACK load main ticker Hour
##########################################################################################

    @dash.callback(
        Output('imported-date-hour-selection', 'disabled'), 
        Output('imported-date-hour-selection', 'className'),
        Output('imported-date-hour-selection', 'options'),

        Input('option-selection', 'value'), 
        Input('imported-date-selection', 'value'),   
    )
    def update_dateTickerDropDown(selected_option, selected_date):

        if selected_date is None or selected_option is None:
            
            className='drop_down_disabled'
            options = []  
            return True, className, options
        
        class_import = LoadingData()

        hours_list = class_import.load_date_imported(selected_option, hour=True, selected_date=selected_date)
        print(hours_list)


        options = ConvertData().format_hours_for_dropdown(hours_list)

        className='drop_down'

        return False, className, options

##########################################################################################
##########################################################################################
###    TAB -> SetOptions CALL-BACK
##########################################################################################
##########################################################################################

class SetOptionsCallBack:
    def __init__(self):
        
        pass

##########################################################################################
###    CALL BACK ENABLE POS & TYPE SELECTION
##########################################################################################

    @dash.callback(
    Output("loading-output", "children"),
    Output('options-select-df', 'data'),
    Output('type-selection', 'disabled'), 
    Output('type-selection', 'className'),
    Output('type-selection', 'options'), 

    Output('pos-selection', 'disabled'), 
    Output('pos-selection', 'className'),
    
    Input('imported-date-selection', 'value'), 
    Input('option-selection', 'value'),  
    Input('strategy-selection', 'value'),
    Input('payoff-show-days-switch', 'value'),
    Input('imported-date-hour-selection', 'value'),
)
    def activate_callPutDropDown(selected_date, selected_option, selected_strategy, show_day, selected_hour):

        if selected_option is None or selected_date is None or selected_strategy is None:
       
            return 'state', dash.no_update, True, 'adapt_drop_down_disabled', [], True, 'adapt_drop_down_disabled'

        if selected_date and selected_option and selected_hour:

            MAIN_DF = LoadingData().get_data_csv(selected_option, selected_date, selected_hour)
            
            selected_strategy = selected_strategy.lower()
            className = 'adapt_drop_down'
        
            options = [
                {'label': 'Call', 'value': 'call', 'disabled': False},
                {'label': 'Put', 'value': 'put', 'disabled': False}
            ]


            if True in show_day:
                function = ConvertData().convert_expiration_to_day(MAIN_DF, selected_date)
                MAIN_DF['expiration'] = function

            FILTRED_DF = MAIN_DF.loc[:, ['option_type', 'strike', 'ask', 'bid', 'expiration', 'implied_volatility']]

            FILTRED_DF = FILTRED_DF[(FILTRED_DF['ask'] != 0) & (FILTRED_DF['bid'] != 0)]
            FILTRED_DF = FILTRED_DF.reset_index()

            store_data = FILTRED_DF.to_dict('records')
        

            return 'state', store_data, False, className, options, False, className
        
        else:
            return 'state', dash.no_update, True, 'adapt_drop_down_disabled', [], True, 'adapt_drop_down_disabled'

##########################################################################################
###    CALL FILTER 1 By Type And Pos
##########################################################################################

    @dash.callback(
        Output('options-select-df-filtred', 'data'),

        Output('strike-selection', 'disabled'), 
        Output('strike-selection', 'className'),
        Output('strike-selection', 'options'),

        Output('premium-selection', 'disabled'), 
        Output('premium-selection', 'className'),
        Output('premium-selection', 'options'),

        Output('maturity-selection', 'disabled'), 
        Output('maturity-selection', 'className'),
        Output('maturity-selection', 'options'),
        
        Input('options-select-df', 'data'),
        Input('type-selection', 'value'),
        Input('pos-selection', 'value'),
        
        Input('type-selection', 'value'),
        Input('pos-selection', 'value'),
        State('payoff-show-days-switch', 'value'),
    )
    def filter_typeAndPos(stored_df, selected_type, selected_pos, state_type, state_pos, show_day):

        df_filtered = pd.DataFrame(stored_df)

        if not all([selected_type, selected_pos, state_type, state_pos]):
            return [], True, 'adapt_drop_down_disabled', [],True, 'adapt_drop_down_disabled', [], True, 'adapt_drop_down_disabled', []
        
        if selected_type or state_type:
            df_filtered = df_filtered[
                (df_filtered['option_type'] == selected_type) | (df_filtered['option_type'] == state_type)
            ]
        
        if selected_pos == 'Long' or state_pos == 'Long':
            df_filtered['premium'] = df_filtered['ask']
        elif selected_pos == 'Short' or state_pos == 'Short':
            df_filtered['premium'] = df_filtered['bid']

        strike_options = [{"label": f"{strike:,.2f}", "value": strike} for strike in sorted(df_filtered['strike'].unique())]
        premium_options = [{"label": f"{premium:,.2f}", "value": premium} for premium in sorted(df_filtered['premium'].unique())]
        maturity_options = [{"label": exp, "value": exp} for exp in sorted(df_filtered['expiration'].unique())]

        #Date or Days Filter
        if len(show_day) == 0:

            dates = df_filtered['expiration']

            sorted_dates = sorted(dates, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=False)
            maturity_options = [{"label": exp, "value": exp} for exp in sorted_dates]

        elif True in show_day:
            
            def parse_expiration(exp):
                if "days" in exp:
                    return int(exp.split()[0])  
                return float('inf') 
            
            expirations = sorted(
                [exp for exp in df_filtered['expiration'].unique()],
                key=parse_expiration
            )
            
            maturity_options = (
                [{"label": str(exp), "value": str(exp)} for exp in expirations]
            )
        else:
            maturity_options = [{"label": exp, "value": exp} for exp in sorted(df_filtered['expiration'].unique())]

        filtered_data = df_filtered.to_dict('records')
     
        return filtered_data, False, 'adapt_drop_down', strike_options, False,  'adapt_drop_down', premium_options, False, 'adapt_drop_down', maturity_options

##########################################################################################
###    CALL FILTER 2 By Strike, Premium, maturity
##########################################################################################

    @dash.callback(
        Output('strike-selection', 'options', allow_duplicate=True),
        Output('strike-selection', 'value'),
        Output('premium-selection', 'options', allow_duplicate=True),
        Output('premium-selection', 'value'),
        Output('maturity-selection', 'options', allow_duplicate=True),
        Output('maturity-selection', 'value'),
        State('options-select-df-filtred', 'data'),
        Input('strike-selection', 'value'),
        Input('premium-selection', 'value'),
        Input('maturity-selection', 'value'),
        State('payoff-show-days-switch', 'value'),
        Input('options-selected-store', 'data'),
        prevent_initial_call='initial_duplicate'
    )
    def update_allfilters(stored_data, selected_strike, selected_premium, selected_maturity, show_day, selected_store):
        if not stored_data:
            return [], None, [], None, [], None

        df_filtered = pd.DataFrame(stored_data)
        df_selected = pd.DataFrame(selected_store)
        
        required_columns = ['strike', 'premium', 'expiration']
        if not all(col in df_filtered.columns for col in required_columns):
            pass

        if not df_selected.empty:
            maturity_value = df_selected['maturity'].iloc[0]
            df_filtered = df_filtered[df_filtered['expiration'] == maturity_value]

        if selected_strike:
            df_filtered = df_filtered[df_filtered['strike'] == selected_strike]

        if selected_premium:
            df_filtered = df_filtered[df_filtered['premium'] == selected_premium]

        strike_options = [{"label": f"{strike:,.2f}", "value": strike} for strike in sorted(df_filtered['strike'].unique())]
        premium_options = [{"label": f"{premium:,.2f}", "value": premium} for premium in sorted(df_filtered['premium'].unique())]

        if not df_selected.empty:
            maturity_value = df_selected['maturity'].iloc[0]
            if True in show_day:
                maturity_options = [{"label": str(maturity_value), "value": str(maturity_value)}]
            else:
                maturity_options = [{"label": str(maturity_value), "value": str(maturity_value)}]
            selected_maturity = maturity_value
        else:
            if len(show_day) == 0:
                dates = df_filtered['expiration']
                sorted_dates = sorted(dates, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=False)
                maturity_options = [{"label": exp, "value": exp} for exp in sorted_dates]
            elif True in show_day:
                def parse_expiration(exp):
                    if "days" in exp:
                        return int(exp.split()[0])  
                    return float('inf') 
                
                expirations = sorted(
                    [exp for exp in df_filtered['expiration'].unique()],
                    key=parse_expiration
                )
                maturity_options = [{"label": str(exp), "value": str(exp)} for exp in expirations]
            else:
                maturity_options = [{"label": exp, "value": exp} for exp in sorted(df_filtered['expiration'].unique())]
            selected_maturity = selected_maturity if selected_maturity in [opt['value'] for opt in maturity_options] else None

        selected_strike = selected_strike if selected_strike in [opt['value'] for opt in strike_options] else None
        selected_premium = selected_premium if selected_premium in [opt['value'] for opt in premium_options] else None

        return (
            strike_options, selected_strike,
            premium_options, selected_premium,
            maturity_options, selected_maturity
        )


##########################################################################################
###    CALL BACK ADD/REMOVE SELECTION
##########################################################################################


    @dash.callback(
    Output('options-selected-store', 'data'),
    Output('selected-options-container', 'children'),
    
    Output('payoff-msgbox', 'is_open'),
    Output('payoff-msgbox', 'color'),
    Output('payoff-msgbox', 'children'),

    Output('payoff-chart', 'figure'),

    Output('pl-value', 'children'),
    Output('breakeven-value', 'children'),
    Output('max-gain-value', 'children'),
    Output('max-loss-value', 'children'),
    Output('st-var-value', 'children'),

    Input('add-options-selection', 'n_clicks'),
    Input({'type': 'del-options-btn', 'index': ALL}, 'n_clicks'),

    State('options-selected-store', 'data'),
    State('option-selection', 'value'),

    State('type-selection', 'value'),
    State('pos-selection', 'value'),
    State('strike-selection', 'value'),
    State('premium-selection', 'value'),
    State('maturity-selection', 'value'),
    State('strategy-selection', 'value'),

    Input('imported-date-selection', 'value'), 
    Input('imported-date-hour-selection', 'value'),  

    State('options-select-df-filtred', 'data'),
    )
    def click_button_add_option(n_clicks, del_clicks, store_selection, selected_option, selected_type, selected_pos, selected_strike, selected_premium, selected_maturity, type_strat, selected_date, selected_hour, filtered_data):

        # Default plot
        fig = go.Figure()
        fig.add_annotation(
            text="Select option(s)",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
            xref="paper",
            yref="paper"
        )
        fig.update_layout(
            title="Waiting for selection",
            template="plotly_white",
            dragmode="pan",
        )

        if not all([selected_option, selected_date, selected_hour]):
            return (
                [], 
                [], 
                False,
                'info',
                'Default message', 
                fig, 
                '--', 
                '--', 
                '--', 
                '--', 
                '--'  
            )

        df_filtered = pd.DataFrame(filtered_data)
        store_selection = store_selection or [] 
        check_store_selection = store_selection.copy()

        open_msgbox = False
        message = 'Default message'
        color = 'info'

        pl = '--'
        break_even = '--'
        max_returns = '--'
        max_losses = '--'
        st_var = '--'

        ctx = callback_context

        if not ctx.triggered:
            return store_selection, [], open_msgbox, color, message, fig, pl, break_even, max_returns, max_losses, st_var

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if 'add-options-selection' in triggered_id:
         
            if n_clicks and all([selected_type, selected_pos, selected_strike, selected_premium, selected_maturity]):

                filtered_iv = df_filtered.loc[
                    (df_filtered['strike'] == selected_strike) &
                    (df_filtered['expiration'] == selected_maturity) &
                    (df_filtered['premium'] == selected_premium) &
                    (df_filtered['option_type'] == selected_type),
                    'implied_volatility'
                ]

                if not filtered_iv.empty:
                    iv = filtered_iv.iloc[0]
                else:
                    iv = None  
            
                id_row = len(store_selection) + 1
                new_row = {
                    "id": id_row,
                    "type": selected_type,
                    "pos": selected_pos,
                    "strike": selected_strike,
                    "premium": selected_premium,
                    "maturity": selected_maturity,
                    "iv":iv,
                }

                check_store_selection.append(new_row)

                class_check = StratManager(check_store_selection, type_strat)

                response = class_check.response
        
                if response == True:
                    store_selection.append(new_row)
                
                else:
                    open_msgbox = True
                    message = class_check.message
                    color = 'danger'
                    
        elif 'del-options-btn' in triggered_id:
            for i, del_click in enumerate(del_clicks):
                if del_click:  
                    index_to_delete = i
                    if 0 <= index_to_delete < len(store_selection):
                        del store_selection[index_to_delete]
                        break
                    
        rows = [
            SetOptions().rowContainerSelected(
                str(row['id']), row['type'], row['pos'], row['strike'], row['premium'], row['maturity']
            )
            for row in store_selection
        ]

        
        if len(rows) > 0 and selected_date and selected_hour:

            class_data = OptionInputConverteur(store_selection, selected_option, selected_date, selected_hour, False)

            pl, max_returns, max_losses, break_even, st_var = Statistics(store_selection, selected_option, selected_date, selected_hour).MultiPayoffStats()
         
            return store_selection, rows, open_msgbox, color, message, class_data.figure, pl, break_even, max_returns, max_losses, st_var

        return store_selection, rows, open_msgbox, color, message, fig, pl, break_even, max_returns, max_losses, st_var

##########################################################################################
##########################################################################################
###    TAB -> MonteCarloSimulation CALL-BACK
##########################################################################################
##########################################################################################

class MonteCarloSimulationCallBack:

    def __init__(self):
        pass   


##########################################################################################
###    CallBack Date Picker Range
##########################################################################################
    @dash.callback(
            Output('payoff-sim-range-date-picker', 'disabled'),
            Output('payoff-sim-range-date-picker', 'min_date_allowed'),
            Output('payoff-sim-range-date-picker', 'start_date'),
            Output('payoff-sim-range-date-picker', 'end_date'),

            Input('payoff-auto-stats-switch', 'value'),
            Input('option-selection', 'value')
    )
    def update_datePickerRange(switch_auto, selected_option):

        if True in switch_auto and selected_option:

            end_date = date.today()
         
            min_date = LoadingData().get_max_start_date(selected_option)
            start_date = date.today() - timedelta(days=365)

            return False, min_date, start_date, end_date
        
        return True, None, None, None
    

##########################################################################################
###    CallBack Auto Sig and Mu
##########################################################################################
    @dash.callback(
            Output('payoff-mu-input', 'value'),
            Output('payoff-sig-input', 'value'),

            Input('payoff-sim-range-date-picker', 'start_date'),
            Input('payoff-sim-range-date-picker', 'end_date'),
            Input('option-selection', 'value')
    )
    def update_datePickerRange(start_date, end_date, selected_option):

        class_ = GetDataAndCalculation()
        
        if start_date and end_date:

            mu, sig = class_.get_st_mu_sig(start_date, end_date, selected_option)

            rounded_mu = f'{round(mu *100, 4)} %' if mu is not None else None
            rounded_sig = f'{round(sig * 100, 4)} %' if sig is not None else None

            return rounded_mu, rounded_sig

        return None, None
    
##########################################################################################
###    Switch IV
##########################################################################################
    @dash.callback(
        Output('payoff-iv-dd', 'disabled'),
        Output('payoff-iv-dd', 'className'),
        Output('payoff-iv-dd', 'options'),  
        Output('payoff-sig-input', 'disabled'),
        Output('payoff-sig-input-div', 'className'),
        Input('payoff-custom-iv-switch', 'value'),
        Input('options-selected-store', 'data'),
    )
    def update_switchIv(switch_iv, selected_data_stored):

        className = 'drop_down_disabled'
        classNameInput = 'input_field'

        if True in switch_iv:

            if not selected_data_stored or not isinstance(selected_data_stored, list):
                iv_options = []
            else:

                iv_options_part = [
                    {"label": f"{option['iv'] * 100:.3f} % - ({option['id']}) {option['type']} {option['maturity']}", "value": option['iv'] * 100}
                    for option in selected_data_stored if 'iv' in option and 'maturity' in option and 'type' in option and 'id' in option
                ]

                if len(selected_data_stored) > 1:
                
                    iv_values = [option['iv'] for option in selected_data_stored if 'iv' in option]

                    if iv_values:
                        iv_mean = sum(iv_values) / len(iv_values)
                    else:
                        iv_mean = 0  

                    iv_mean_option = [{"label": f"{iv_mean * 100:.3f} % (IV mean)", "value": iv_mean * 100}]

                    iv_options = iv_options_part + iv_mean_option

                else:

                    iv_options = iv_options_part 
        
            className = 'drop_down'
            classNameInput = 'input_field_disabled'

            return False, className, iv_options, True, classNameInput

        iv_options = []
        return True, className, iv_options, False, classNameInput

    

##########################################################################################
###    Enable mu 
##########################################################################################

    @dash.callback(
        Output('payoff-mu-input', 'disabled'),
        
        Input('payoff-auto-stats-switch', 'value')
    )
    def update_muAndSigDd(switch_auto):

        if switch_auto == True:
            
            return True

        return False
    

##########################################################################################
###    Enable simulation time
##########################################################################################
    @dash.callback(
    Output('payoff-sim-exp-dd', 'disabled'),
    Output('payoff-sim-exp-dd', 'placeholder'),
    Output('payoff-sim-exp-dd', 'className'),
    Output('payoff-sim-exp-dd', 'options'),
    Output('payoff-sim-exp-dd', 'value'),
    Input('options-selected-store', 'data'),
    Input('payoff-show-days-switch', 'value'),
    )
    def update_maturitySelection(stored_data, show_day):

        className = 'drop_down_disabled'
        placeholder = "Simulation Time"
        value = ''
        options = [
            {'label': '1 week', 'value': '1w'},
            {'label': '2 weeks', 'value': '2w'},
            {'label': '1 month', 'value': '1mo'},
            {'label': '3 months', 'value': '3mo'},
            {'label': '6 months', 'value': '6mo'},
            {'label': '1 year', 'value': '1y'},
            {'label': '2 years', 'value': '2y'},
        ]


        if stored_data and True in show_day:
            className = 'drop_down'

            options = [
                {'label': 'Min expiration', 'value': 'min'},
                {'label': 'Max expiration', 'value': 'max'},
                {'label': '1 week', 'value': '1w'},
                {'label': '2 weeks', 'value': '2w'},
                {'label': '1 month', 'value': '1mo'},
                {'label': '3 months', 'value': '3mo'},
                {'label': '6 months', 'value': '6mo'},
                {'label': '1 year', 'value': '1y'},
                {'label': '2 years', 'value': '2y'},
            ]
          
            return False, placeholder, className, options, value

        elif stored_data and not show_day:
            className = 'drop_down'
            value = 'min'  
          
            return False, placeholder, className, options, value

        return True, placeholder, className, options, value

##########################################################################################
###    Launch Simulation 
##########################################################################################

    @dash.callback(
        Output('payoff-msgbox', 'is_open', allow_duplicate=True),
        Output('payoff-msgbox', 'color', allow_duplicate=True),
        Output('payoff-msgbox', 'children', allow_duplicate=True),
        Output('payoff-distrib-chart', 'figure'),  
        Output('payoff-sim-chart', 'figure'),      

        Output('payoff-model-param-div', 'children'),
        Output('payoff-stats-globals-div', 'children'),
        Output('payoff-statistics-div', 'children'),

        Input('payoff-launch-sim-button', 'n_clicks'),

        State('option-selection', 'value'),
        State('options-selected-store', 'data'),
        State('payoff-mu-input', 'value'),

        State('payoff-custom-iv-switch', 'value'),
        State('payoff-sig-input', 'value'),
        State('payoff-iv-dd', 'value'),

        State('payoff-sim-exp-dd', 'value'),

        State('payoff-nbsim-dd', 'value'),
        prevent_initial_call=True,  
    )
    def launch_SimButton(n_clicks, selected_option, df, mu, switch_iv, sig_input, sig_iv, sim_exp, nbr_sim):
     
        fig = go.Figure()
        fig.add_annotation(
            text="Select options and launch simulation",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
            xref="paper",
            yref="paper"
        )
        fig.update_layout(
            title="Waiting for selection",
            template="plotly_white",
            dragmode="pan",
        )

        color = 'danger'
        message = 'Please, fill parameters before launch simulation'

        ctx = callback_context

        if not ctx.triggered:
         
            return False, color, message, fig, fig, dash.no_update, dash.no_update, dash.no_update

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if 'payoff-launch-sim-button' in triggered_id: 
            if n_clicks:

                if True in switch_iv:
                
                    sig = sig_iv
                    

                else:
                    sig = sig_input
                
                if sig and mu and len(df) > 0 and sim_exp and nbr_sim:

                    class_ = Simulation(selected_option, df, nbr_sim, mu, sig, sim_exp)

                    fig1 = class_.figure1
                    fig2 = class_.figure2

                    mu_adjusted = class_.mu
                    sig_adjusted = class_.sig
                    period = class_.T
                    n_steps = class_.n_steps

                    mean = class_.mean
                    std = class_.std
                    median = class_.median
                    percentile_5 = class_.percentile_5
                    percentile_95 = class_.percentile_95

                    max_prob = class_.max_prob
                    max_prob_range1, max_prob_range2 = class_.max_prob_range

                    min_prob = class_.min_prob
                    min_prob_range1, min_prob_range2 = class_.min_prob_range

                    max_payoff = class_.max_payoff
                    max_payoff_prob = class_.max_payoff_prob
                    min_payoff = class_.min_payoff
                    min_payoff_prob = class_.min_payoff_prob

                    positive_payoff = class_.positive_payoff
                    negative_payoff = class_.negative_payoff                    


                    global_stats = html.Div(
                        [
                            html.Span('period length (days) : ', className='stats_text'),
                            html.Br(),
                            html.Span(f'{period}', className='stats_content'),
                            html.Br(),
                            html.Span('simulation step : ', className='stats_text'),
                            html.Br(),
                            html.Span(f'{n_steps}', className='stats_content'),
                            html.Br(),
                            html.Span('µ value over period :', className='stats_text'),
                            html.Br(),
                            html.Span(f'{round(mu_adjusted * 100, 3)} %', className='stats_content'),
                            html.Br(),
                            html.Span('σ value over period :', className='stats_text'),
                            html.Br(),
                            html.Span(f'{round(sig_adjusted * 100, 3)} %', className='stats_content'),  
                        ]
                    )

                    basic_stats = html.Div(
                        [
                            html.Span('Mean : ', className='stats_text'),
                            html.Span(f'{round(mean, 2):,.2f}', className='stats_content'),
                            html.Br(),
                            html.Span('Std Dev : ', className='stats_text'),
                            html.Span(f'{round(std, 2):,.2f}', className='stats_content'),
                            html.Br(),
                            html.Span('Median : ', className='stats_text'),
                            html.Br(),
                            html.Span(f'{round(median, 2):,.2f}', className='stats_content'),
                            html.Br(),
                            html.Span('Percentile (5th) :', className='stats_text'),
                            html.Br(),
                            html.Span(f'{round(percentile_5, 2):,.2f}', className='stats_content'),
                            html.Br(),
                            html.Span('Percentile (95th) :', className='stats_text'),
                            html.Br(),
                            html.Span(f'{round(percentile_95,):,.2f}', className='stats_content'),
                            html.Br(),
                        ]
                    )

                    payoff_stats = html.Div(
                        [
                            html.Span('Max Probability : ', className='stats_text'),
                            html.Span(f'{round(max_prob * 100, 2):,.2f} %', className='stats_content'),
                            html.Br(),
                            html.Span(f'Range : {round(max_prob_range1, 2):,.2f} | {round(max_prob_range2, 2):,.2f}', className='stats_content'),
                            html.Br(),
                            html.Span('Min Probability : ', className='stats_text'),
                            html.Span(f'{round(min_prob * 100, 2):,.2f} %', className='stats_content'),
                            html.Br(),
                            html.Span(f'Range : {round(min_prob_range1, 2):,.2f} | {round(min_prob_range2, 2):,.2f}', className='stats_content'),
                            html.Br(),
                            html.Span('Max Payoff Probability : ', className='stats_text'),
                            html.Span(f'{round(max_payoff_prob * 100, 2):,.2f} %', className='stats_content'),
                            html.Br(),
                            html.Span(f'Max {round(max_payoff):,.2f}', className='stats_content'),
                            html.Br(),
                            html.Span('Min Payoff Probability : ', className='stats_text'),
                            html.Span(f'{round(min_payoff_prob * 100, 2):,.2f} %',className='stats_content'),
                            html.Br(),
                            html.Span(f'Max {round(min_payoff):,.2f}', className='stats_content'),
                            html.Br(),
                            html.Span(f'Positive Payoff : ',className='stats_text'),
                            html.Span(f'{round(positive_payoff * 100, 2):,.2f} %',className='stats_content'),
                            html.Br(),
                            html.Span(f'Negative Payoff : ',className='stats_text'),
                            html.Span(f'{round(negative_payoff * 100, 2):,.2f} %',className='stats_content'),
                        ]
                    )

                    return False, color, message, fig1, fig2, global_stats, basic_stats, payoff_stats

                else:
                    print('Inputs are invalid or missing.')
                    message = "Please, fill parameters before launch simulation"
                    return True, color, message, fig, fig, dash.no_update, dash.no_update, dash.no_update