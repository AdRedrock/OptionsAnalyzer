from datetime import datetime, time

import pandas as pd
import dask.dataframe as dd
import plotly.graph_objects as go
import dash
from dash import html, Input, Output, State, callback_context, ALL
from dash.exceptions import PreventUpdate
from functools import lru_cache

from import_data.utils import LoadingData, ConvertData

from src.analyzers.analyzer_oi import MetricsOI, VariationsOI, VolumesExpirations
from src.analyzers.analyzer_iv import IVSmileByStrike, IVDeltaSkewAsymmetry, ImpliedVolatilitySurface, IVAtmAndRealizedVolatility
from src.analyzers.analyzer_greeks import GammaExposure, DeltaExposure, VannaCumulative
from src.config.constant import PROVIDER_LIST



##########################################################################################
###    CALL-BACK GLOBAL SET-UP LAYOUT (option choosen etc...)
##########################################################################################
class GlobalSetUpLayoutCallBack:

    def __init__(self):
        pass

##########################################################################################
###   Refresh Options Tickers
##########################################################################################

    @dash.callback(
        Output('metrics-option-selection', 'options'),
        Input('import-already-imported-options-ticker-store', 'data'),
    )
    def refresh_optionsTickers(current):
        already_imported = LoadingData().load_existing_symbols()

        dropdown_options = [{"label": option, "value": option} for option in already_imported]
    
        return dropdown_options

##########################################################################################
###    CALL-BACK load main ticker date
##########################################################################################
    @dash.callback(
        Output('metrics-date-selection', 'disabled'), 
        Output('metrics-date-selection', 'className'),
        Output('metrics-date-selection', 'options'),
        Output('metrics-date-selection', 'value'),  
        Input('metrics-option-selection', 'value'),   
    )
    def update_dateTickerDropDown(selected_option):
        if selected_option is None:
            return True, 'drop_down_disabled', [], None  

        class_import = LoadingData()
        dates = class_import.load_date_imported(selected_option, hour=False, selected_date=None)
        
        sorted_dates = sorted(dates, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=True)
        options = [{"label": date, "value": date} for date in sorted_dates]

        return False, 'drop_down', options, None  

##########################################################################################
###    CALL-BACK load main ticker Hour
##########################################################################################

    @dash.callback(
        Output('metrics-date-hour-selection', 'disabled'), 
        Output('metrics-date-hour-selection', 'className'),
        Output('metrics-date-hour-selection', 'options'),
        Output('metrics-date-hour-selection', 'value'),

        Input('metrics-option-selection', 'value'), 
        Input('metrics-date-selection', 'value'),   
    )
    def update_hourImportedDropDown(selected_option, selected_date):
        if selected_date is None or selected_option is None:
            return True, 'drop_down_disabled', [], None  # Réinitialisation forcée

        class_import = LoadingData()
        hours_list = class_import.load_date_imported(selected_option, hour=True, selected_date=selected_date)

        options = ConvertData().format_hours_for_dropdown(hours_list)

        value = options[0]['value'] if options else None  

        return False, 'drop_down', options, value 


##########################################################################################
###    CALL-BACK UP-DATE GLOBAL DCC.SOTRE (reference df)
##########################################################################################
    @dash.callback( 
        Output('metrics-global-df-store', 'data'), 
        Output('metrics-option-info-store', 'data'),
        Output('metrics-custom-df-store', 'data', allow_duplicate=True),

        Output('metrics-msgbox', 'is_open'),
        Output('metrics-msgbox', 'color'),
        Output('metrics-msgbox', 'children'),
    
        Input('metrics-option-selection', 'value'),  
        Input('metrics-date-selection', 'value'), 
        Input('metrics-date-hour-selection', 'value'),
        prevent_initial_call=True,
    )
    def update_globalAndCustomStores(selected_option, selected_date, selected_hour):

        is_open = False
        color = 'danger'
        message = 'message'


        if selected_option and selected_date and selected_hour:

            underlying_ticker, change, quotation_type, quotation_type_value, lot_size = (
                LoadingData().load_st_ticker_info_json(
                    'search', 
                    selected_option
                )
            )    

            df = LoadingData().get_data_csv(selected_option, selected_date, selected_hour)

            df['expiration_bis'] = df['expiration']
        
            function = ConvertData().convert_expiration_to_day(df, selected_date, False)
 
            df['expiration'] = function

            store_ticker_info = {
                "underlying_ticker":underlying_ticker,
                "change":change,
                'quotation_type':quotation_type,
                "quotation_type_value":quotation_type_value,
                "lot_size":lot_size,
            }

            is_open = True
            color = 'info'
            message = 'Data successfully loaded!'

            store_data = df.to_dict('records')


            return store_data, store_ticker_info, dash.no_update, is_open, color, message

        return {}, {}, {}, is_open, color, message
    

    @dash.callback(
        Output('metrics-msgbox', 'is_open', allow_duplicate=True),
        Output('metrics-msgbox', 'color', allow_duplicate=True),
        Output('metrics-msgbox', 'children', allow_duplicate=True),

        Input('metrics-date-hour-selection', 'value'),
        prevent_initial_call='initial_duplicate',
    )
    def update_alertLoadingData(selected_date):

        ctx = callback_context

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if 'add-options-selection' in triggered_id:

            is_open = True
            color = 'warning'
            message = 'Data loading, please wait'

            return is_open, color, message
        return dash.no_update, dash.no_update, dash.no_update
    

@lru_cache(maxsize=1)
def get_column_definitions():
    base_columns = [
        {"headerName": "Call/Put", "field": "option_type", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Moneyness", "field": "moneyness", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Strike", "field": "strike", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Expiration", "field": "expiration", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Delta", "field": "delta", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Gamma", "field": "gamma", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Theta", "field": "theta", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Vega", "field": "vega", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Implied Vol", "field": "implied_volatility", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Volume", "field": "volume", "filter": True, "sortable": True, "resizable": True},
        {"headerName": "Open Interest", "field": "open_interest", "filter": True, "sortable": True, "resizable": True},
    ]
    
    return (
        [{"checkboxSelection": True, "headerName": "Select", "width": 10, "filter": True, "sortable": True, "resizable": True}] + base_columns,
        [{"checkboxSelection": True, "headerName": "Delete", "width": 10, "filter": True, "sortable": True, "resizable": True}] + base_columns
    )


##########################################################################################
##########################################################################################
###    TAB -> Options Selection
##########################################################################################
##########################################################################################


class MetricsOptionsSelectionCallBack:
    def __init__(self):
        self._cached_ddf = None
        self._last_trigger = None
        self._last_custom_df = None
        self._loading_state = False
        self._retry_count = 0
        self._max_retries = 3

# # #########################################################################################
# # ##    CALL-BACK DataTable
# # #########################################################################################

    def update_dataTable(
            self, 
            selected_option, selected_date, data, show_day, 
            add_clicks, del_clicks, selected_rows_to_delete, 
            selected_rows_to_add, stored_df=None
        ):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if not self._validate_inputs(selected_option, selected_date, data):
            return self._empty_response()

        try:
      
            if self._should_reload_data(trigger_id, data):
                self._loading_state = True
                success = self._load_main_dataframe(data, show_day)
                if not success:
                    return self._empty_response()

            custom_ddf = self._initialize_custom_dataframe(stored_df)
            if custom_ddf is None:
                return self._empty_response()
            
            custom_ddf = self._process_operations(
                trigger_id, 
                custom_ddf, 
                selected_rows_to_add, 
                selected_rows_to_delete
            )

            return self._compute_final_results(custom_ddf)

        except Exception as e:
            print(f"Error in update_dataTable: {e}")
            if self._retry_count < self._max_retries:
                self._retry_count += 1
                time.sleep(0.5)  
                return self.update_dataTable(
                    selected_option, selected_date, data, show_day,
                    add_clicks, del_clicks, selected_rows_to_delete,
                    selected_rows_to_add, stored_df
                )
            return self._empty_response()
        finally:
            self._loading_state = False
            self._retry_count = 0

    def _validate_inputs(self, selected_option, selected_date, data):
        """Validates basic inputs."""
        return all([
            selected_option, 
            selected_date, 
            data is not None,
            isinstance(data, (list, pd.DataFrame, dict))
        ])

    def _should_reload_data(self, trigger_id, data):
        """Determines whether master data should be reloaded."""
        return (
            self._cached_ddf is None or 
            trigger_id in ['metrics-option-selection', 'metrics-date-selection', 'metrics-global-df-store'] or
            len(self._cached_ddf.index.compute()) == 0
        )

    def _load_main_dataframe(self, data, show_day):
        """Loads the main DataFrame with error handling."""
        try:
            if isinstance(data, pd.DataFrame):
                ddf = dd.from_pandas(data, npartitions=4)
            else:
                ddf = dd.from_pandas(pd.DataFrame(data), npartitions=4)

            col_exp = 'expiration' if show_day else 'expiration_bis'
            if col_exp in ddf.columns:
                ddf['expiration'] = ddf[col_exp].copy()

            if len(ddf.index.compute()) > 0:
                self._cached_ddf = ddf
                return True
            return False

        except Exception as e:
            print(f"Error loading main DataFrame: {e}")
            return False

    def _initialize_custom_dataframe(self, stored_df):
        """Initializes custom DataFrame."""
        try:
            if stored_df is None:
                return dd.from_pandas(pd.DataFrame(), npartitions=1)

            if isinstance(stored_df, list):
                pandas_df = pd.DataFrame(stored_df)
            elif isinstance(stored_df, pd.DataFrame):
                pandas_df = stored_df
            else:
                pandas_df = pd.DataFrame(stored_df)

            return dd.from_pandas(pandas_df if not pandas_df.empty else pd.DataFrame(), npartitions=2)

        except Exception as e:
            print(f"Error initializing custom DataFrame: {e}")
            return None

    def _process_operations(self, trigger_id, custom_ddf, selected_rows_to_add, selected_rows_to_delete):
        """Handles add and delete operations."""

        if trigger_id == 'metrics-add-selection-button' and selected_rows_to_add:
            return self._process_add_operation(custom_ddf, selected_rows_to_add)
        elif trigger_id == 'metrics-del-selection-button' and selected_rows_to_delete:
            return self._process_delete_operation(custom_ddf, selected_rows_to_delete)
        return custom_ddf

    def _process_add_operation(self, custom_ddf, selected_rows_to_add):
        """Processes the add operation."""
        add_ids = {row['contract_symbol'] for row in selected_rows_to_add}
        new_rows_ddf = self._cached_ddf[self._cached_ddf['contract_symbol'].isin(add_ids)]
        
        if len(custom_ddf.index.compute()) > 0:
            custom_ddf = dd.concat([custom_ddf, new_rows_ddf])
            custom_ddf = custom_ddf.drop_duplicates(subset=['contract_symbol'])
        else:
            custom_ddf = new_rows_ddf

        self._last_custom_df = custom_ddf
        return custom_ddf

    def _process_delete_operation(self, custom_ddf, selected_rows_to_delete):
        """Processes the delete operation."""
        delete_ids = {row['contract_symbol'] for row in selected_rows_to_delete}
        if self._last_custom_df is not None:
            custom_ddf = self._last_custom_df[~self._last_custom_df['contract_symbol'].isin(delete_ids)]
        else:
            custom_ddf = custom_ddf[~custom_ddf['contract_symbol'].isin(delete_ids)]
        self._last_custom_df = custom_ddf
        return custom_ddf

    def _compute_final_results(self, custom_ddf):
        """Calculates final results with verification."""
        columnDefs_selection, columnDefs_selected = get_column_definitions()
        
        if self._cached_ddf is None or len(self._cached_ddf.index.compute()) == 0:
            return self._empty_response()

        rowData = self._cached_ddf.compute().to_dict('records')
        selected_data = custom_ddf.compute().to_dict('records')

        return (
            columnDefs_selection,
            columnDefs_selected,
            rowData,
            selected_data,
            selected_data,
            []
        )

    def _empty_response(self):
        """Returns an empty but valid response."""
        columnDefs_selection, columnDefs_selected = get_column_definitions()
        return columnDefs_selection, columnDefs_selected, [], [], [], []

metrics_callback = MetricsOptionsSelectionCallBack()

dash.callback(
    Output('metrics-selection-datatable', 'columnDefs'),
    Output('metrics-selected-datatable', 'columnDefs'),
    Output('metrics-selection-datatable', 'rowData'),
    Output('metrics-selected-datatable', 'rowData'),
    Output('metrics-custom-df-store', 'data'),
    Output('metrics-selection-datatable', 'selectedRows'),

    Input('metrics-option-selection', 'value'),
    Input('metrics-date-selection', 'value'),
    Input('metrics-global-df-store', 'data'),
    Input('metrics-show-days-switch', 'value'),
    Input('metrics-add-selection-button', 'n_clicks'),
    Input('metrics-del-selection-button', 'n_clicks'),
    State('metrics-selected-datatable', 'selectedRows'),
    State('metrics-selection-datatable', 'selectedRows'),
    State('metrics-custom-df-store', 'data')
)(metrics_callback.update_dataTable)


##########################################################################################
##########################################################################################
###    TAB -> OI & Volumes CallBack
##########################################################################################
##########################################################################################

##    OI Volumes CallBack

class OIVolumeCallBack:

    def __init__(self):
        pass

##########################################################################################
###    CALL-BACK expiration type
##########################################################################################

    @dash.callback(
            Output("metrics-peak-isolated-dd", 'disabled'),
            Output("metrics-peak-isolated-dd", 'className'),
            Output("metrics-peak-isolated-dd", 'options'),
            Output("metrics-peak-isolated-dd", 'value'),
            
            Input('metrics-option-selection', 'value'),
            Input('metrics-date-selection', 'value'),
            Input('metrics-date-hour-selection', 'value'),
            Input('metrics-custom-df-store', 'data'),
    )
    def update_selectExpirationType(selected_option, selected_date, selected_hour, custom_data):

        options=[
                {'label': 'All', 'value': 'All', 'disabled': False},
                {'label': 'Peak', 'value': 'Peak', 'disabled': False},
                {'label': 'Specific', 'value': 'Specific', 'disabled': False},
                {'label': 'Custom Selection', 'value': 'ItemChosen', 'disabled': True}
            ]

        className = 'adapt_drop_down_disabled'
        value = ''

        custom_df = pd.DataFrame(custom_data)

        if selected_option and selected_date and selected_hour:

            className = 'adapt_drop_down'
            value = 'All'

            print('VOici custom df')
            print(custom_df)
            if not custom_df.empty:

                options=[
                    {'label': 'All', 'value': 'All', 'disabled': False},
                    {'label': 'Peak', 'value': 'Peak', 'disabled': False},
                    {'label': 'Specific', 'value': 'Specific', 'disabled': False},
                    {'label': 'Custom Selection', 'value': 'ItemChosen', 'disabled': False}
                ]

            return False, className, options, value

        return True, className, options, value

##########################################################################################
###    CALL-BACK expiration list rangeSlider
##########################################################################################

    @dash.callback(
            Output('metrics-strike-oi-rgs', 'disabled'),
            Output('metrics-strike-oi-rgs', 'min'),
            Output('metrics-strike-oi-rgs', 'max'),
            Output('metrics-strike-oi-rgs', 'value'),

            Input('metrics-date-selection', 'value'),
            Input('metrics-option-selection', 'value'),
            Input('metrics-peak-isolated-dd', 'value'),
            Input('metrics-exp-oi-dd', 'value'),
            Input('metrics-global-df-store', 'data'),
            State('metrics-custom-df-store', 'data'),
            Input('metrics-show-days-switch', 'value'),
    )
    def update_rangeSlider(selected_date, selected_option, selected_exp_type, selected_exp, global_df, custom_df, show_day):
        class_LoadingData = LoadingData()

        value = []

        if not selected_exp_type or ('Peak' in selected_exp_type and not selected_exp) or ('Specific' in selected_exp_type and not selected_exp):
            return True, None, None, value
        
        if custom_df and 'ItemChosen' in selected_exp_type:
            df = pd.DataFrame(custom_df)
        else:
            df = pd.DataFrame(global_df)

        if True in show_day:
            selected_show_day = True
        else:
            selected_show_day = False
      
        if selected_option and selected_date and selected_exp_type and not df.empty:
    
            listed = list(df['strike'].unique())

            if len(listed) > 0:

                min_strike = float(min(listed))
                max_strike = float(max(listed))
                value = [min_strike, max_strike]

                return False, min_strike, max_strike, value
            
        else:
                return True, None, None, None


##########################################################################################
###    CALL-BACK List all expiration (update Params1 options)
##########################################################################################

    @dash.callback(
        Output('metrics-exp-oi-dd', 'disabled'),
        Output('metrics-exp-oi-dd', 'className'),
        Output('metrics-exp-oi-dd', 'multi'),
        Output('metrics-exp-oi-dd', 'options'), 
        Output('metrics-exp-oi-dd', 'value'),

        Input('metrics-peak-isolated-dd', 'value'),
        Input('metrics-date-selection', 'value'),
        Input('metrics-exp-oi-dd', 'value'),

        Input('metrics-option-selection', 'value'),
        Input('metrics-global-df-store', 'data'),
        Input('metrics-custom-df-store', 'data'),
        Input('metrics-show-days-switch', 'value'),
    )
    def update_expirationOIDrowDown(selected_exp_type, selected_date, exp_select, selected_option, global_data, custom_data, show_day):

        className = 'adapt_drop_down_disabled'
        list_exp = []
        options = []
        multi=False

        if exp_select and isinstance(exp_select, list) and len(exp_select) >=5:
            exp_select = exp_select[:3]

        if selected_exp_type and 'All' in selected_exp_type or 'ItemChosen' in selected_exp_type:
            return True, className, multi, options, exp_select
        
        if selected_exp_type and selected_exp_type in {'Peak', 'Specific'}:

            if selected_exp_type == 'ItemChosen':
                df = pd.DataFrame(custom_data)

            else:
                df = pd.DataFrame(global_data)

            if show_day:

                col = 'expiration' 
                list_exp = sorted(list(df[col].unique()))
                options = (
                        [{"label": f'{str(exp)} days', "value": str(exp)} for exp in list_exp]
                    )
                
            else:

                col = 'expiration_bis'
                list_exp = sorted(list(df[col].unique()))
                sorted_dates = sorted(list_exp, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=False)
                options = [{"label": date, "value": date} for date in sorted_dates]

            if selected_exp_type == 'Specific':

                multi=True
                

            className = 'adapt_drop_down'

            return False, className, multi, options, exp_select
        
        return True, className, multi, options, exp_select
        

##########################################################################################
###    CALL-BACK Open Interest Graph
##########################################################################################

    @dash.callback(
            Output("metrics-OI-vol-type-dd", 'disabled'),
            Output("metrics-OI-vol-type-dd", 'className'),
            Output("metrics-OI-vol-type-dd", 'value'),
            
            Input('metrics-option-selection', 'value'),
            Input('metrics-date-selection', 'value'),
            Input('metrics-date-hour-selection', 'value'),
    )
    def update_volumesType(selected_option, selected_date, selected_hour):


        className = 'adapt_drop_down_disabled'
        value = ''

        if selected_option and selected_date and selected_hour:

            className = 'adapt_drop_down'
            value = 'volAndOI'
            

            return False, className, value

        return True, className, value


##########################################################################################
###    CALL-BACK Open Interest Graph
##########################################################################################


    @dash.callback(
        Output('metrics-OI-chart', 'figure'),

        Output('metrics-call-vol-div', 'children'),
        Output('metrics-put-vol-div', 'children'),
        Output('metrics-ratio-vol-div', 'children'),

        Input('metrics-global-df-store', 'data'),
        State('metrics-custom-df-store', 'data'),
        Input('metrics-option-info-store', 'data'),
        Input('metrics-strike-oi-rgs', 'value'),
        Input('metrics-peak-isolated-dd', 'value'),
        Input('metrics-exp-oi-dd', 'value'),
        Input("metrics-OI-vol-type-dd", 'value'),

        Input('metrics-date-selection', 'value'),
        Input('metrics-date-hour-selection', 'value'),

        Input('metrics-show-days-switch', 'value'),
    )
    def update_graphMetrics1(strored_data, custom_data, info_data, range_strike, selected_exp_type, selected_expiration, selected_vol, selected_date, selected_hour, show_day):

        # Default plot
        fig = go.Figure()
        fig.add_annotation(
            text="Select Parameters",
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
            xaxis=dict(
                fixedrange=True
            ),
            dragmode=False,
            hovermode="x",
        )

        call_div = dash.no_update
        put_div = dash.no_update
        ratio_div = dash.no_update

        if True in show_day:
            selected_show_day = True
        else:
            selected_show_day = False

        if info_data and range_strike and selected_vol:
           
            strike_dw = range_strike[0]
            strike_up = range_strike[1]

            if custom_data and 'ItemChosen' in selected_exp_type:

                df = pd.DataFrame(custom_data)
            else:
                df = pd.DataFrame(strored_data)

            class_ = MetricsOI(df, info_data, selected_show_day, selected_date, selected_hour)

            if not selected_expiration:
                selected_expiration = []

            fig, listed_dict = class_.OIByVolumeAndStrike(strike_dw, strike_up, plot=True, type=selected_exp_type, vol_type=selected_vol, exp_selected=selected_expiration)

            call_div = html.Div(
                        [
                            html.Span('Max OI : ', className='stats_text'),
                            html.Span(f'{listed_dict["max_call"]:,.0f}', className='stats_content'),
                            html.Br(),
                            html.Span(f'Strike {listed_dict["max_call_strike"]:,.2f}', className='stats_content'),
                            html.Br(),
                            html.Br(),
                            html.Span('Median Strike: ', className='stats_text'),
                            html.Br(),
                            html.Span(f'{listed_dict["call_median"]:,.2f}', className='stats_content'),
                        ]
                    )
            
            put_div = html.Div(
                        [
                            html.Span('Max OI : ', className='stats_text'),
                            html.Span(f'{listed_dict["max_put"]:,.0f}', className='stats_content'),
                            html.Br(),
                            html.Span(f'Strike {listed_dict["max_put_strike"]:,.2f}', className='stats_content'),
                            html.Br(),
                            html.Br(),
                            html.Span('Median Strike: ', className='stats_text'),
                            html.Br(),
                            html.Span(f'{listed_dict["put_median"]:,.2f}', className='stats_content'),
                        ]
                    )
            
            ratio_div = html.Div(
                        [
                            html.Span(f'{round(listed_dict["put_call_ratio"], 2)}', className='stats_content'),
                        ]
                    )

            return fig, call_div, put_div, ratio_div
        
        return fig, call_div, put_div, ratio_div

###    OI Volumes by Expiration CallBack

class OIVolumesExpirationsCallBack:
    def __init__(self):
        pass

##########################################################################################
###    Update Volume Type
##########################################################################################
    @dash.callback(
        Output('metrics-OI-vol-type-by-exp-dd', 'disabled'),
        Output('metrics-OI-vol-type-by-exp-dd', 'className'),
        Output('metrics-OI-vol-type-by-exp-dd', 'value'),

        Input('metrics-global-df-store', 'data'),
    )
    def update_volumesType(global_data):

        disabled = True
        className = 'adapt_drop_down_disabled'
        value = ''

        if not pd.DataFrame(global_data).empty:

            disabled = False
            className = 'adapt_drop_down'
            value = 'volume'
        
        return disabled, className, value
    
##########################################################################################
###    Update Options Type
##########################################################################################
    @dash.callback(
        Output('metrics-OI-options-type-by-exp-dd', 'disabled'),
        Output('metrics-OI-options-type-by-exp-dd', 'className'),
        Output('metrics-OI-options-type-by-exp-dd', 'value'),

        Input('metrics-OI-vol-type-by-exp-dd', 'value'),
    )
    def update_optionsType(vol_type):

        disabled = True
        className = 'adapt_drop_down_disabled'
        value = ''

        if vol_type:

            disabled = False
            className = 'adapt_drop_down'
            value = 'All'
        
        return disabled, className, value

##########################################################################################
###    Update Graph
##########################################################################################
    @dash.callback(
        Output('metrics-vol-exp-chart', 'figure'),

        Input('metrics-global-df-store', 'data'),
        Input('metrics-OI-vol-type-by-exp-dd', 'value'),
        Input('metrics-OI-options-type-by-exp-dd', 'value'),
        Input('metrics-show-days-switch', 'value'),
    )
    def update_graphMetricsVolExpiration(global_data, vol_type, option_type, show_day):

        fig = go.Figure()
        fig.add_annotation(
            text="Select Parameters",
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
            dragmode=False,
        )

        df = pd.DataFrame(global_data)

        if True in show_day:
            selected_show_day = True
        else:
            selected_show_day = False

        if not df.empty and vol_type and option_type:
            fig = VolumesExpirations(selected_show_day).getVolumeByExpiration(df, vol_type, option_type)

        return fig

###    OI Variations CallBack

class OIVariationCallback:
    def __init__(self):
        pass

##########################################################################################
###    Load other date
##########################################################################################

    @dash.callback(
        Output('metrics-import-earlier-date', 'disabled'),
        Output('metrics-import-earlier-date', 'className'),
        Output('metrics-import-earlier-date', 'options'),

        Input('metrics-option-selection', 'value'),
        Input('metrics-date-selection', 'value'),
    )
    def update_importEarlierDate(selected_option, selected_date):
        
        disabled = True
        className = 'adapt_drop_down_disabled'
        options = []
        
        if selected_option and selected_date is not None:
      
            disabled = False
            className = 'adapt_drop_down'
            
            class_LoadingData = LoadingData()
            list_date = class_LoadingData.load_date_imported(selected_option)

            
            if selected_date in list_date:
                list_imported = LoadingData().load_date_imported(selected_option, hour=True, selected_date=selected_date)

                if len(list_imported) <= 1:
                    list_date.remove(selected_date)
            
            sorted_dates = sorted(list_date,
                                key=lambda date: datetime.strptime(date, "%Y-%m-%d"),
                                reverse=True)
            options = [{"label": date, "value": date} for date in sorted_dates]
                
        return disabled, className, options
    
##########################################################################################
###    Load other Hour
##########################################################################################

    @dash.callback(
        
        Output('metrics-import-earlier-hour', 'disabled'), 
        Output('metrics-import-earlier-hour', 'className'),
        Output('metrics-import-earlier-hour', 'options'),
        Output('metrics-import-earlier-hour', 'value'),

        Input('metrics-option-selection', 'value'), 
        Input('metrics-date-selection', 'value'),
        Input('metrics-import-earlier-date', 'value'),
        Input('metrics-date-hour-selection', 'value'),   
    )
    def update_importEarlierHour(selected_option, selected_date1, selected_date2, selected_hour):

        value = ''

        options = []

        if selected_date2 is None or selected_option is None:
            
            className='adapt_drop_down_disabled'
            options = []  
            return True, className, options, value
        
        class_import = LoadingData()

        hours_list = class_import.load_date_imported(selected_option, hour=True, selected_date=selected_date2)

        options = ConvertData().format_hours_for_dropdown(hours_list)

        if selected_date2 == selected_date1:
            options = [item for item in options if item['value'] != selected_hour]
       
        value = options[0]['value']

        className='adapt_drop_down'

        return False, className, options, value
    
##########################################################################################
###    Expiration Type
##########################################################################################

    @dash.callback(
            Output('metrics-peak-isolated-2-dd', 'disabled'),
            Output('metrics-peak-isolated-2-dd', 'className'),
            Output('metrics-peak-isolated-2-dd', 'options'),
            Output('metrics-peak-isolated-2-dd', 'value'),
            
            Input('metrics-option-selection', 'value'),
            Input('metrics-import-earlier-date', 'value'),
            Input('metrics-import-earlier-hour', 'value'),
            Input('metrics-custom-df-store', 'data'),
    )
    def update_expirationOItype2(selected_option, selected_date, selected_hour, custom_df):

        options=[
                {'label': 'All', 'value': 'All', 'disabled': False},
                {'label': 'Peak', 'value': 'Peak', 'disabled': False},
                {'label': 'Specific', 'value': 'Specific', 'disabled': False},
            ]

        className = 'adapt_drop_down_disabled'
        value = ''

        if selected_option and selected_date and selected_hour:

            className = 'adapt_drop_down'
            value = 'All'

            return False, className, options, value

        return True, className, options, value
    

##########################################################################################
###    Expiration Expiration Filter
##########################################################################################

    @dash.callback(
        Output('metrics-exp-oi-2-dd', 'disabled'),
        Output('metrics-exp-oi-2-dd', 'className'),
        Output('metrics-exp-oi-2-dd', 'options'),
        Output('metrics-exp-oi-2-dd', 'multi'),
        Output('metrics-exp-oi-2-dd', 'value'),

        Output('metrics-global-var1-df-store', 'data'), 
        Output('metrics-global-var2-df-store', 'data'), 

        Input('metrics-peak-isolated-2-dd', 'value'),
        Input('metrics-import-earlier-date', 'value'),
        Input('metrics-import-earlier-hour', 'value'),
        Input('metrics-option-selection', 'value'),
        Input('metrics-show-days-switch', 'value'),
        Input('metrics-global-df-store', 'data'), 
        Input('metrics-exp-oi-2-dd', 'value'),
    )
    def update_expirationOIDrowDown2(selected_exp_type, selected_date2, selected_hour2, selected_option, show_day, stored_data, exp_select):

        className = 'adapt_drop_down_disabled'
        list_exp = []
        options = []
        multi=False

        if exp_select and isinstance(exp_select, list) and len(exp_select) >=5:
            exp_select = exp_select[:3]

        if selected_date2 and selected_hour2:

            df1 = pd.DataFrame(stored_data) 
            df2 = LoadingData().get_data_csv(selected_option, selected_date2, selected_hour2) 

            function = ConvertData().convert_expiration_to_day(df2, selected_date2, False)
            df2['expiration_bis'] = df2['expiration']
            df2['expiration'] = function

            stored_data_var_1 = df1.to_dict('records') 
            stored_data_var_2 = df2.to_dict('records')            

            if selected_exp_type and 'All' in selected_exp_type:

                return True, className, [], multi, exp_select, stored_data_var_1, stored_data_var_2

            
            if selected_exp_type and ('Peak' in selected_exp_type or 'Specific' in selected_exp_type):

                className = 'adapt_drop_down'
                class_ConvertData = ConvertData()

                list_exp1 = list(df1['strike'].unique())
                list_exp2 = list(df2['strike'].unique())

                list_exp = list(set(list_exp1) & set(list_exp2))
                df1_filtered = df1[df1['strike'].isin(list_exp)].copy()
            
                if show_day:
                    col = 'expiration' 
                    
                    list_exp_filtered = sorted(list(df1_filtered[col].unique()))
                    options = (
                            [{"label": f'{str(exp)} days', "value": str(exp)} for exp in list_exp_filtered]
                        )
                
                else:

                    col = 'expiration_bis'
                    list_exp_filtered = sorted(list(df1_filtered[col].unique()))
                    sorted_dates = sorted(list_exp_filtered, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=False)
                    options = [{"label": date, "value": date} for date in sorted_dates]

                if selected_exp_type == 'Specific':

                    multi=True
                    

                className = 'adapt_drop_down'

                return False, className, options, multi, exp_select, stored_data_var_1, stored_data_var_2
        
        return True, className, options, multi, exp_select, [], []





##########################################################################################
###    CALL-BACK expiration list rangeSlider
##########################################################################################

    @dash.callback(
            Output('metrics-strike-oi-2-rgs', 'disabled'),
            Output('metrics-strike-oi-2-rgs', 'min'),
            Output('metrics-strike-oi-2-rgs', 'max'),
            Output('metrics-strike-oi-2-rgs', 'value'),

            Input('metrics-global-var2-df-store', 'data'),
            Input('metrics-custom-df-store', 'data'),
            Input('metrics-import-earlier-date', 'value'),
            Input('metrics-option-selection', 'value'),
            Input('metrics-peak-isolated-2-dd', 'value'),
            Input('metrics-exp-oi-2-dd', 'value'),
    )
    def update_rangeSlider2(stored_data, custom_df, selected_date, selected_option, selected_exp_type, selected_exp):

        value = []

        if not selected_exp_type or ('Peak' in selected_exp_type and not selected_exp) or ('Specific' in selected_exp_type and not selected_exp):
            return True, None, None, value
        
        if custom_df and 'ItemChosen' in selected_exp_type:
            df = pd.DataFrame(custom_df)
        else:
            df = pd.DataFrame(stored_data)

        if selected_option and selected_date and selected_exp_type and not df.empty:
    
            listed = list(df['strike'].unique())

            min_strike = float(min(listed))
            max_strike = float(max(listed))
            value = [min_strike, max_strike]

            return False, min_strike, max_strike, value
            
        else:
            return True, None, None, None



##########################################################################################
###    CALL-BACK Open Interest Variation
##########################################################################################

    @dash.callback(
            Output("metrics-OI-vol-type-2-dd", 'disabled'),
            Output("metrics-OI-vol-type-2-dd", 'className'),
            Output("metrics-OI-vol-type-2-dd", 'value'),
            
            Input('metrics-option-selection', 'value'),
            Input('metrics-date-selection', 'value'),
            Input('metrics-import-earlier-hour', 'value'),
    )
    def update_volumesType(selected_option, selected_date, selected_hour):

        className = 'adapt_drop_down_disabled'
        value = ''

        if selected_option and selected_date and selected_hour:

            className = 'adapt_drop_down'
            value = 'volAndOI'
            
            return False, className, value

        return True, className, value


##########################################################################################
###    CALL-BACK Open Interest Variation
##########################################################################################

    @dash.callback(
        Output('metrics-OI-call-chart', 'figure'),
        Output('metrics-OI-put-chart', 'figure'),

        Output('metrics-info-call-var-div', 'children'),
        Output('metrics-info-put-var-div', 'children'),

        Input('metrics-global-var1-df-store', 'data'),
        Input('metrics-global-var2-df-store', 'data'),
        Input('metrics-custom-df-store', 'data'),

        Input('metrics-option-info-store', 'data'),
        Input('metrics-strike-oi-2-rgs', 'value'),
        Input('metrics-peak-isolated-2-dd', 'value'),
        Input('metrics-exp-oi-2-dd', 'value'),
        Input("metrics-OI-vol-type-2-dd", 'value'),

        Input('metrics-show-days-switch', 'value'),

        State('metrics-date-selection', 'value'),
        State('metrics-import-earlier-date', 'value'),
        Input('metrics-date-hour-selection', 'value'),
        Input('metrics-import-earlier-hour', 'value'),
    )
    def update_graphMetricsCallPut2(strored_data1, strored_data2, custom_data, info_data, range_strike, selected_exp_type, selected_expiration, selected_vol, show_day, date1, date2, selected_hour1, selected_hour2):

        # Default plot
        fig = go.Figure()
        fig.add_annotation(
            text="Select Parameters",
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
            dragmode=False,
        )

        fig_call = fig
        fig_put = fig

        call_info_div = dash.no_update
        put_info_div = dash.no_update

        if True in show_day:
            selected_show_day = True
        else:
            selected_show_day = False

        if info_data and range_strike and selected_vol:

            strike_dw = range_strike[0]
            strike_up = range_strike[1]


            if custom_data and 'ItemChosen' in selected_exp_type:

                df1 = pd.DataFrame(custom_data)
            else:
                df1 = pd.DataFrame(strored_data1)

            df2 = pd.DataFrame(strored_data2)

            class_ = VariationsOI(info_data, df1, df2, date1, date2, selected_hour1, selected_hour2, selected_show_day)

            if not selected_expiration:
                selected_expiration = None

            fig_call, call_info = class_.variation(strike_dw, strike_up, option_type='call', plot=True, type=selected_exp_type, vol_type=selected_vol,exp_selected=selected_expiration)
            fig_put, put_info = class_.variation(strike_dw, strike_up, option_type='put', plot=True, type=selected_exp_type, vol_type=selected_vol,exp_selected=selected_expiration)

            if call_info:

                call_info_div = html.Div(
                            [
                                html.Span('Max OI variation : ', className='stats_text'),
                                html.Br(),
                                html.Span(f'Strike {call_info["max_var_strike"]:,.0f}', className='stats_content'),
                                html.Br(),
                                html.Span(f'{round(call_info["max_var"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Br(),
                                html.Span('Min OI variation : ', className='stats_text'),
                                html.Br(),
                                html.Span(f'Strike {call_info["min_var_strike"]:,.0f}', className='stats_content'),
                                html.Br(),
                                html.Span(f'{round(call_info["min_var"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Br(),
                                html.Span('Mean : ', className='stats_text'),
                                html.Span(f'{round(call_info["mean"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Span('Std : ', className='stats_text'),
                                html.Span(f'{round(call_info["std"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Span('Median : ', className='stats_text'),
                                html.Span(f'{round(call_info["median"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Span('St Variation : ', className='stats_text'),
                                html.Span(f'{round(call_info["st_var"], 4):,.4f} %', className='stats_content'),
                            ]
                        )
            else:
                call_info = dash.no_update

            if put_info:
                
                put_info_div = html.Div(
                            [
                                html.Span('Max OI variation : ', className='stats_text'),
                                html.Br(),
                                html.Span(f'Strike {put_info["max_var_strike"]:,.0f}', className='stats_content'),
                                html.Br(),
                                html.Span(f'{round(put_info["max_var"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Br(),
                                html.Span('Min OI variation : ', className='stats_text'),
                                html.Br(),
                                html.Span(f'Strike {put_info["min_var_strike"]:,.0f}', className='stats_content'),
                                html.Br(),
                                html.Span(f'{round(put_info["min_var"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Br(),
                                html.Span('Mean : ', className='stats_text'),
                                html.Span(f'{round(put_info["mean"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Span('Std : ', className='stats_text'),
                                html.Span(f'{round(put_info["std"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Span('Median : ', className='stats_text'),
                                html.Span(f'{round(put_info["median"], 2):,.2f} %', className='stats_content'),
                                html.Br(),
                                html.Span('St Variation : ', className='stats_text'),
                                html.Span(f'{round(put_info["st_var"], 4):,.4f} %', className='stats_content'),
                            ]
                        )
                
            else:
               put_info = dash.no_update
                    
        
        return fig_call, fig_put, call_info_div, put_info_div


#########################################################################################
#########################################################################################
##    TAB -> Implied Volatility CallBack
#########################################################################################
#########################################################################################

##    IVSmileStrikeLayoutCallBack

class IVSmileStrikeLayoutCallBack:
    def __init__(self):
        pass


##########################################################################################
###    CALL-BACK Expirations Type DropDown
##########################################################################################

    @dash.callback(
            Output('metrics-select-type-IV-1-dd', 'disabled'),
            Output('metrics-select-type-IV-1-dd', 'className'),
            Output('metrics-select-type-IV-1-dd', 'options'),
            Output('metrics-select-type-IV-1-dd', 'value'),
            
            Input('metrics-global-df-store', 'data'),
            Input('metrics-custom-df-store', 'data'),
    )
    def update_selectionTypeIV1(global_df, custom_df):
    
        disabled = True
        className = 'adapt_drop_down_disabled'
        options = [
            {'label': 'Specific', 'value': 'Specific', 'disabled': False},
            {'label': 'Custom Selection', 'value': 'ItemChosen', 'disabled': True}
        ]
        
        value = ''

        if global_df:
            disabled = False
            className = 'adapt_drop_down'

            value = 'Specific'

            if custom_df:
             
                options[1]['disabled'] = False  
        
        return disabled, className, options, value


##########################################################################################
###    CALL-BACK Expirations DropDown 1
##########################################################################################

    @dash.callback(
            Output('metrics-exp-IV-1-dd', 'disabled'),
            Output('metrics-exp-IV-1-dd', 'className'),
            Output('metrics-exp-IV-1-dd', 'options'),
            Output('metrics-exp-IV-1-dd', 'value'),

            Input('metrics-option-selection', 'value'),
            Input('metrics-select-type-IV-1-dd', 'value'),

            Input('metrics-global-df-store', 'data'),
            Input('metrics-custom-df-store', 'data'),
            Input('metrics-show-days-switch', 'value'),
            Input('metrics-exp-IV-1-dd', 'value'),
    )
    def update_expirationIVDrowDown1(selected_option, selected_exp_type, global_data, custom_data, show_day, exp_select):
        className = 'adapt_drop_down_disabled'
        list_exp = []
        options = []

        if exp_select and isinstance(exp_select, list) and len(exp_select) >=5:
            exp_select = exp_select[:3]

        
        if selected_exp_type and selected_exp_type in {'Specific', 'ItemChosen'}:

            if selected_exp_type == 'ItemChosen':
                df_custom = pd.DataFrame(custom_data)

                df_global = pd.DataFrame(global_data)

                mask = df_custom.isin(df_global['dte'])
                df = df_global[mask].copy()

                print(df)

            else:

                df = pd.DataFrame(global_data)

            if show_day:

                col = 'dte' 
                list_exp = sorted(list(df[col].unique()))
                options = (
                        [{"label": f'{str(exp)} days', "value": str(exp)} for exp in list_exp]
                    )
                
            else:

                col = 'expiration_bis'
                list_exp = sorted(list(df[col].unique()))
                sorted_dates = sorted(list_exp, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=False)
                options = [{"label": date, "value": date} for date in sorted_dates]

            if exp_select is None and options:
                exp_select = [options[0]['value']]
                
            className = 'adapt_drop_down'

            return False, className, options, exp_select
        
        return True, className, options, exp_select
    
##########################################################################################
###    CALL-BACK Expirations DropDown 2
##########################################################################################

    @dash.callback(
            Output('metrics-exp-IV-2-dd', 'disabled'),
            Output('metrics-exp-IV-2-dd', 'className'),
            Output('metrics-exp-IV-2-dd', 'options'),
            Output('metrics-exp-IV-2-dd', 'value'),

            Input('metrics-option-selection', 'value'),

            Input('metrics-global-iv-smile-df-store', 'data'),
            Input('metrics-show-days-switch', 'value'),
            Input('metrics-exp-IV-2-dd', 'value'),
    )
    def update_expirationIVDrowDown2(selected_option, global_data, show_day, exp_select):
        className = 'adapt_drop_down_disabled'
        list_exp = []
        options = []

        df = pd.DataFrame(global_data)

        if exp_select and isinstance(exp_select, list) and len(exp_select) >=5:
            exp_select = exp_select[:3]

        
        if not df.empty:

            if show_day:

                col = 'expiration' 
                list_exp = sorted(list(df[col].unique()))
                options = (
                        [{"label": f'{str(exp)} days', "value": str(exp)} for exp in list_exp]
                    )
                
            else:

                col = 'expiration_bis'
                list_exp = sorted(list(df[col].unique()))
                sorted_dates = sorted(list_exp, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=False)
                options = [{"label": date, "value": date} for date in sorted_dates]

                
            className = 'adapt_drop_down'

            return False, className, options, exp_select
        
        return True, className, options, exp_select
    
##########################################################################################
###    Load other date IV
##########################################################################################

    @dash.callback(
        Output('metrics-import-earlier-date-IV', 'disabled'),
        Output('metrics-import-earlier-date-IV', 'className'),
        Output('metrics-import-earlier-date-IV', 'options'),

        Input('metrics-option-selection', 'value'),
        Input('metrics-date-selection', 'value'),
        Input('metrics-exp-IV-1-dd', 'value'),
    )
    def update_importEarlierDate(selected_option, selected_date, exp_list1):
        
        disabled = True
        className = 'adapt_drop_down_disabled'
        options = []
        
        if selected_option and selected_date and exp_list1:
      
            disabled = False
            className = 'adapt_drop_down'
            
            class_LoadingData = LoadingData()
            list_date = class_LoadingData.load_date_imported(selected_option)

            if selected_date in list_date:
                list_imported = LoadingData().load_date_imported(selected_option, hour=True, selected_date=selected_date)

                if len(list_imported) <= 1:
                    list_date.remove(selected_date)
            
            sorted_dates = sorted(list_date,
                                key=lambda date: datetime.strptime(date, "%Y-%m-%d"),
                                reverse=True)
            options = [{"label": date, "value": date} for date in sorted_dates]
                
        return disabled, className, options
    
##########################################################################################
###    Load other Hour
##########################################################################################

    @dash.callback(
        Output('metrics-import-earlier-hour-IV', 'disabled'), 
        Output('metrics-import-earlier-hour-IV', 'className'),
        Output('metrics-import-earlier-hour-IV', 'options'),
        Output('metrics-import-earlier-hour-IV', 'value'),

        Input('metrics-option-selection', 'value'), 
        Input('metrics-date-selection', 'value'),
        Input('metrics-import-earlier-date-IV', 'value'),
        Input('metrics-date-hour-selection', 'value'),   
    )
    def update_importEarlierHour(selected_option, selected_date1, selected_date2, selected_hour):

        value = ''
        options = []

        if selected_date2 is None or selected_option is None:
            
            className='adapt_drop_down_disabled'
            options = []  
            return True, className, options, value
        
        class_import = LoadingData()

        hours_list = class_import.load_date_imported(selected_option, hour=True, selected_date=selected_date2)

        options = ConvertData().format_hours_for_dropdown(hours_list)

        if selected_date2 == selected_date1:
            options = [item for item in options if item['value'] != selected_hour]

        className='adapt_drop_down'

        return False, className, options, value

##########################################################################################
###    Get variation volatility Skew dataframe
##########################################################################################

    @dash.callback(
        Output('metrics-global-iv-smile-df-store', 'data'),

        Input('metrics-option-selection', 'value'), 
        Input('metrics-import-earlier-date-IV', 'value'),
        Input('metrics-import-earlier-hour-IV', 'value'),
    )
    def update_getCompareDataFrame(selected_option, selected_date, selected_hour):

        store_data = {}

        if selected_option and selected_date and selected_hour:

            df = LoadingData().get_data_csv(selected_option, selected_date, selected_hour)

            df['expiration_bis'] = df['expiration']
        
            function = ConvertData().convert_expiration_to_day(df, selected_date, False)
 
            df['expiration'] = function

            store_data = df.to_dict('records')

        return store_data

    
##########################################################################################
###    CALL-BACK Show IV Smile
##########################################################################################

    @dash.callback(
        Output('metrics-IV-strike-chart', 'figure'),

        Input('metrics-option-selection', 'value'),
        Input('metrics-date-selection', 'value'),
        Input('metrics-import-earlier-date-IV', 'value'),

        Input('metrics-date-hour-selection', 'value'),
        Input('metrics-import-earlier-hour-IV', 'value'),

        Input('metrics-exp-IV-1-dd', 'value'),
        Input('metrics-exp-IV-2-dd', 'value'),

        Input('metrics-global-df-store', 'data'),
        Input('metrics-global-iv-smile-df-store', 'data'),
        State('metrics-option-info-store', 'data'),

        Input('metrics-smooth-methods-IV-dd', 'value'),
        Input('metrics-moneyness-IV-dd', 'value'),
        Input('metrics-show-days-switch', 'value'),
        Input('metrics-st-selection-1-switch', 'value')
    )
    def update_ivGraphs(selected_option, selected_date1, selected_date2, selected_hour1, selected_hour2, exp_list1, exp_list2, global_data, var_data, info, smooth, moneyness, show_day, st_switch):

        fig = go.Figure()
        fig.add_annotation(
            text="Select at least one expiration",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
            xref="paper",
            yref="paper"
        )
        fig.update_layout(
            title="Waiting for selection",
            template="plotly_white"
        )

        if True in show_day:
            selected_show_day = True
        else:
            selected_show_day = False
        
        st_on_imported = True if True in st_switch else False

        global_df = pd.DataFrame(global_data)
        var_df = pd.DataFrame(var_data)

        variation_dates = False

        if not selected_option or not selected_date1 or not info:
            return  fig
        
        if exp_list1 and not global_df.empty:

            if exp_list2 and not var_df.empty:
                variation_dates = True
            else:
                exp_list2 = []

            class_ = IVSmileByStrike(
                selected_option=selected_option,
                selected_date=selected_date1,
                selected_date2=selected_date2,
                selected_hour=selected_hour1,
                selected_hour2=selected_hour2,
                info=info,
                exp_list=exp_list1,
                exp_list2=exp_list2,
                show_day=selected_show_day,
                variation_dates=variation_dates
            )
            fig = class_.smileFunction(global_df, var_df, True, moneyness, smooth, st_on_imported)
            
        return fig

##    IVDeltaSkewMetricsCallBack

class IVDeltaSkewMetricsCallBack:
    def __init__(self):
        pass

##########################################################################################
###    CALL-BACK Informations
##########################################################################################

    @dash.callback(
        Output("metrics-IV-indicator-toast", "is_open"),
        [Input("metrics-IV-indicator-button", "n_clicks")],
    )
    def open_toast(n):
        if n == 0:
            return dash.no_update
        return True



##########################################################################################
###    CALL-BACK Formula
##########################################################################################
    @dash.callback(
        Output('metrics-dskew-formula-IV-dd', 'disabled'),
        Output('metrics-dskew-formula-IV-dd', 'className'),
        Output('metrics-dskew-formula-IV-dd', 'value'),

        Input('metrics-global-df-store', 'data'),
    )
    def update_selectFormula(global_data):

        disabled = True
        className = 'adapt_drop_down_disabled'
        value=''

        df = pd.DataFrame(global_data)

        if not df.empty:

            disabled = False
            className = 'adapt_drop_down'
            value='deltaSkew30'

        return disabled, className, value


##########################################################################################
###    CALL-BACK Max History
##########################################################################################
    @dash.callback(
        Output('metrics-max-history-dskew-IV-dd', 'disabled'),
        Output('metrics-max-history-dskew-IV-dd', 'className'),
        Output('metrics-max-history-dskew-IV-dd', 'options'),
        Output('metrics-max-history-dskew-IV-dd', 'value'),

        Input('metrics-dskew-formula-IV-dd', 'value'),
        Input('metrics-option-selection', 'value'), 
        Input('metrics-date-selection', 'value'),
    )
    def update_selectFormula(selected_formula, selected_option, selected_date):

        disabled = True
        className = 'adapt_drop_down_disabled'
        options = []
        value=''

        if selected_formula and selected_formula != 'ivDeltaSkewSpread':

            disabled = False
            className = 'adapt_drop_down'
            value=''

            selected_date = datetime.strptime(selected_date, "%Y-%m-%d")
            dates = LoadingData().load_date_imported(selected_option)

            filtered_dates = [
                date for date in dates if datetime.strptime(date, "%Y-%m-%d") <= selected_date
            ]

            sorted_dates = sorted(filtered_dates, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=True)
            options = [{"label": date, "value": date} for date in sorted_dates]

            value = sorted_dates[-1] if sorted_dates else None

        return disabled, className, options, value
    
    
    ##########################################################################################
    ###    Plot delta
    ##########################################################################################
    @dash.callback(
        Output('metrics-IV-delta-dskew-chart', 'figure'),

        Input('metrics-global-df-store', 'data'),

        Input('metrics-option-selection', 'value'),
        Input('metrics-date-selection', 'value'),
        Input('metrics-date-hour-selection', 'value'),

        Input('metrics-show-days-switch', 'value'),
        Input('metrics-dskew-formula-IV-dd', 'value'),
        Input('metrics-max-history-dskew-IV-dd', 'value'),
        Input('metrics-option-info-store', 'data'),
    )
    def update_graphMetricsIvDeltaSkewStrike(global_data, selected_option, selected_date, selected_hour, show_day, selected_formula, max_date, info):

        fig = go.Figure()
        fig.add_annotation(
            text="Select the parameters to display the graph.",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
            xref="paper",
            yref="paper"
        )
        fig.update_layout(
            title="Waiting for selection",
            template="plotly_white"
        )

        selected_show_day = any(show_day)

        df = pd.DataFrame(global_data)

        if selected_formula:

            class_IVAtmAndRealizedVolatility = IVAtmAndRealizedVolatility(selected_option, selected_date, selected_hour, max_date, info)
            class_IVDeltaSkewAsymmetry = IVDeltaSkewAsymmetry(selected_option, selected_date, selected_hour, max_date, info)

            if selected_formula == 'IVvsRV30':
                fig = class_IVAtmAndRealizedVolatility.getRealizedVolatility30(True)

            if selected_formula == 'IVvsRVclosest':
                fig = class_IVAtmAndRealizedVolatility.getRealizedVolatilityNearest(True)

            if selected_formula == 'deltaSkew30':
                fig = class_IVDeltaSkewAsymmetry.getDeltaSkewOptions(indicator_exp='30', delta_targeted= 0.25, skew_type='classic', plot=True)
            if selected_formula == 'bfDeltaSkew30':
                fig = class_IVDeltaSkewAsymmetry.getDeltaSkewOptions(indicator_exp='30', delta_targeted= 0.25, skew_type='butterfly', plot=True)
      

        return fig

        
###    IVSurfaceLayoutCallBack

class IVSurfaceLayoutCallBack:
    def __init__(self):
        pass

##########################################################################################
###    CALL-BACK Expirations Type DropDown
##########################################################################################

    @dash.callback(
            Output('metrics-surface-exp-type-IV-dd', 'disabled'),
            Output('metrics-surface-exp-type-IV-dd', 'className'),
            Output('metrics-surface-exp-type-IV-dd', 'options'),
            Output('metrics-surface-exp-type-IV-dd', 'value'),
            
            Input('metrics-global-df-store', 'data'),
            Input('metrics-custom-df-store', 'data'),
    )
    def update_selectionTypeSurfaceIV(global_df, custom_df):
    
        disabled = True
        className = 'adapt_drop_down_disabled'

        options=[
                {"label": 'All', "value": 'All', 'disabled': False},
                {"label": 'Peak', "value": 'Peak', 'disabled': False},
            ]
        
        value = ''

        if global_df:
            disabled = False
            className = 'adapt_drop_down'

            value = 'All'

            if custom_df:
                df = pd.DataFrame(custom_df)
                list_strike = list(df['strike'].unique())

                if len(list_strike) >= 5:
                    options[1]['disabled'] = False  
        
        return disabled, className, options, value
    
# ##########################################################################################
# ###    Expiration Expiration Filter
# ##########################################################################################


    @dash.callback(
        Output('metrics-surface-exp-IV-dd', 'disabled'),
        Output('metrics-surface-exp-IV-dd', 'className'),
        Output('metrics-surface-exp-IV-dd', 'options'),
       

        Input('metrics-surface-exp-type-IV-dd', 'value'),
        Input('metrics-global-df-store', 'data'),
        Input('metrics-show-days-switch', 'value'),
    )
    def update_surfaceExpirationFilter(selected_exp_type, global_data, show_day):

        disabled = True
        className = 'adapt_drop_down_disabled'

        options=[]
        list_exp = []
        
        if 'Peak' in selected_exp_type:

            df = pd.DataFrame(global_data)

            if show_day:

                col = 'expiration' 
                list_exp = sorted(list(df[col].unique()))
                options = (
                        [{"label": f'{str(exp)} days', "value": str(exp)} for exp in list_exp]
                    )
                
            else:

                col = 'expiration_bis'
                list_exp = sorted(list(df[col].unique()))
                sorted_dates = sorted(list_exp, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=False)
                options = [{"label": date, "value": date} for date in sorted_dates]

            disabled = False
            className = 'adapt_drop_down'
            

        return disabled, className, options
    
# ##########################################################################################
# ###    Call Or Put Filter
# ##########################################################################################

    @dash.callback(
        Output('metrics-surface-options-type-IV-dd', 'disabled'),
        Output('metrics-surface-options-type-IV-dd', 'className'),
        Output('metrics-surface-options-type-IV-dd', 'options'),
        Output('metrics-surface-options-type-IV-dd', 'value'),

        Input('metrics-surface-exp-type-IV-dd', 'value'),
        Input('metrics-global-df-store', 'data'),
        Input('metrics-custom-df-store', 'data'),
    )
    def update_selectOptionTypeIV(selected_type, global_df, custom_df):
 
        disabled = True
        className = 'adapt_drop_down_disabled'
        options = [
            {"label": 'Call', "value": 'call', 'disabled': False},
            {"label": 'Put', "value": 'put', 'disabled': False},
            {"label": 'Both (Mean)', "value": 'mean', 'disabled': False},
        ]

        value = 'call'

        if selected_type and ('All' in selected_type or 'Peak' in selected_type):
            disabled = False
            className = 'adapt_drop_down'

        elif selected_type and 'Custom Selection' in selected_type:

            if custom_df:
                df = pd.DataFrame(custom_df)

                if 'option_type' in df.columns:
                
                    has_put = 'put' in df['option_type'].values
                    has_call = 'call' in df['option_type'].values

                    options[0]['disabled'] = not has_call  
                    options[1]['disabled'] = not has_put   
                    options[2]['disabled'] = not (has_call and has_put)  

                    disabled = False
                    className = 'adapt_drop_down'

        return disabled, className, options, value
    
# ##########################################################################################
# ###    SURFACE RANGE SLIDER 
# ##########################################################################################

    @dash.callback(
        Output('metrics-surface-IV-rgs', 'disabled'),
        Output('metrics-surface-IV-rgs', 'min'),
        Output('metrics-surface-IV-rgs', 'max'),
        Output('metrics-surface-IV-rgs', 'value'),

        Input('metrics-surface-exp-type-IV-dd', 'value'),
        Input('metrics-surface-exp-IV-dd', 'value'),
        Input('metrics-surface-options-type-IV-dd', 'value'),

        Input('metrics-global-df-store', 'data'),
        State('metrics-custom-df-store', 'data'),
        State('metrics-show-days-switch', 'value')  
    )
    def update_range_surface_slider(selected_exp_type, selected_exp, selected_option_type, global_data, custom_data, show_day):

        if custom_data and 'ItemChosen' in selected_exp_type:
            df = pd.DataFrame(custom_data)
        else:
            df = pd.DataFrame(global_data)

        if True in show_day and selected_exp and not df.empty:  
            col = 'expiration'
            
            df['expiration'] = df['expiration'].astype(int)
            selected_exp = int(selected_exp)

        elif False in show_day and not df.empty:
            col = 'expiration_bis'

        elif df.empty:
            return True, None, None, []

        if selected_option_type and 'mean' in selected_option_type:
          
            if {'strike', 'option_type', col}.issubset(df.columns):
                df = df[df['strike'].notnull() & (df['option_type'] == 'put') & (df[col].isin(df[df['option_type'] == 'call'][col]))]
            else:
                return True, None, None, []
        else:
      
            df = df[df['option_type'] == selected_option_type]

   
        if selected_exp_type and 'All' in selected_exp_type:

            min_strike = float(df['strike'].min())
            max_strike = float(df['strike'].max())
            value = [min_strike, max_strike]

            return False, min_strike, max_strike, value

        if selected_exp_type and 'Peak' in selected_exp_type and selected_exp is not None and not df.empty:
 
            if df.empty:
                return True, None, None, []

            else:
                
                df = df[df[col] <= selected_exp]

                min_strike = float(df['strike'].min())
                max_strike = float(df['strike'].max())
                value = [min_strike, max_strike]
                return False, min_strike, max_strike, value

        if not selected_exp_type or ('Peak' in selected_exp_type and not selected_exp) or ('Specific' in selected_exp_type and not selected_exp):
        
            return True, None, None, []

        return True, None, None, []


# ##########################################################################################
# ###    Plot Surface
# ##########################################################################################

    @dash.callback(
        Output('metrics-IV-surface-chart', 'figure'),
        
        Input('metrics-date-selection', 'value'),
        Input('metrics-surface-exp-type-IV-dd', 'value'),
        Input('metrics-surface-exp-IV-dd', 'value'),
        Input('metrics-surface-options-type-IV-dd', 'value'),

        Input('metrics-global-df-store', 'data'),
        Input('metrics-custom-df-store', 'data'),

        Input('metrics-surface-IV-rgs', 'value'),
        Input('metrics-option-info-store', 'data'),
    )
    def update_graphMetricsIvSurface(selected_date, selected_type, selected_exp, selected_option_type, global_data, custom_data, range_slider, info):

        fig = go.Figure()
        fig.add_annotation(
            text="Select Parameters",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
            xref="paper",
            yref="paper"
        )
        fig.update_layout(
            title="Waiting for selection",
            template="plotly_white"
        )

        global_df = pd.DataFrame(global_data)
        custom_df = pd.DataFrame(custom_data)

        if range_slider and selected_type and not global_df.empty and selected_option_type:

            if not selected_exp:
                selected_exp = None
        
            strike_dw = range_slider[0]
            strike_up = range_slider[1]

            class_ = ImpliedVolatilitySurface(selected_date, info)
            fig = class_.surfaceCalculation(global_df, custom_df, strike_dw, strike_up, selected_type, selected_option_type, selected_exp, True)


        return fig
    
#########################################################################################
#########################################################################################
##    TAB -> Greeks CallBack
#########################################################################################
#########################################################################################


class GreeksGEXLayoutCallBack:
    def __init__(self):
        pass

##########################################################################################
###    CALL-BACK Expirations Type & VOl Type DropDown
##########################################################################################

    @dash.callback(
        Output('metrics-GEX-vol-type-dd', 'disabled'),
        Output('metrics-GEX-vol-type-dd', 'className'),
        Output('metrics-GEX-vol-type-dd', 'value'),

        Output('metrics-exp-type-GEX-dd', 'disabled'),
        Output('metrics-exp-type-GEX-dd', 'className'),
        Output('metrics-exp-type-GEX-dd', 'options'),
        Output('metrics-exp-type-GEX-dd', 'value'),

        Input('metrics-option-selection', 'value'),
        Input('metrics-date-selection', 'value'),
        Input('metrics-global-df-store', 'data'),
        Input('metrics-custom-df-store', 'data'),
    )
    def update_selectionGex(selected_option, selected_date, global_data, custom_data):

        custom_df = pd.DataFrame(custom_data) 
        global_df = pd.DataFrame(global_data) 

        options = []
        
        if selected_option and selected_date and not global_df.empty:

            options = [
                {"label": 'All', "value": 'All', 'disabled': False},
                {"label": 'Peak', "value": 'Peak', 'disabled': False},
                {"label": 'Specific', "value": 'Specific', 'disabled': False},
                {"label": 'Custom', "value": 'ItemChosen', 'disabled': True}
            ]

            if not custom_df.empty:
                options[3]['disabled'] = False  
            
            return (
                False, 'adapt_drop_down', 'volume',
                False, 'adapt_drop_down', options, 'All'
            )
        
        return (
            True, 'adapt_drop_down_disabled', '', 
            True, 'adapt_drop_down_disabled', options,''
        )
        
    
# ##########################################################################################
# ###    Expiration Expiration Filter
# ##########################################################################################


    @dash.callback(
        Output('metrics-exp-select-GEX-dd', 'disabled'),
        Output('metrics-exp-select-GEX-dd', 'className'),
        Output('metrics-exp-select-GEX-dd', 'multi'),
        Output('metrics-exp-select-GEX-dd', 'options'),
        Output('metrics-exp-select-GEX-dd', 'value'),
       
        Input('metrics-exp-type-GEX-dd', 'value'),
        Input('metrics-global-df-store', 'data'),
        Input('metrics-show-days-switch', 'value'),
        Input('metrics-exp-select-GEX-dd', 'value'),
    )
    def update_surfaceExpirationFilter(selected_exp_type, global_data, show_day, exp_select):

        disabled = True
        className = 'adapt_drop_down_disabled'
        multi = False

        options=[]
        list_exp = []

        if exp_select and isinstance(exp_select, list) and len(exp_select) >=5:
            exp_select = exp_select[:5]

        if selected_exp_type and selected_exp_type in {'Peak', 'Specific'}:

            df = pd.DataFrame(global_data)

            if show_day:

                col = 'expiration' 
                list_exp = sorted(list(df[col].unique()))
                options = (
                        [{"label": f'{str(exp)} days', "value": str(exp)} for exp in list_exp]
                    )
                
            else:

                col = 'expiration_bis'
                list_exp = sorted(list(df[col].unique()))
                sorted_dates = sorted(list_exp, key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=False)
                options = [{"label": date, "value": date} for date in sorted_dates]

            if selected_exp_type == 'Specific':

                multi=True

            disabled = False
            className = 'adapt_drop_down'
            

        return disabled, className, multi, options, exp_select
    

##########################################################################################
###    CALL-BACK expiration list rangeSlider
##########################################################################################

    @dash.callback(
            Output('metrics-GEX-rgs', 'disabled'),
            Output('metrics-GEX-rgs', 'min'),
            Output('metrics-GEX-rgs', 'max'),
            Output('metrics-GEX-rgs', 'value'),

            Input('metrics-date-selection', 'value'),
            Input('metrics-option-selection', 'value'),
            Input('metrics-exp-type-GEX-dd', 'value'),
            Input('metrics-exp-select-GEX-dd', 'value'),
            Input('metrics-global-df-store', 'data'),
            State('metrics-custom-df-store', 'data'),
            Input('metrics-option-info-store', 'data'),
            Input('metrics-show-days-switch', 'value'),
    )
    def update_rangeSlider(selected_date, selected_option, selected_exp_type, selected_exp, global_df, custom_df, info, show_day):

        value = []

        if not selected_exp_type or ('Peak' in selected_exp_type and not selected_exp) or ('Specific' in selected_exp_type and not selected_exp):
            return True, None, None, value
        
        if custom_df and 'ItemChosen' in selected_exp_type:
            df = pd.DataFrame(custom_df)
        else:
            df = pd.DataFrame(global_df)
      
        if selected_option and selected_date and selected_exp_type and not df.empty:
    
            listed = list(df['strike'].unique())

            if len(listed) > 0:

                min_strike = float(min(listed))
                max_strike = float(max(listed))

                last_st = LoadingData().get_last_st(info, True, selected_date)
    
                c = 4  
                f = c / (last_st ** 0.5)

                range_min = round(last_st * (1 - f))
                range_max = round(last_st * (1 + f))
                value = [range_min, range_max]

                return False, min_strike, max_strike, value
            
        else:
                return True, None, None, None
        
##########################################################################################
###    CALL-BACK Update graphs
##########################################################################################
    @dash.callback(
        Output('metrics-net-GEX-chart', 'figure'),
        Output('metrics-abs-GEX-chart', 'figure'),
        Output('metrics-DEX-chart', 'figure'),
        Output('metrics-VEX-chart', 'figure'),

        Input('metrics-date-selection', 'value'),
        Input('metrics-date-hour-selection', 'value'),
        Input('metrics-GEX-vol-type-dd', 'value'),
        Input('metrics-exp-type-GEX-dd', 'value'),
        Input('metrics-exp-select-GEX-dd', 'value'),
        Input('metrics-GEX-rgs', 'value'),

        Input('metrics-global-df-store', 'data'),
        State('metrics-custom-df-store', 'data'),

        Input('metrics-option-info-store', 'data'),
        Input('metrics-show-days-switch', 'value'),
    )
    def update_gexGraphs(selected_date, selected_hour, vol_type, exp_type, exp_selected, strike_range, global_data, custom_data, info, show_day):
        
        fig = go.Figure()
        fig.add_annotation(
            text="Select Parameters",
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
            dragmode=False,
        )

        fig_net_gex= fig
        fig_abs_gex = fig
        fig_vex = fig
        fig_dex = fig

        if True in show_day:
            selected_show_day = True
        else:
            selected_show_day = False

        if exp_type:
            if exp_type == 'ItemChosen' and custom_data:
                custom_df = pd.DataFrame(custom_data)
                list_custom_df = custom_df['expiration'].unique().tolist()
                
                df = pd.DataFrame(global_data)
                df = df[df['expiration'].isin(list_custom_df)]
            else:
                df = pd.DataFrame(global_data)
        else:
            df = pd.DataFrame()

        if not df.empty and exp_type and strike_range:

            if not exp_selected and exp_type in ['Specific', 'Peak']:
                return fig_net_gex, fig_abs_gex, fig_vex

            strike_dw, strike_up = strike_range  
            gamma_exposure = GammaExposure(selected_date, selected_hour, info, selected_show_day)
            delta_exposure = DeltaExposure(selected_date, selected_hour, info, selected_show_day)
            vanna_exposure = VannaCumulative(selected_date, selected_hour, info, selected_show_day)

            fig_net_gex = gamma_exposure.gammaExposureCalcul(df, 'net', vol_type, strike_dw, strike_up, exp_type, exp_selected, plot=True) 
            fig_abs_gex = gamma_exposure.gammaExposureCalcul(df, 'abs', vol_type, strike_dw, strike_up, exp_type, exp_selected, plot=True)  

            fig_dex = delta_exposure.getDeltaExposure(df, strike_dw, strike_up, exp_type, exp_selected, plot=True)

            fig_vex = vanna_exposure.getVannaExposure(df, strike_dw, strike_up, exp_type, exp_selected, plot=True)

        return fig_net_gex, fig_abs_gex, fig_dex, fig_vex
