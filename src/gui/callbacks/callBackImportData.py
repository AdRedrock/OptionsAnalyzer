import dash
from dash import html, Input, Output, State, callback_context
from dash.exceptions import PreventUpdate

from import_data.import_data import ImportOptionSymbol, OptionsDataFetcher
from import_data.utils import CheckFileAndData, LoadingData


from src.config.constant import PROVIDER_LIST

##########################################################################################
##########################################################################################
###    CALL-BACK SelectData
##########################################################################################
##########################################################################################

class SetDataCallBack:
    def __init__(self):
        pass


##########################################################################################
###    CALL-BACK SELECT DATA
##########################################################################################

    @dash.callback(
    Output('import-provider-dd', 'disabled'),  
    Output('import-provider-dd', 'className'),
    Output('import-provider-dd', 'value'),

    Output('import-ticker-dd', 'disabled'),
    Output('import-ticker-dd', 'className'),
    Output('import-ticker-dd', 'options'),

    Input('import-provider-dd', 'value'),
    Input('import-already-imported-switch', 'value')
    )
    def update_listedTickersDropDown(selected_provider, already_imported):

        class_ImportOptionSymbol = ImportOptionSymbol()
        class_LoadingData = LoadingData()

        value = ''

        if already_imported:
            
            imported_symbol = class_LoadingData.load_existing_symbols()

            options = [{'label': key, 'value': key, 'disabled': False} for key in imported_symbol]
            className = 'drop_down'

            return True, 'drop_down_disabled', value, False, className, options


        elif selected_provider and not already_imported:
            
            if selected_provider == 'CBOE':
                symbol_list = class_ImportOptionSymbol.load_all_symbol_json()
            
            options = [{'label': key, 'value': key, 'disabled': False} for key in symbol_list]
            className = 'drop_down'

            return False, className, dash.no_update, False, className, options
        

        className = 'drop_down_disabled'

 
        return False, 'drop_down', value, True, className, [] 
    
##########################################################################################
###    CALL-BACK DROWDOWN FILL TICKER IF INFO JSON
##########################################################################################

    @dash.callback(
    Output('import-ticker-st-input', 'disabled'),
    Output('import-ticker-st-input', 'className'),
    Output('import-ticker-st-input', 'value'),

    Output('import-change-dd', 'value'),
    Output('import-quote-type-dd', 'value'),
    Output('import-lot-size-dd', 'value'),

    Output('import-quotation-type-value-store', 'data'),

    Input('import-ticker-dd', 'value'),
    State('import-provider-dd', 'value'),
    State('import-already-imported-switch', 'value')
    )
    def update_loadTicker(selected_option, selected_provider, already_imported):

        className = 'drop_down_disabled'

        class_LoadingData = LoadingData()
        class_CheckFileAndData = CheckFileAndData()

        if selected_provider and selected_option:

            underlying_ticker, change, quotation_type, quotation_type_value, lot_size = class_LoadingData.load_st_ticker_info_json(selected_provider, selected_option)

            className = 'drop_down'  

            return False, className, underlying_ticker, change, quotation_type, lot_size, quotation_type_value

    
        elif selected_option and not selected_provider:

            for i in PROVIDER_LIST:

                check_json = class_CheckFileAndData.check_json(i, selected_option)
                if check_json:

                    underlying_ticker, change, quotation_type, quotation_type_value, lot_size= class_LoadingData.load_st_ticker_info_json(i, selected_option)
             
                    className = 'drop_down'
                    
                    return False, className, underlying_ticker, change, quotation_type, lot_size, str(quotation_type_value)

                else:
                    st_value = selected_option 
                    className = 'drop_down'

                    return False, className, st_value, None, None, None, None

            return True, className, None, None, None, None, None

        return True, className, None, None, None, None, None  

##########################################################################################
###    CALL-BACK RELOAD BUTTON
##########################################################################################

    @dash.callback(
            Output("import-loading-data2", "children"),
            Output('import-reload-symbols-button', 'className'),  
            Output('import-reload-symbols-button', 'children'),  
            Output('import-reload-symbols-button', 'disabled'),  

            Input('import-provider-dd', 'value'), 
            Input('import-reload-symbols-button', 'n_clicks'),
            prevent_initial_call='initial_duplicate', 
    )
    def update_cboeSymbol(provider, n_clicks):
        ctx = dash.callback_context  

        if ctx.triggered and 'import-provider-dd.value' in ctx.triggered[0]['prop_id']:
            if provider == 'CBOE':
                return (
                    dash.no_update,
                    "reload_symbol_button",  
                    [html.I(className='bi bi-arrow-clockwise')],  
                    False  
                )
            else:
                return (
                    dash.no_update,
                    "reload_symbol_button_disabled", 
                    [html.I(className='bi bi-arrow-clockwise')],  
                    True  
                )

        if ctx.triggered and 'import-reload-symbols-button.n_clicks' in ctx.triggered[0]['prop_id']:
            if n_clicks and n_clicks > 0:
              
                class_ImportOptionSymbol = ImportOptionSymbol()
                check_ticker = class_ImportOptionSymbol.download_symbol_json() 

                if check_ticker:
                    return (
                        dash.no_update,
                        "reload_symbol_button_valid",  
                        [html.I(className='bi bi-cloud-check')], 
                        False  
                    )
                else:
                    return (
                        dash.no_update,
                        "reload_symbol_button_invalid",  
                        [html.I(className='bi bi-file-earmark-x')],  
                        False  
                    )

        return (
            dash.no_update,
            "reload_symbol_button_disabled",  
            [html.I(className='bi bi-arrow-clockwise')],  
            True 
    )


##########################################################################################
###    CALL-BACK CHECK ST
##########################################################################################

    @dash.callback(
            Output("import-loading-data1", "children"),
            Output('import-check-st-button', 'className'), 
            Output('import-check-st-button', 'children'),  
            Output('import-check-st-button', 'disabled'),  
            Input('import-check-st-button', 'n_clicks'),  
            Input('import-ticker-st-input', 'value'),     
    )
    def update_checkSt(n_clicks, selected_st):
        ctx = dash.callback_context 

    
        if ctx.triggered and 'import-ticker-st-input' in ctx.triggered[0]['prop_id']:
            if selected_st:
                return dash.no_update, 'check_st_button', [html.I(className='bi bi-cloud-arrow-up')], False
            return dash.no_update, 'check_st_button_disable', [html.I(className='bi bi-cloud-arrow-up')], True

    
        if ctx.triggered and 'import-check-st-button.n_clicks' in ctx.triggered[0]['prop_id']:
            if n_clicks and n_clicks > 0:
                class_CheckFileAndData = CheckFileAndData()
                check_ticker = class_CheckFileAndData.check_st_yfinance(selected_st) 

                if check_ticker:
                    return (
                        dash.no_update,
                        "check_st_button_valid-button",
                        [html.I(className='bi bi-cloud-check')],
                        False
                    )
                else:
                    return (
                        dash.no_update,
                        "check_st_button_invalid-button",
                        [html.I(className='bi bi-file-earmark-x')],
                        False
                    )

        return dash.no_update, 'check_st_button_disable', [html.I(className='bi bi-cloud-arrow-up')], True

##########################################################################################
###    CALL-BACK DOWNLOAD DATA
##########################################################################################

    @dash.callback(
        Output('import-msgbox', 'is_open'),
        Output('import-msgbox', 'color'),
        Output('import-msgbox', 'children'),

        Output("import-loading-data", "children"),
        Output('import-already-imported-options-ticker-store', 'data'),

        Input('import-dl-button', 'n_clicks'),
        State('import-ticker-dd', 'value'),
        State('import-ticker-st-input', 'value'),
        State('import-change-dd', 'value'),
        State('import-quote-type-dd', 'value'),
        State('import-vn-pt-value-dd', 'value'),
        State('import-lot-size-dd', 'value'),
        State('import-provider-dd', 'value'),
        State('import-already-imported-switch', 'value'),
        Input('import-already-imported-options-ticker-store', 'data'),
        prevent_initial_call='initial_duplicate'
    )
    def download_buttonImportData(n_clicks, selected_ticker, selected_st, selected_change, selected_quote, select_value, selected_lot, provider,already_imported, refresh_imported_options):

        ctx = dash.callback_context 

        if ctx.triggered and 'import-dl-button' in ctx.triggered[0]['prop_id']:

            refresh_imported_options = refresh_imported_options + ['1']

            if selected_quote == 'direct_quote' and select_value is None:
                select_value = 1

            class_ImportOptionSymbol = ImportOptionSymbol()
            class_OptionsDataFetcher = OptionsDataFetcher()
            class_CheckFileAndData = CheckFileAndData()

            dict_info = {
                            "provider":f"{provider}",
                            "market_place":f"{provider}",
                            "option_ticker":f"{selected_ticker}",
                            "underlying_ticker":f"{selected_st}",
                            "change":f"{selected_change}",
                            "quotation_type":f"{selected_quote}", 
                            "quotation_type_value":f"{select_value}",
                            "lot_size":f"{selected_lot}"
                        }


            if selected_quote == 'nominal_value' or selected_quote == 'points':
                if not select_value:

                    message = 'Please fill Nominal or Point value section'
                    color = 'warning'

                    return True, color,  message, dash.no_update, refresh_imported_options


            if not already_imported and selected_quote and selected_ticker and selected_st and selected_change and selected_lot:
                if provider == 'CBOE':
                    
                    class_ImportOptionSymbol.create_json_info(dict_info, provider, selected_ticker)
                    class_OptionsDataFetcher.get_options_data_cboe(selected_ticker, True)

                    message = f'Success ! new {selected_ticker} asset data has been imported'
                    color = 'success'

                    return True, color,  message, dash.no_update, refresh_imported_options

                else:
                    
                    message = 'Coming soon !'
                    color = 'Info'

                    return True, color,  message, dash.no_update, refresh_imported_options

            elif already_imported and selected_quote and selected_ticker and selected_st and selected_change and selected_lot:

                for i in PROVIDER_LIST:

                    check_json = class_CheckFileAndData.check_json(i, selected_ticker)
                    if not check_json:
                     

                        class_ImportOptionSymbol.create_json_info(dict_info, i, selected_ticker)
                        class_OptionsDataFetcher.get_options_data_cboe(selected_ticker, True)
                 
                        message = f'Success ! new {selected_ticker} asset data has been imported'
                        color = 'success'

                        return True, color,  message, dash.no_update, refresh_imported_options
                    
                    else:
                        
                        class_ImportOptionSymbol.create_json_info(dict_info, i, selected_ticker)
                        class_OptionsDataFetcher.get_options_data_cboe(selected_ticker, True)
                 
                        message = f'Success ! new {selected_ticker} asset data has been imported'
                        color = 'success'

                        return True, color,  message, dash.no_update, refresh_imported_options

            else:
                if not selected_quote or not selected_ticker or not selected_st or not selected_change or not selected_lot:
                    
                    message = 'Please, set parameters before importing data'
                    color = 'danger'
                    

                    return True, color,  message, dash.no_update, refresh_imported_options

        color = 'info'

        return False, color, '', dash.no_update, refresh_imported_options
    
##########################################################################################
###    CALL-BACK UPDATE INFO FILE
##########################################################################################
    @dash.callback(
        Output('import-msgbox', 'is_open', allow_duplicate=True),
        Output('import-msgbox', 'color', allow_duplicate=True),
        Output('import-msgbox', 'children', allow_duplicate=True),

        Input('import-info-button', 'n_clicks'),
        State('import-ticker-dd', 'value'),
        State('import-ticker-st-input', 'value'),
        State('import-change-dd', 'value'),
        State('import-quote-type-dd', 'value'),
        State('import-vn-pt-value-dd', 'value'),
        State('import-lot-size-dd', 'value'),
        State('import-provider-dd', 'value'),
        State('import-already-imported-switch', 'value'),
        prevent_initial_call='initial_duplicate'
        
    )
    def download_buttonImportData(n_clicks, selected_ticker, selected_st, selected_change, selected_quote, select_value, selected_lot, provider,already_imported):

        ctx = dash.callback_context 

        if ctx.triggered and 'import-info-button' in ctx.triggered[0]['prop_id']:

            class_ImportOptionSymbol = ImportOptionSymbol()

            if selected_quote == 'direct_quote' and select_value is None:
                select_value = 1

            dict_info = {
                            "provider":f"{provider}",
                            "market_place":f"{provider}",
                            "option_ticker":f"{selected_ticker}",
                            "underlying_ticker":f"{selected_st}",
                            "change":f"{selected_change}",
                            "quotation_type":f"{selected_quote}", 
                            "quotation_type_value":f"{select_value}",
                            "lot_size":f"{selected_lot}"
                        }
            if selected_quote != 'direct_quote':
                if already_imported and selected_quote and selected_ticker and selected_st and selected_change and select_value and selected_lot:

                    
                    create_json_info = class_ImportOptionSymbol.create_json_info(dict_info, provider='search', selected_option=selected_ticker)

                    message = f'{selected_ticker} Info file is successfully refreshed'
                    color = 'info'

                    return True, color,  message
                
                elif not selected_quote or not selected_ticker or not selected_st or not selected_change or not selected_lot or not select_value:
                        
                    message = 'Please, set parameters before refresh info file'
                    color = 'danger'
                    
                    return True, color,  message

                else:

                    message = 'Fatal error'
                    color = 'danger'
                    
                    return True, color,  message
                
            elif selected_quote == 'direct_quote':

                if already_imported and selected_quote and selected_ticker and selected_st and selected_change and selected_lot:

                   
                    result = class_ImportOptionSymbol.create_json_info(dict_info, provider='search', selected_option=selected_ticker)

                    message = f'{selected_ticker} Info file is successfully refreshed'
                    color = 'info'

                    if not result:
                    
                        message = f'{selected_ticker} has not already been imported, ensure it is imported at least once to update the information.'
                        color = 'warning'

                    return True, color,  message
                
                elif not already_imported and selected_quote and selected_ticker and selected_st and selected_change and selected_lot:
                    
                    result = class_ImportOptionSymbol.create_json_info(dict_info, provider='search', selected_option=selected_ticker)
                    message = f'{selected_ticker} Info file is successfully refreshed'
                    color = 'info'

                    if not result:
                    
                        message = f'{selected_ticker} has not already been imported, ensure it is imported at least once to update the information.'
                        color = 'warning'

                    return True, color,  message
                
                elif not already_imported or not selected_quote or not selected_ticker or not selected_st or not selected_change or not selected_lot:
                        
                    message = 'Please, set parameters before refresh info file'
                    color = 'danger'
                    
                    return True, color,  message

                else:

                    message = 'Fatal error'
                    color = 'danger'
                    
                    return True, color,  message

        color = 'info'

        return False, color, ''
    

##########################################################################################
##########################################################################################
###    CALL-BACK ParamInfoJson
##########################################################################################
##########################################################################################

class ParamInfoJsonCallBack:
    def __init__(self):
        pass

##########################################################################################
###    CALL-BACK UPDATE NOMINAL OR POINT VALUE DROPDOWN
##########################################################################################

    @dash.callback(
        Output('import-vn-pt-value-dd', 'disabled'),
        Output('import-vn-pt-value-dd', 'className'),
        Output('import-vn-pt-value-dd', 'options'),
        Output('import-vn-pt-value-dd', 'placeholder'),
        Output('import-vn-pt-value-dd', 'value'),
        Output('import-quotation-type-value-store', 'data', allow_duplicate=True), 

        Input('import-quote-type-dd', 'value'),
        Input('import-quotation-type-value-store', 'data'),
        State('import-quote-type-dd', 'value'),
        State('import-change-dd', 'value'),
        prevent_initial_call='initial_duplicate'
    )
    def update_nominalOrPointValueList(selected_quote_type, stored_variable, state_quote_type, selected_change):
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        value = ''
        change_dict = {
            'USD': '$',
            'GBP': '£',
            'EUR': '€',
            'JPY': '¥',
        }

        change_symbol = change_dict.get(selected_change, '')
        placeholder = 'St Nominal/Point value'
        className = 'adapt_drop_down_disabled'
        options = []  

        if stored_variable:
            value = stored_variable
            stored_variable = ''  


        if 'import-quote-type-dd' in triggered_id:
            if selected_quote_type == 'direct_quote' or state_quote_type == 'direct_quote':
                return True, className, options, placeholder, value, stored_variable

            if selected_quote_type == 'points' or state_quote_type == 'points':
                placeholder = f'Select Point Value ({change_symbol})'
                options = [
                    {'label': '1', 'value': '1'},
                    {'label': '10', 'value': '10'},
                    {'label': '20', 'value': '20'},
                    {'label': '50', 'value': '50'},
                    {'label': '100', 'value': '100'},
                    {'label': '1,000', 'value': '1000'},
                ]
                className = 'adapt_drop_down'
                return False, className, options, placeholder, value, stored_variable

            if selected_quote_type == 'nominal_value' or state_quote_type == 'nominal_value':
                placeholder = f'Select Nominal Value ({change_symbol})'
                options = [
                    {'label': '100', 'value': '100'},
                    {'label': '1,000', 'value': '1000'},
                    {'label': '5,000', 'value': '5000'},
                    {'label': '100,000', 'value': '100000'},
                    {'label': '1,000,000', 'value': '1000000'},
                ]
                className = 'adapt_drop_down'
                return False, className, options, placeholder, value, stored_variable

        return True, className, options, placeholder, value, stored_variable