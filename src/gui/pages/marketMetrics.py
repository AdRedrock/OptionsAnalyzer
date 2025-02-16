import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import html, dcc

from import_data.utils import LoadingData

from src.config.constant import PERSISTENCE_TYPE


class HeaderLayout:
    def __init__(self):
        pass 
    
    def header(self):
        content = html.Div(
         
            children=[
                html.H1("Market Metrics", className="head_title"),  
                html.Hr(className='head_divider'), 
                dbc.Alert(id='metrics-msgbox', children='Test', color="info", is_open=False, dismissable=True, fade=True, class_name='alert-dismissible'),
                dcc.Store(id='metrics-global-df-store'),
                dcc.Store(id='metrics-custom-df-store'),
                dcc.Store(id='metrics-global-var1-df-store'),
                dcc.Store(id='metrics-global-var2-df-store'),
                dcc.Store(id='metrics-global-iv-smile-df-store'),
                dcc.Store(id='metrics-option-info-store'),
            ]
        )
        return content
    
##########################################################################################
###    GLOBAL SET-UP LAYOUT (option choosen etc...)
##########################################################################################

class GlobalSetUpLayout:
    def __init__(self):
        self.class_LoadingData = LoadingData()
        self.already_imported = self.class_LoadingData.load_existing_symbols()
     

    def layout(self):

        content = dbc.Col(
            children=[
                html.Div(self.tickerDropDown()),
                html.Div(self.dateImportedDropDown()),
                html.Div(self.hourImportedDropDown()),
                html.Div(self.showDayExpiration()),
                html.Div(self.spinnerLoading())
            ],
            style={
                'display': 'flex', 
                'justify-content': 'flex-start',
                'gap': '20px',
                'padding-top' : '20px'
                }
        )
        return content

    def tickerDropDown(self):

        dropdown_options = [{"label": option, "value": option} for option in self.already_imported]

        select_box = dcc.Dropdown(
            id='metrics-option-selection',
            options=dropdown_options,
            optionHeight=25,
            disabled=False,
            placeholder="Select a symbol",
            searchable=True,
            search_value='',
            className='drop_down',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    

    def dateImportedDropDown(self):

        select_box = dcc.Dropdown(
            id='metrics-date-selection',
            optionHeight=25,
            disabled=True,
            placeholder="Imported Date Y-M-D",
            searchable=True,
            search_value='',
            className='drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def hourImportedDropDown(self):

        select_box = dcc.Dropdown(
            id='metrics-date-hour-selection',
            optionHeight=25,
            disabled=True,
            placeholder="Select Hour",
            searchable=True,
            search_value='',
            className='drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
         
    def showDayExpiration(self):

        switch = dbc.Checklist(
            id="metrics-show-days-switch",
            options=[{"label": "", "value": True}],  
            value=[True], 
            switch=True,  
            style={"fontSize": "10px"},
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )
    
        return html.Div([
            switch, 
            html.Div("Expiry (Days)", className="switch-sub") 
        ], className="custom-switch-container")

    def spinnerLoading(self):
        spinner = dbc.Spinner(
            html.Div(id='metrics-loading-output', children='default', style={'color': 'var(--customBgColor)', 'margin-top':'12px'}),
            color='info'
        )
        return spinner

##########################################################################################
##########################################################################################
###    TAB -> Metrics Options Selection
##########################################################################################
##########################################################################################

class MetricsOptionsSelection:
    def __init__(self):
        pass

    def layout(self):

        row1 = html.Div([
            html.H6('Select the options most relevant to your needs. You will then be able to choose your "basket" for further analysis.', style={'fontWeight': 'normal'}),
        ])
        
        row2 = dbc.Row(
            [
                 dcc.Loading(
                [    
                    self.buttonAddSelection(),
                    self.dataTable()
                ],
                overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                custom_spinner=dbc.Spinner(color="info"),
                ),
            ]
        )

        row3 = dbc.Row(
            [
                 dcc.Loading(
                [    
                    self.buttonDelSelection(),
                    self.selectionDatatable()
                ],
                overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                custom_spinner=dbc.Spinner(color="info"),
                ),
            ]
        )


        content = dbc.Container(
            [
                row1,
                html.H2("DataTable"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                row2,
                            ],
                            title='Choose options from the dataset',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
                html.H2("Selected Option(s)"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                row3,
                            ],
                            title='List of selected options',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
            ],
            fluid=True,  
            style={'margin-left':'0px'}
        )

        return content


    def dataTable(self):

        data = dag.AgGrid(
            id='metrics-selection-datatable',
            columnDefs=[
                {"checkboxSelection": True, "headerName": "Select", "width": 10},  
                {"headerName": "Call/Put", "field": "option_type", "filter": True, "sortable": True, "resizable": True},
   
            ],
            defaultColDef={"flex": 1, "minWidth": 150, "sortable": True, "resizable": True, "filter": True},
            dashGridOptions={
                "rowSelection": "multiple", 
                "suppressRowClickSelection": True,  
            },
        )

        return data
    
    def selectionDatatable(self):

        data = dag.AgGrid(
            id='metrics-selected-datatable',
            columnDefs=[],
            defaultColDef={"flex": 1, "minWidth": 150, "sortable": True, "resizable": True, "filter": True},
            dashGridOptions={"rowSelection":"multiple"},
        )

        return data

    def buttonAddSelection(self):
        button = html.Button(
            [
                html.I(className='bi bi-file-earmark-plus', style={'margin-right': '8px', 'font-size': '30px'}),
                html.Span('Add Selection', style={'font-weight': '500'}),
            ],
            id='metrics-add-selection-button',
            n_clicks=0,
            className='important_button',
            style={
                'margin-bottom': '20px',
                'display': 'flex',        
                'align-items': 'center', 
                'justify-content': 'center', 
                'gap': '4px'  
            }
        )

        return button

    def buttonDelSelection(self):
        button = html.Button(
            [
                html.I(className='bi bi-trash3', style={'margin-right': '8px', 'font-size': '27px'}),
                html.Span('Delete Selection', style={'font-weight': '500'}),
            ],
            id='metrics-del-selection-button',
            n_clicks=0,
            className='del_button',
            style={
                'margin-bottom': '20px',
                'display': 'flex',        
                'align-items': 'center', 
                'justify-content': 'center', 
                'gap': '4px'  
            }
        )

        return button


##########################################################################################
##########################################################################################
###    TAB -> Metrics Put Call Open Interest
##########################################################################################
##########################################################################################

class MetricsPutCallOI:
    def __init__(self):

        self.OIVolumeLayout = OIVolumeLayout()
        self.OIVariationLayout = OIVariationLayout()
        self.OIVolumesExpirationsLayout = OIVolumesExpirationsLayout()

    def layout(self):

        col1 = dbc.Col(

            dcc.Loading(
                [    
                    self.OIVolumeLayout.graphMetrics1(),
                ],
                overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                custom_spinner=dbc.Spinner(color="info"),
                ),
            width=7  
        )

        col2 = dbc.Col(
            [
                 self.OIVolumeLayout.paramsMetrics1(),
            ],
            width=5  
        )

        row1 = dbc.Row(
            [
                col1,
                col2
            ],
            justify='start',
        )


        row2 = dbc.Row(
            [
                self.OIVolumesExpirationsLayout.paramsMetrics()
            ]
        )
                

        row2b = dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(  
                            [
                                self.OIVolumesExpirationsLayout.graphMetricsVolExpiration()
                            ],
                            overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                            custom_spinner=dbc.Spinner(color="info"),
                        )
                    ],
                ),
            ]
        )


        row3 = dbc.Row(
            [
                self.OIVariationLayout.paramsMetrics2()
            ]
        )

        row3b = dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(
                            [
                                self.OIVariationLayout.graphMetricsCall2(),
                            ],
                            overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                            custom_spinner=dbc.Spinner(color="info"),
                        )
                    ],
                    style={'border-right': '1px solid #ccc'},
                    width=9,
                ),
                dbc.Col(
                    [
                        self.OIVariationLayout.infoGraphMetricsCall2(),
                    ],
                    style={'margin-left':'40px'},
                )
            ]
        )


        row3c = dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(  
                            [
                                self.OIVariationLayout.graphMetricsPut2(),
                            ],
                            overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                            custom_spinner=dbc.Spinner(color="info"),
                        )
                    ],
                    style={'border-right': '1px solid #ccc'},
                    width=9,
                ),
                dbc.Col(
                    [
                        self.OIVariationLayout.infoGraphMetricsPut2(),
                    ],
                    style={'margin-left':'40px'},
                )
            ]
        )

        

        content = dbc.Container(
            [
                html.H2("Current Volumes"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                row1,
                            ],
                            title='Volumes for Loaded Data',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
                html.H2("Volumes by expiration"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                row2,
                                row2b,
                            ],
                            title='Volumes by strike and expiration',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
                html.H2("Volumes Variations"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                row3,
                                row3b,
                                row3c
                            ],
                            title='Compare Call/Put evolution',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
            ],
            fluid=True,  
            style={'margin-left':'0px'}
        )

        return content

###    Layout Open Interest Volume 

class OIVolumeLayout:

    def __init__(self):
        pass

    def graphMetrics1(self):

        content = html.Div( 
            dcc.Graph(
                id='metrics-OI-chart',
                style={'height': '600px', 'width': '100%'}, 
                config={
                    'scrollZoom': True, 
                    'doubleClick': 'reset',
                    'displaylogo': False, 
                    'modeBarButtonsToAdd': [
                        'pan2d',
                        'zoomIn2d',
                        'zoomOut2d',
                        'toImage',  
                        'resetScale2d',
                        "v1hovermode",
                        "toggleSpikelines",
                        'hoverClosestCartesian',
                        'hoverCompareCartesian',
                    ],
                    'modeBarButtonsToRemove': [
                        'zoom2d', 'select2d', 'lasso2d',
                        'autoScale2d',
                
                    ],
                },
            )
        )
        return content

    
    def paramsMetrics1(self):
     
        expiration = dbc.Col(
            children=[
                html.P('Expiration'),
                html.Div(self.expirationOIDrowDown())
            ],
            width='100%'
        )

        expiration_type = dbc.Col(
            children=[
                html.P('Expiration Type'),
                html.Div(self.expirationOItype())
            ],
            width='100%'
        )

        volume_type = dbc.Col(
            children=[
                html.P('Volume Type'),
                html.Div(self.volumesType())
            ],
            width='100%'

        )



        row1 = dbc.Row(
            [
                dbc.Col([expiration_type], width=5, xs=12, sm=5),
                dbc.Col(expiration, width=5, xs=12, sm=5),
            ],
            style={'gap': '5px'},

        )

        row1b = dbc.Row(
            [
                dbc.Col(volume_type, width=5, xs=12, sm=5),
            ],
            style={'gap': '2px'},

        )

        strike_slider = dbc.Col(
            children=[
                html.P('Strike'),
                dcc.Loading(
                    [    
                        html.Div(self.strikeOIRangeSlider())
                    ],
                    overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                    custom_spinner=dbc.Spinner(color="info"),
                    ),
            ],
            width='100%'
        )

        call_stat = dbc.Col(
            [
                html.P('Call'),
                html.Div(id='metrics-call-vol-div', children='--')
            ]
        )

        put_stat = dbc.Col(
            [
                html.P('Put'),
                html.Div(id='metrics-put-vol-div', children='--')
            ]
        )

        put_call_ratio = dbc.Col(
            [
                html.P('Global Put/Call Ratio'),
                html.Div(id='metrics-ratio-vol-div', children='--')
            ]
        )

        row = dbc.Col(
            [
                dbc.Row([
                    row1,
                    row1b,
                    strike_slider,
                    dbc.Row(
                        [
                            call_stat,
                            put_stat,
                        ],
                    ),
                    put_call_ratio,
                ],
                style={'gap':'20px'}
                )
            ],
            style={'margin-top':'40px'}
        )
        return row

    def expirationOIDrowDown(self):

        select_box = dcc.Dropdown(
            id='metrics-exp-oi-dd',
            optionHeight=25,
            disabled=True,
            placeholder="Select expirations",
            searchable=True,
            multi=False,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def expirationOItype(self):
    
        select_box = dcc.Dropdown(
            id="metrics-peak-isolated-dd",
            optionHeight=25,
            disabled=True,
            placeholder="Select Expiration Filter",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box

    def volumesType(self):

        select_box = dcc.Dropdown(
            id="metrics-OI-vol-type-dd",
            options=[
                {"label": 'Volume', "value": 'volume'},
                {"label": 'OI', "value": 'oi'},
                {"label": 'Volume + OI', "value": 'volAndOI'},
            ],
            value='',
            optionHeight=25,
            disabled=True,
            placeholder="Select Volume Type",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box


    def strikeOIRangeSlider(self):

        content = dcc.RangeSlider(
            id='metrics-strike-oi-rgs',
            min=0,
            max=100,
            pushable=1,
            tooltip={"placement": "bottom", "always_visible": True},
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return content


###    Layout Open Interest Volumes by Expirations

class OIVolumesExpirationsLayout:
    
    def __init__(self):
        pass

    def paramsMetrics(self):

        volume_type = dbc.Col(
            children=[
                html.P('Volume Type'),
                html.Div(self.volumesType(), )
            ],
        )

        option_type = dbc.Col(
            children=[
                html.P('Options Type'),
                html.Div(self.optionsType())
            ],
        )

        row1 = dbc.Row(
            [
                dbc.Col(volume_type),
                dbc.Col(option_type),
            ],
        )


        row = dbc.Row(
            [
                row1,
            ],
                style={'margin-top':'40px', 'gap':'40px'}
                )
        
        return row
    
    def volumesType(self):

        select_box = dcc.Dropdown(
            id="metrics-OI-vol-type-by-exp-dd",
            options=[
                {"label": 'Volume', "value": 'volume'},
                {"label": 'OI', "value": 'oi'},
                {"label": 'Volume + OI', "value": 'volAndOI'},
            ],
            value='',
            optionHeight=25,
            disabled=True,
            placeholder="Select Volume Type",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box

    def optionsType(self):

        select_box = dcc.Dropdown(
            id="metrics-OI-options-type-by-exp-dd",
            options=[
                {"label": 'All', "value": 'All'},
                {"label": 'Call', "value": 'call'},
                {"label": 'Put', "value": 'put'},
            ],
            value='',
            optionHeight=25,
            disabled=True,
            placeholder="Select Volume Type",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def graphMetricsVolExpiration(self):

        content = html.Div( 
            dcc.Graph(
                id='metrics-vol-exp-chart',
                style={'height': '500px', 'width': '100%'},  
                config={
                    'scrollZoom': True,  
                    'doubleClick': 'reset',
                    'displaylogo': False, 
                    'modeBarButtonsToAdd': [
                        'pan2d',
                        'zoomIn2d',
                        'zoomOut2d',
                        'toImage', 
                        'resetScale2d',
                        "v1hovermode",
                        "toggleSpikelines",
                        'hoverClosestCartesian',
                        'hoverCompareCartesian',
                    ],
                    'modeBarButtonsToRemove': [
                        'zoom2d', 'select2d', 'lasso2d',
                        'autoScale2d',
                
                    ],
                },
            )
        )
        return content
    
###    Layout Open Interest Variation 

class OIVariationLayout:
    
    def __init__(self):
        pass

    def paramsMetrics2(self):
       
        volume_type = dbc.Col(
            children=[
                html.P('Volume Type'),
                self.volumesType()
            ],
        )
    
        import_another_date = dbc.Col(
            children=[
                html.P('Retrieve Another Trading Date'),
                self.importEarlierDate()
            ],
        )

        import_another_hour = dbc.Col(
            children=[
                html.P('Load Market Hour'),
                self.importEarlierHour()
            ],
        )

        expiration_type = dbc.Col(
            children=[
                html.P('Expiration Type'),
                html.Div(self.expirationOItype2())
            ],
        )

        expiration = dbc.Col(
            children=[
                html.P('Expiration'),
                html.Div(self.expirationOIDrowDown2())
            ],
        )

        col1 = dbc.Col(
            [
                dbc.Row(dbc.Col(import_another_date), className="mb-3"),
                dbc.Row(dbc.Col(volume_type, className="align-self-end")),
            ],
        )

        col2 = dbc.Col(
            [
                dbc.Row(dbc.Col(import_another_hour), className="mb-3"),
                dbc.Row(dbc.Col(expiration_type, className="align-self-end")),
            ],
        )

        col3 = dbc.Col(
            [
                dbc.Row(dbc.Col(expiration, className="align-self-end")),
            ],
        )

        row1 = dbc.Row(
            [
                col1,
                col2,
                col3,
            ],
            align="end",  
            # style={'row-gap': '20px'} 
        )

        strike_slider = dbc.Col(
            children=[
                html.P('Strike'),
                dcc.Loading(
                        [    
                            html.Div(self.strikeOIRangeSlider2())
                        ],
                        overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                        custom_spinner=dbc.Spinner(color="info"),
                    ),
            ],
            width='100%',
        )

        params_row = dbc.Row(
            [
                row1,
            ]
        )

        row = dbc.Row(
            [
                params_row,
                strike_slider
            ],
                style={'margin-top':'20px', 'gap':'40px'}
                )
        
        return row
    
    def infoGraphMetricsCall2(self):

        call_info = dbc.Col(
            [
                html.P('Call OI variations'),
                html.Div(id='metrics-info-call-var-div', children='--'),
            ],
            width='100%',
        )

        row = dbc.Row(
            [
                call_info
            ],
            style={'margin-top': '20px', 'margin-bottom': '20px'},
            
        )

        return row
    

    def infoGraphMetricsPut2(self):

        put_info = dbc.Col(
            [
                html.P('Put OI variations'),
                html.Div(id='metrics-info-put-var-div', children='--'),
            ],
            width='100%',
        )

        row = dbc.Row(
            [
                put_info
            ],
            style={'margin-top': '20px', 'margin-bottom': '20px'},
            
        )

        return row
    
    def volumesType(self):

        select_box = dcc.Dropdown(
            id="metrics-OI-vol-type-2-dd",
            options=[
                {"label": 'Volume', "value": 'volume'},
                {"label": 'OI', "value": 'oi'},
                {"label": 'Volume + OI', "value": 'volAndOI'},
            ],
            value='',
            optionHeight=25,
            disabled=True,
            placeholder="Select Volume Type",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box


    def importEarlierDate(self):
    
        select_box = dcc.Dropdown(
            id="metrics-import-earlier-date",
            options=[],
            optionHeight=25,
            disabled=True,
            placeholder="Select Other Expiration",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def importEarlierHour(self):

        select_box = dcc.Dropdown(
            id='metrics-import-earlier-hour',
            optionHeight=25,
            disabled=True,
            placeholder="Select Hour",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box

    def expirationOItype2(self):
    
        select_box = dcc.Dropdown(
            id="metrics-peak-isolated-2-dd",
            options=[
                {'label': 'All', 'value': 'All', 'disabled': False},
                {'label': 'Peak', 'value': 'Peak', 'disabled': False},
                {'label': 'Specific', 'value': 'Specific', 'disabled': False}
            ],
            optionHeight=25,
            disabled=True,
            placeholder="Select Expiration Filter",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def expirationOIDrowDown2(self):

        select_box = dcc.Dropdown(
            id='metrics-exp-oi-2-dd',
            optionHeight=25,
            disabled=True,
            placeholder="Select expiration",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box

    def strikeOIRangeSlider2(self):

        content = dcc.RangeSlider(
            id='metrics-strike-oi-2-rgs',
            min=0,
            max=100,
            pushable=1,
            tooltip={"placement": "bottom", "always_visible": True},
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return content

    def graphMetricsCall2(self):

        content = dcc.Graph(
            id='metrics-OI-call-chart',
            style={'height': '500px', 'width': '100%'}, 
            config={
                'scrollZoom': True, 
                'doubleClick': 'reset',
                'displaylogo': False, 
                'modeBarButtonsToAdd': [
                    'pan2d',
                    'zoomIn2d',
                    'zoomOut2d',
                    'toImage', 
                    'resetScale2d',
                    "v1hovermode",
                    "toggleSpikelines",
                    'hoverClosestCartesian',
                    'hoverCompareCartesian',
                ],
                'modeBarButtonsToRemove': [
                    'zoom2d', 'select2d', 'lasso2d',
                    'autoScale2d',
            
                ],
            },
        )
        return content
    
    def graphMetricsPut2(self):

        content = html.Div( 
            dcc.Graph(
                id='metrics-OI-put-chart',
                style={'height': '500px', 'width': '100%'},  
                config={
                    'scrollZoom': True,  
                    'doubleClick': 'reset',
                    'displaylogo': False, 
                    'modeBarButtonsToAdd': [
                        'pan2d',
                        'zoomIn2d',
                        'zoomOut2d',
                        'toImage', 
                        'resetScale2d',
                        "v1hovermode",
                        "toggleSpikelines",
                        'hoverClosestCartesian',
                        'hoverCompareCartesian',
                    ],
                    'modeBarButtonsToRemove': [
                        'zoom2d', 'select2d', 'lasso2d',
                        'autoScale2d',
                
                    ],
                },
            )
        )
        return content
    

##########################################################################################
##########################################################################################
###    TAB -> Implied Volatility
##########################################################################################
##########################################################################################

class MetricsIV:
    def __init__(self):

        self.IVSmileStrikeLayout = IVSmileStrikeLayout()
        self.IVDeltaSkewMetrics = IVDeltaSkewMetrics()
        self.IVSurfaceStrikeLayout = IVSurfaceStrikeLayout()
        

    def layout(self):

        row1a = dbc.Row(
            [
                self.IVSmileStrikeLayout.SetUpOptions()
            ],
            justify='start',
        )

        row2a = dbc.Row(
            [
                self.IVSmileStrikeLayout.plotGraphParams(),
            ],
            justify='start',
        )

        row1b = dbc.Row(
            [
                self.IVDeltaSkewMetrics.setParams(),
            ],
            justify='start',
        )

        row2b = dbc.Row(
            [
                self.IVDeltaSkewMetrics.graphMetricsIvDeltaSkewStrike(),
            ]
        )

        row1d = dbc.Row(
            [
                self.IVSurfaceStrikeLayout.SetUpSurfaceOptions(),
            ],
            justify='start',
        )

        row2d = dbc.Row(
            [
                self.IVSurfaceStrikeLayout.graphMetricsIvSurface(),
            ],
            justify='start',
        )


        content = dbc.Container(
            [
                html.H2("IV Indicators"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                row1b,
                                dcc.Loading(
                                    [
                                        html.Div(row2b, style={'position': 'relative', 'width': '100%'})  
                                    ],
                                    overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                                    custom_spinner=dbc.Spinner(color="info"),
                                )
                            ],
                            title='IV relative to Realized Vol. & 25-Delta Skew Indicators',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
                html.H2("IV Smile (Strike)"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                row1a,
                                dcc.Loading(
                                [    
                                    row2a,
                                ],
                                overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                                custom_spinner=dbc.Spinner(color="info"),
                                ),
                            ],
                            title='IV relative to strike prices',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),

                html.H2("IV Surface"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                row1d,
                                dcc.Loading(
                                [    
                                    row2d,
                                ],
                                overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                                custom_spinner=dbc.Spinner(color="info"),
                                ),
                            ],
                            title='Targeting a Specific Option',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
            ],
            fluid=True,  
            style={'margin-left':'0px'}
        )

        return content

###    Layout IV Smile

class IVSmileStrikeLayout:

    def __init__(self):
        pass

    def SetUpOptions(self):

        selection_type = dbc.Col(
            children=[
                html.P('Type Selection'),
                html.Div(self.selectionTypeIV1())
            ],
        )

        select_exp = dbc.Col(
            children=[
                html.P('Expiration(s)'),
                html.Div(self.expirationIVDrowDown1(), )
            ],
        )

        select_st = dbc.Col(
            children=[
                html.P('Underlying Date'),
                html.Div(self.selectionSt(), style={'margin-top': '25px'}),
            ],
        )

        load_another_date = dbc.Col(
            children=[
                html.P('Retrieve Another Trading Date'),
                html.Div(self.importEarlierDate(), )
            ],
        )

        load_another_hour = dbc.Col(
            children=[
                html.P('Load Market Hour'),
                html.Div(self.importEarlierHour(), )
            ],
        )

        select_exp_2 = dbc.Col(
            children=[
                html.P('Expiration (s)'),
                html.Div(self.expirationIVDrowDown2(), )
            ],
        )



       
        row1 = dbc.Row(
            [
                dbc.Col(selection_type),
                dbc.Col(select_exp),
                dbc.Col(select_st)
            ],
        )

        row2 = dbc.Row(
            [
                dbc.Col(load_another_date),
                dbc.Col(load_another_hour),
                dbc.Col(select_exp_2),
            ],
        )


        row = dbc.Row(
            [
                row1,
                row2,
            ],
                style={'margin-top':'20px', 'gap':'40px'}
                )
        
        return row
    
    def plotGraphParams(self):

        graph_iv = dbc.Col(
            [
                html.Div(self.graphMetricsIvStrike())
            ],
        )


        smooth_methods = dbc.Col(
            children=[
                html.P('Smooth Method'),
                html.Div(self.smoothMethodDrowDown())
            ],
        )

        moneyness = dbc.Col(
            children=[
                html.P('Moneyness'),
                html.Div(self.showMoneynessDrowDown())
            ],
        )

        row = dbc.Row(
            [
                smooth_methods,
                moneyness,
            ]
        )


        content = dbc.Col(
            [
                graph_iv,
                row
            ]
        )

        return content

    def selectionTypeIV1(self):

        select_box = dcc.Dropdown(
            id='metrics-select-type-IV-1-dd',
            optionHeight=25,
            disabled=True,
            placeholder="Select Type",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box


    def selectionSt(self):

        switch = dbc.Checklist(
            id="metrics-st-selection-1-switch",
            options=[{"label": "", "value": True}],  
            value=[True], 
            switch=True,  
            style={"fontSize": "10px"},
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )
    
        return html.Div([
            switch,  
            html.Div("Moneyness on current date", className="switch-sub")  
        ], className="custom-switch-container")

    def expirationIVDrowDown1(self):

        select_box = dcc.Dropdown(
            id='metrics-exp-IV-1-dd',
            optionHeight=25,
            disabled=True,
            multi=True,
            placeholder="Select expiration(s)",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def expirationIVDrowDown2(self):

        select_box = dcc.Dropdown(
            id='metrics-exp-IV-2-dd',
            optionHeight=25,
            disabled=True,
            multi=True,
            placeholder="Select expiration(s)",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def importEarlierDate(self):
    
        select_box = dcc.Dropdown(
            id="metrics-import-earlier-date-IV",
            options=[],
            optionHeight=25,
            disabled=True,
            placeholder="Select Other Expiration",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def importEarlierHour(self):

        select_box = dcc.Dropdown(
            id='metrics-import-earlier-hour-IV',
            optionHeight=25,
            disabled=True,
            placeholder="Select Hour",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    
    def smoothMethodDrowDown(self):

        select_box = dcc.Dropdown(
            id='metrics-smooth-methods-IV-dd',
            options=[
                {"label": 'Raw Data', "value": 'Raw Data'},
                {"label": 'Interpolate', "value": 'interpolate'},
                {"label": 'Savgol', "value": 'savgol'},
            ],
            value='Raw Data',
            optionHeight=25,
            disabled=False,
            placeholder="Select Methods",
            searchable=False,
            search_value='',
            className='adapt_drop_down',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def showMoneynessDrowDown(self):

        select_box = dcc.Dropdown(
            id='metrics-moneyness-IV-dd',
            options=[
                {"label": 'All', "value": 'All'},
                {"label": 'OTM', "value": 'OTM'},
                {"label": 'ITM', "value": 'ITM'},
            ],
            value='All',
            optionHeight=25,
            disabled=False,
            placeholder="Select Methods",
            searchable=False,
            search_value='',
            className='adapt_drop_down',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def graphMetricsIvStrike(self):

        content = dcc.Graph(
            id='metrics-IV-strike-chart',
            style={'height': '600px', 'width': '100%'},  
            config={
                'scrollZoom': True,  
                'doubleClick': 'reset',
                'displaylogo': False, 
                'modeBarButtonsToAdd': [
                    'pan2d',
                    'zoomIn2d',
                    'zoomOut2d',
                    'toImage', 
                    'resetScale2d',
                    "v1hovermode",
                    "toggleSpikelines",
                    'hoverClosestCartesian',
                    'hoverCompareCartesian',
                ],
                'modeBarButtonsToRemove': [
                    'zoom2d', 'select2d', 'lasso2d',
                    'autoScale2d', 'resetScale2d',
                ],
            },
        )
        return content

###    Layout IV Skew Delta

class IVDeltaSkewMetrics:
    def __init__(self):
        pass


    def setParams(self):

        select_formula = dbc.Col(
            children=[
                html.P('Formula'),
                html.Div(self.selectFormula())
            ],
        )

        select_max_history = dbc.Col(
            children=[
                html.P('Max History'),
                html.Div(self.maxHistory())
            ]
        )

        content = dbc.Row(
            [
                dbc.Col(select_formula),
                dbc.Col(select_max_history),
            ]
        )

        return content


    def selectFormula(self):

        select_box = dcc.Dropdown(
            id='metrics-dskew-formula-IV-dd',
            options=[
                {"label": 'Delta Skew (30D)', "value": 'deltaSkew30'},
                {"label": 'Butterfly Skew (30D)', "value": 'bfDeltaSkew30'},
                {"label": 'ATM IV & Realized Vol (30D)', "value": 'IVvsRV30'},
                {"label": 'ATM IV & Realized Vol (Nearest Expiry)', "value": 'IVvsRVclosest'},
            ],
            value='',
            optionHeight=25,
            disabled=True,
            placeholder="Select Indicator",
            searchable=False,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def maxHistory(self):

        select_box = dcc.Dropdown(
            id='metrics-max-history-dskew-IV-dd',
            options=[
            ],
            value='',
            optionHeight=25,
            disabled=True,
            placeholder="Select max History",
            searchable=False,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    
    def graphMetricsIvDeltaSkewStrike(self):

        content = dcc.Graph(
            id='metrics-IV-delta-dskew-chart',
            style={'height': '600px', 'width': '100%'},  
            config={
                'scrollZoom': True,  
                'doubleClick': 'reset',
                'displaylogo': False, 
                'modeBarButtonsToAdd': [
                    'pan2d',
                    'zoomIn2d',
                    'zoomOut2d',
                    'toImage',  
                    'resetScale2d',
                    "v1hovermode",
                    "toggleSpikelines",
                    'hoverClosestCartesian',
                    'hoverCompareCartesian',
                ],
                'modeBarButtonsToRemove': [
                    'zoom2d', 'select2d', 'lasso2d',
                    'autoScale2d', 'resetScale2d',
                ],
            },
        )
        return content

###    Layout IV Surface

class IVSurfaceStrikeLayout:

    def __init__(self):
        pass


    def SetUpSurfaceOptions(self):

        selection_type = dbc.Col(
            children=[
                html.P('Expiration Type'),
                html.Div(self.selectionTypeIV2())
            ],
        )

        select_expiration = dbc.Col(
            children=[
                html.P('Expiration'),
                html.Div(self.selectSurfaceExpirationIV(), )
            ],
        )


        select_range = dbc.Col(
            children=[
                html.P('Strike'),
                html.Div(self.strikeOIRangeSlider(), )
            ],
        )

        select_option_type = dbc.Col(
            children=[
                html.P('Option Type'),
                html.Div(self.selectOptionTypeIV(), )
            ],
        )

        row1 = dbc.Row(
            [
                dbc.Col(selection_type),
                dbc.Col(select_expiration),
                dbc.Col(select_option_type),
            ],
        )

        row2 = dbc.Row(
            [
                select_range
            ],
        )


        row = dbc.Row(
            [
                row1,
                row2
            ],
                style={'margin-top':'20px', 'gap':'40px'}
                )
        
        return row
    

    def selectionTypeIV2(self):

        select_box = dcc.Dropdown(
            id='metrics-surface-exp-type-IV-dd',
            options=[
                {"label": 'All', "value": 'All'},
                {"label": 'Peak', "value": 'Peak'},
                {"label": 'Custom Selection', "value": 'ItemChose'},
            ],
            value='All',
            optionHeight=25,
            disabled=False,
            placeholder="Select Expiration Type",
            searchable=False,
            search_value='',
            className='adapt_drop_down',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def selectSurfaceExpirationIV(self):

        select_box = dcc.Dropdown(
            id='metrics-surface-exp-IV-dd',
            options=[
            ],
            value='',
            optionHeight=25,
            disabled=True,
            placeholder="Select Expiration Type",
            searchable=False,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def selectOptionTypeIV(self):

        select_box = dcc.Dropdown(
            id='metrics-surface-options-type-IV-dd',
            options=[
                {"label": 'Call', "value": 'call'},
                {"label": 'Put', "value": 'put'},
                {"label": 'Both', "value": 'both'},
            ],
            value='call',
            optionHeight=25,
            disabled=False,
            placeholder="Select Options Type",
            searchable=False,
            search_value='',
            className='adapt_drop_down',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def strikeOIRangeSlider(self):

        content = dcc.RangeSlider(
            id='metrics-surface-IV-rgs',
            min=0,
            max=100,
            pushable=1,
            tooltip={"placement": "bottom", "always_visible": True},
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return content
    
    def graphMetricsIvSurface(self):

        content = dcc.Graph(
            id='metrics-IV-surface-chart',
            style={'height': '700px', 'width': '100%'},  
            config={
                'scrollZoom': True,  
                'doubleClick': 'reset',
                'displaylogo': False, 
                'modeBarButtonsToRemove': [
                    'zoom2d', 'pan2d', 'select2d', 'lasso2d',
                    'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d',
                    'hoverClosestCartesian', 'hoverCompareCartesian',
                    'toggleSpikelines', 
                ],
            },
        )
        return content

##########################################################################################
##########################################################################################
###   TAB -> Greeks Metrics
##########################################################################################
##########################################################################################

class MetricsGreeks:
    def __init__(self):
        self.GreeksGEXLayout = GreeksGEXLayout()

    def layout(self):

        row1a = dbc.Row(
            [
                self.GreeksGEXLayout.setParamsGEX()
            ],
            justify='start',
        )

        row1b = dbc.Row(
            [
                self.GreeksGEXLayout.graphMetricsNetGex()
            ],
            justify='start',
        )

        row1c = dbc.Row(
            [
                self.GreeksGEXLayout.graphMetricsAbsGex(),
            ],
            justify='start',
        )

        row2 = dbc.Row(
            [
                self.GreeksGEXLayout.graphMetricsDEX()
            ]
        )

        row3 = dbc.Row(
            [
                self.GreeksGEXLayout.graphMetricsVEX()
            ]
        )

        content = dbc.Container(
            [
                
                row1a,
                        
                 
                html.H2("Gamma Exposure"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                
                                dcc.Loading(
                                [    
                                    row1b,
                                ],
                                overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                                custom_spinner=dbc.Spinner(color="info"),
                                ),
                                dcc.Loading(
                                [    
                                    row1c,
                                ],
                                overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                                custom_spinner=dbc.Spinner(color="info"),
                                ),
                            ],
                            title='Gamma exposure relative to strike and volumes',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
                html.H2("Delta Exposure"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                dcc.Loading(
                                [    
                                    row2,
                                ],
                                overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                                custom_spinner=dbc.Spinner(color="info"),
                                ),
                            ],
                            title='Delta exposure across strikes',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
                html.H2("Vanna exposure"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                
                                dcc.Loading(
                                [    
                                    row3,
                                ],
                                overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                                custom_spinner=dbc.Spinner(color="info"),
                                ),
                            ],
                            title='Vanna exposure across strikes',
                        )
                    ],
                    style={'margin-top':'20px', 'margin-bottom':'20px'},
                ),
            ],
            fluid=True,  
            style={'margin-left':'0px'},
        )

        return content

###    Layout Gamma Exposure

class GreeksGEXLayout:
    def __init__(self):
        pass 


    def setParamsGEX(self):

        volume_type = dbc.Col(
            children=[
                html.P('Volume Type'),
                html.Div(self.selectionVolTypeGex())
            ]
        )

        expiration_type = dbc.Col(
            children=[
                html.P('Expiration Type'),
                html.Div(self.selectionTypeGexDD())
            ]
        )

        select_exp = dbc.Col(
            children=[
                html.P('Expiration'),
                html.Div(self.expirationGexDD())
            ]
        )

        range_strike = dbc.Col(
            children=[
                html.P('Strike'),
                html.Div(self.strikeGexRangeSlider(), style={'margin-top':'25px'})
            ],
            
        )


        row1 = dbc.Row(
            [
                dbc.Col(volume_type),
                dbc.Col(expiration_type),
                dbc.Col(select_exp),
            ]
        )

        row2 = dbc.Row(
            [
                dbc.Col(range_strike),
            ],
            style={'margin-top':'20px'},
        )

        content= dbc.Row(
            [
                row1,
                row2,
            ]
        )

        return content
    
    
    def selectionVolTypeGex(self):

        select_box = dcc.Dropdown(
            id='metrics-GEX-vol-type-dd',
            options=[
                {"label": 'Volume', "value": 'volume'},
                {"label": 'OI', "value": 'oi'},
                {"label": 'Volume + OI', "value": 'volAndOI'},
            ],
            value='',
            optionHeight=25,
            disabled=True,
            placeholder="Select Volume Type",
            searchable=False,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box

    def selectionTypeGexDD(self):

        select_box = dcc.Dropdown(
            id='metrics-exp-type-GEX-dd',
            options=[],
            value='',
            optionHeight=25,
            disabled=True,
            placeholder="Select Expiration Type",
            searchable=False,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box

    def expirationGexDD(self):

        select_box = dcc.Dropdown(
            id='metrics-exp-select-GEX-dd',
            optionHeight=25,
            disabled=True,
            placeholder="Select Expiration",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def strikeGexRangeSlider(self):

        content = dcc.RangeSlider(
            id='metrics-GEX-rgs',
            min=0,
            max=100,
            pushable=1,
            tooltip={"placement": "bottom", "always_visible": True},
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return content


    def graphMetricsNetGex(self):

        content = dcc.Graph(
            id='metrics-net-GEX-chart',
            style={'height': '600px', 'width': '100%'},  
            config={
                'scrollZoom': True, 
                'doubleClick': 'reset',
                'displaylogo': False, 
                'modeBarButtonsToAdd': [
                    'pan2d',
                    'zoomIn2d',
                    'zoomOut2d',
                    'toImage', 
                    'resetScale2d',
                    "v1hovermode",
                    "toggleSpikelines",
                    'hoverClosestCartesian',
                    'hoverCompareCartesian',
                ],
                'modeBarButtonsToRemove': [
                    'zoom2d', 'select2d', 'lasso2d',
                    'autoScale2d', 'resetScale2d',
                ],
            },
        )
        return content
    
    def graphMetricsAbsGex(self):

        content = dcc.Graph(
            id='metrics-abs-GEX-chart',
            style={'height': '600px', 'width': '100%'},  
            config={
                'scrollZoom': True,  
                'doubleClick': 'reset',
                'displaylogo': False, 
                'modeBarButtonsToAdd': [
                    'pan2d',
                    'zoomIn2d',
                    'zoomOut2d',
                    'toImage',  
                    'resetScale2d',
                    "v1hovermode",
                    "toggleSpikelines",
                    'hoverClosestCartesian',
                    'hoverCompareCartesian',
                ],
                'modeBarButtonsToRemove': [
                    'zoom2d', 'select2d', 'lasso2d',
                    'autoScale2d', 'resetScale2d',
                ],
            },
        )
        return content
    
    def graphMetricsDEX(self):

        content = dcc.Graph(
            id='metrics-DEX-chart',
            style={'height': '600px', 'width': '100%'},  
            config={
                'scrollZoom': True, 
                'doubleClick': 'reset',
                'displaylogo': False, 
                'modeBarButtonsToAdd': [
                    'pan2d',
                    'zoomIn2d',
                    'zoomOut2d',
                    'toImage', 
                    'resetScale2d',
                    "v1hovermode",
                    "toggleSpikelines",
                    'hoverClosestCartesian',
                    'hoverCompareCartesian',
                ],
                'modeBarButtonsToRemove': [
                    'zoom2d', 'select2d', 'lasso2d',
                    'autoScale2d', 'resetScale2d',
                ],
            },
        )
        return content




    def graphMetricsVEX(self):

        content = dcc.Graph(
            id='metrics-VEX-chart',
            style={'height': '600px', 'width': '100%'},  
            config={
                'scrollZoom': True, 
                'doubleClick': 'reset',
                'displaylogo': False, 
                'modeBarButtonsToAdd': [
                    'pan2d',
                    'zoomIn2d',
                    'zoomOut2d',
                    'toImage', 
                    'resetScale2d',
                    "v1hovermode",
                    "toggleSpikelines",
                    'hoverClosestCartesian',
                    'hoverCompareCartesian',
                ],
                'modeBarButtonsToRemove': [
                    'zoom2d', 'select2d', 'lasso2d',
                    'autoScale2d', 'resetScale2d',
                ],
            },
        )
        return content

##########################################################################################
###    TABS LAYOUT
##########################################################################################

class TabsLayout:
    def __init__(self, tab1, tab2, tab3, tab4):

        self.tab1 = tab1
        self.tab2 = tab2
        self.tab3 = tab3
        self.tab4 = tab4
    
    def layout(self):

        content = dbc.Tabs(
            [    
            dbc.Tab(self.tab1, label='Options Selection'),
            dbc.Tab(self.tab2, label='Volumes & OI'),
            dbc.Tab(self.tab3, label='Implied Volatility'),
            dbc.Tab(self.tab4, label='Greeks Analysis'),
            ],
            style={
                'margin-top': '30px',
                'margin-bottom': '20px',
                'width': '100%',
                'display': 'flex',
                'flex-wrap': 'nowrap',
            },
        )

        return content

##########################################################################################
###    FINAL LAYOUT
##########################################################################################

class MetricsPageFrame:

    def __init__(self):
        super().__init__()

        self.header = HeaderLayout().header()
        self.GlobalSetUpLayout = GlobalSetUpLayout().layout()
        
        #tabs list
        self.tabs1 = MetricsOptionsSelection().layout()
        self.tabs2 = MetricsPutCallOI().layout()
        self.tabs3 = MetricsIV().layout()
        self.tabs4 = MetricsGreeks().layout()

        self.TabsLayout = TabsLayout(self.tabs1, self.tabs2, self.tabs3, self.tabs4).layout()  

        self.layout = dbc.Col(
            [
            self.header,  
            self.GlobalSetUpLayout,
            self.TabsLayout
        ],
        style={'margin-left': '40px'}
        )
    
    def render(self):
        return self.layout  


def layout():
    return MetricsPageFrame().render()