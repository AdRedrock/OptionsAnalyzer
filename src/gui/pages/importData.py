from dash import html, dcc
import dash_bootstrap_components as dbc


class HeaderLayout:
    def __init__(self):
        pass 
    
    def header(self):
        content = html.Div(
            children=[
                html.H1("Import Data", className="head_title"),  
                html.Hr(className='head_divider'), 
                dbc.Alert(id='import-msgbox', children='Test', color="info", is_open=False, dismissable=True, fade=True, class_name='alert-dismissible'),
                dcc.Store(id='import-already-imported-options-ticker-store', data=[]),
                dcc.Store(id='import-quotation-type-value-store'),
            ]
        )


        return content
    
##########################################################################################
###    Layout SelectData
##########################################################################################

class SelectData:
    def __init__(self):
        pass

    def layout(self):

        content = dbc.Col(
            children=[
                html.Div(self.listedProviderDropDown()),
                html.Div(self.listedTickerDropDown()),
                html.Div(self.buttonReloadSymbol()),
                html.Div(
                    [     
                    self.addUnderlayingTicker(),
                    dbc.Tooltip(
                    "Choose the ticker of the underlying on the yfinance website. Ex nasdaq ticker is ^NDX", 
                    target="import-ticker-st-input",
                    ),
                    ],
                    ),
                html.Div(
                    [   
                    self.buttonCheckSt(),
                    dbc.Tooltip(
                    "Sends a request to the binance servers to check whether the ticker is valid", 
                    target="import-check-st-button",
                    ),
                    ]
                         )
            ],
            style={
                'display': 'flex', 
                'justify-content': 'flex-start',
                'gap': '20px',
                'padding-top' : '20px'
                }
        )

        row = dbc.Row(
            children=[
                html.Div(
                    [
                        self.switchAlreadyImported(),
                        dbc.Tooltip(
                    "Select an imported contract. Deactivate to import a new contract.", 
                    target="import-already-imported-switch",
                        )
                    ]
                    ),
                    
                content
            ]
        )

        return row

    def listedProviderDropDown(self):

        select_box = dcc.Dropdown(
            id='import-provider-dd',
            options=[
                {'label': 'CBOE', 'value': 'CBOE'},
                {'label': 'Barchart', 'value':'Barchart (coming soon)', 'disabled':True},     
                     ],
            optionHeight=25,
            disabled=True,
            placeholder="Select a data provider",
            searchable=False,
            search_value='',
            className='drop_down',
        )

        return select_box

    def listedTickerDropDown(self):

        select_box = dcc.Dropdown(
            id='import-ticker-dd',
            optionHeight=25,
            disabled=True,
            placeholder="Select a symbol",
            searchable=True,
            search_value='',
            className='drop_down',
        )

        return select_box
    
    def addUnderlayingTicker(self):

        content = html.Div(
            [
                dbc.Input(
                    id='import-ticker-st-input',
                    placeholder='St Ticker (yahoofinance)',
                    disabled=True,
                    className='drop_down_disabled',
                    ),
            ],
        )

        return content
    
    def switchAlreadyImported(self):
        switch = dbc.Checklist(
            id="import-already-imported-switch",
            options=[{"label": "", "value": True}],  
            value=[], 
            switch=True,  
            style={"fontSize": "10px"} 
        )
    
        return html.Div([
            switch,
            html.Div("Imported", className="switch-title") 
        ], className="custom-switch-container")

    def buttonCheckSt(self):

        button = html.Button(
            
            [
                html.I(className='bi bi-cloud-arrow-up'),
            ],
            id='import-check-st-button',
            n_clicks=0,
            disabled=True,
            className='check_st_button_disable',
            title="Verify if yfinance can access the specified ticker"
        )


        return button

    def buttonReloadSymbol(self):
        return html.Button(
            
        [
            html.I(className='bi bi-arrow-clockwise'),
        ],
        id='import-reload-symbols-button',
        n_clicks=0,
        className='reload_symbol_button_disabled',
        title="Reload options tickers list (CBOE only)"
        )
    

    def buttonImportData(self):
        button = html.Button(
            'Download Data',
            id='import-dl-button',
            n_clicks=0,
            className='classic_button'
        )

        return button

##########################################################################################
###    Layout ParamInfoJson
##########################################################################################

class ParamInfoJson:
    def __init__(self):
        pass

    def layout(self):

        content = dbc.Col(
            [
                self.paramsBox(),
                dbc.Row( 
                    [
                        dbc.Col(self.buttonImportData(), width="auto", className="p-0 m-0"),  
                        dbc.Col(
                            dcc.Loading(
                                children=[html.Div(id="import-loading-data"), html.Div(id="import-loading-data1"), html.Div(id="import-loading-data2")],
                                custom_spinner=dbc.Spinner(color="info"),
                            ),
                            width="1",
                            style={'margin-top':'20px'},
                        ),
                    ],
                    className="g-0",
                    style={'display': 'flex', 'gap': '5px', 'alignItems': 'center'}
                )            
            ],
            id='import-params-container',
        )

        return content    


    def paramsBox(self):

        return html.Div([  
         
            html.Div([
                html.Div(self.addParams()),
            ], 
            className='container_radius',
            style={'margin-bottom':'20px'}
            )
        ])
    
    def addParams(self):
        col1 = dbc.Col(
            children=[
                html.P('Change Symbol', className='parameter-label'), 
                html.Div(self.changeList())
            ],
            width=2,
            className='d-flex flex-column'
        )
        
        col2 = dbc.Col(
            children=[
                html.P('Contract Size', className='parameter-label'),
                html.Div(self.underlyingLotSizeList())
            ],
            width=2,
            className='d-flex flex-column'
        )
        
        col3 = dbc.Col(
            children=[
                html.P('Quotation Type', className='parameter-label'),
                html.Div(self.quotationTypeList())
            ],
            width=2,
            className='d-flex flex-column'
        )
        
        col4 = dbc.Col(
            children=[
                html.P('Nominal Or Point Value', className='parameter-label'),
                html.Div(self.nominalOrPointValueList())
            ],
            width=2,
            className='d-flex flex-column'
        )
        
        col5 = dbc.Col(
            children=[
                self.buttonUpdateInfo()
            ],
            style={'margin-top':'44px'},
            width=2
        )

        content = dbc.Row(
            children=[col1, col2, col3, col4, col5],
            style={
                'gap':'10px',
                'padding': '10px',
                'align-items': 'stretch' 
            }
        )
    
        return content
    
    def changeList(self):

        select_box = dcc.Dropdown(
            id='import-change-dd',
            options=[
                {'label': 'USD ($)', 'value': 'USD'},
                {'label': 'EUR (€)', 'value':'EUR'},
                {'label': 'GBP (£)', 'value':'GBP'},
                {'label': 'JPY (¥)', 'value':'JPY'},         
                     ],
            optionHeight=25,
            disabled=False,
            placeholder="Select change",
            searchable=False,
            search_value='',
            className='adapt_drop_down',
        )

        return select_box
    
    def quotationTypeList(self):

        select_box = dcc.Dropdown(
            id='import-quote-type-dd',
            options=[
                {'label': 'Direct Quotation', 'value': 'direct_quote'},
                {'label': 'Point-based Quotation', 'value': 'points'},
                {'label': 'Nominal Value (%)', 'value': 'nominal_value', 'disabled':True},    
                        ],
            optionHeight=25,
            disabled=False,
            placeholder="Select Quotation Type",
            searchable=False,
            search_value='',
            className='adapt_drop_down',
        )

        return select_box
    
    def underlyingLotSizeList(self):


        select_box = dcc.Dropdown(
            id='import-lot-size-dd',
            options=[
                {'label': '1', 'value': '1'},
                {'label': '100', 'value': '100'},
                {'label': '1,000', 'value': '1000'},  
                {'label': '100,000', 'value': '100000'},   
                        ],
            optionHeight=25,
            disabled=False,
            placeholder="Select lot size",
            searchable=False,
            search_value='',
            className='adapt_drop_down',
        )

        return select_box
    
    def nominalOrPointValueList(self):

        select_box = dcc.Dropdown(
            id='import-vn-pt-value-dd',
            options=[],
            optionHeight=25,
            disabled=True,
            placeholder="St Nominal/Point value",
            searchable=False,
            search_value='',
            className='adapt_drop_down_disabled',
        )

        return select_box
    
    def buttonImportData(self):
        button = html.Button(
            'Download Data',
            id='import-dl-button',
            n_clicks=0,
            className='important_button'
        )

        return button
    
    def buttonUpdateInfo(self):
        button = html.Button(
            'Update Info Only',
            id='import-info-button',
            n_clicks=0,
            className='classic_button'
        )

        return button

##########################################################################################
###    MAIN FRAME LAYOUT
##########################################################################################

class ImportDataPageFrame:

    def __init__(self):
        super().__init__()

        self.header = HeaderLayout().header()
        self.selectdata = SelectData().layout()
        self.params = ParamInfoJson().layout()

        self.layout = dbc.Col([
            self.header,
            self.selectdata,
            self.params
        ],
        style={'margin-left': '40px'}
        )
    
    def render(self):
        return self.layout  
    

def layout():
    return ImportDataPageFrame().render()