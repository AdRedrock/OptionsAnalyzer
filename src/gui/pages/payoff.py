from datetime import date

import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

from src.import_data.utils import LoadingData

from src.config.constant import PERSISTENCE_TYPE


class HeaderLayout:
    def __init__(self):
        pass 
    
    def header(self):
        content = html.Div(
           
            children=[
                html.H1("Payoff Analyzer", className="head_title"),  
                html.Hr(className='head_divider'),
                dbc.Alert(id='payoff-msgbox', children='defaul msg', color='info', is_open=False, dismissable=True, fade=True, class_name='alert-dismissible'),
                dcc.Store(id="payoff-stats-trigger")
            ]
        )
        return content


##########################################################################################
##########################################################################################
###    SET-UP Layout (Data imported)
##########################################################################################
##########################################################################################

class SetUpLayout:
    def __init__(self):
        self.class_LoadingData = LoadingData()
        self.already_imported = self.class_LoadingData.load_existing_symbols()
        pass

    def layout(self):

        content = dbc.Col(
            children=[
                html.Div(self.strategiesDropDown()),
                html.Div(self.tickerDropDown()),
                html.Div(self.dateImportedDropDown()),
                html.Div(self.hourImportedDropDown()),
                self.showDayExpiration(),
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

    def strategiesDropDown(self):


        select_box = dcc.Dropdown(
            id='strategy-selection',
            options=[
                {'label': 'Simple Payoff', 'value':'simplePayoff'},
                {'label': 'Multi Payoff', 'value':'openPayoff'},
            ],
            optionHeight=25,
            disabled=False,
            placeholder="Select a strategie",
            searchable=True,
            search_value='',
            className='drop_down',
        )

        return select_box
    

    def tickerDropDown(self):

        dropdown_options = [{"label": option, "value": option} for option in self.already_imported]

        select_box = dcc.Dropdown(
            id='option-selection',
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
            id='imported-date-selection',
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
            id='imported-date-hour-selection',
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
            id="payoff-show-days-switch",
            options=[{"label": "", "value": True}],  
            value=[True], 
            switch=True,  
            style={"fontSize": "10px"},
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )
    
        return html.Div([
            switch,  # Le switch à gauche
            html.Div("Expiry (Days)", className="switch-sub")  # Le titre à droite
        ], className="custom-switch-container")

    def spinnerLoading(self):
        spinner = dbc.Spinner(
            html.Div(id='loading-output', children='default', style={'color': 'var(--customBgColor)', 'margin-top':'12px'}),
            color='info'
        )
        return spinner

##########################################################################################
##########################################################################################
###    SET-OPTION
##########################################################################################
##########################################################################################

class SetOptions:
    def __init__(self):
        pass

    def layout(self):

        content = dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    dcc.Loading(
                        id="payoff-loading-options",
                        children=dbc.Col(
                            [
                                self.OptionsBox(),
                            ],
                            id='container-set-options',
                        ),
                        overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                        custom_spinner=dbc.Spinner(color="info"), # Style discret
                    )
                ],
                title='Set options parameters'
            )
        ],
        start_collapsed=True,
        style={'margin-top': '20px'},
        className="custom-accordion",
    )

        return content

    def OptionsBox(self):

        return html.Div([  
         
            html.Div([
                html.Div(self.addOption()),
                html.Hr(),
                dcc.Store(id='options-select-df'),
                dcc.Store(id='options-select-df-filtred'),
                dcc.Store(id='options-selected-store', data=[]),
                html.Div(id='selected-options-container'),
            ], 
            className='container_radius'  
            )
        ])

    def addOption(self):

        col1 = dbc.Col(
            children=[

                html.P(self.buttonAddOption())
            ],
            width=1  
        )

        col2 = dbc.Col(
            children=[
                html.P('Call/Put'),
                html.Div(self.callPutDropDown())
            ],
            width=2
        )

        col3 = dbc.Col(
            children=[
                html.P('Position'),
                html.Div(self.positionDropDown())
            ],
            width=2
        )


        col4 = dbc.Col(
            children=[
                html.P('Strike'),
                html.Div(self.strikeDropDown())
            ],
            width=2
        )

        col5 = dbc.Col(
            children=[
                html.P('Premium'),
                html.Div(self.premiumDropDown())
            ],
            width=2
        )

        col6 = dbc.Col(
            children=[
                html.P('Expiration'),
                html.Div(self.maturityDropDown())
            ],
            width=2
        )

        content = dbc.Row(children=[
            col1,
            col2,
            col3,
            col4,
            col5,
            col6,
        ],
        )

        return content

    def callPutDropDown(self):
        select_box = dcc.Dropdown(
            id='type-selection',
            optionHeight=25,
            disabled=True,
            placeholder="Select Type",
            searchable=False,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box
    
    def positionDropDown(self):
        select_box = dcc.Dropdown(
            id='pos-selection',
            options=[
                {'label': 'Long', 'value': 'Long', 'disabled': False},
                {'label': 'Short', 'value': 'Short', 'disabled': False}
            ],
            optionHeight=25,
            disabled=True,
            placeholder="Long/Short",
            searchable=False,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box

    def strikeDropDown(self):
        select_box = dcc.Dropdown(
            id='strike-selection',
            optionHeight=25,
            disabled=True,
            placeholder="Select Strike",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )
        
        return select_box
    
    def premiumDropDown(self):
        select_box = dcc.Dropdown(
            id='premium-selection',
            optionHeight=25,
            disabled=True,
            placeholder="Select Premium",
            searchable=True,
            search_value='',
            className='adapt_drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )
        
        return select_box

    def maturityDropDown(self):
        select_box = dcc.Dropdown(
            id='maturity-selection',
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
    
    def rowContainerSelected(self, row_id, call_put_value, position_value, strike_value, premium_value, maturity_value):

        col1 = dbc.Col(
            children=[

                html.P(self.buttonDelOption(row_id))
            ],
            width=1,  
        )

        col2 = dbc.Col(
            children=[
                html.P('Call/Put'),
                html.Div(call_put_value)
            ],
            width=2,
        )

        col3 = dbc.Col(
            children=[
                html.P('Position'),
                html.Div(position_value)
            ],
            width=2,
        )


        col4 = dbc.Col(
            children=[
                html.P('Strike'),
                html.Div(strike_value)
            ],
            width=2,
        )

        col5 = dbc.Col(
            children=[
                html.P('Premium'),
                html.Div(premium_value)
            ],
            width=2
        )

        col6 = dbc.Col(
            children=[
                html.P('Expiration'),
                html.Div(maturity_value)
            ],
            width=2
        )

        content = dbc.Row(children=[
            col1,
            col2,
            col3,
            col4,
            col5,
            col6,
        ],
        id=f'selected-stored-line-{row_id}',
        )

        return content
      

    def buttonAddOption(self):
        return html.Button(
            
            [
                html.I(className='bi bi-plus-square-fill'),
            ],
            id='add-options-selection',
            n_clicks=0,
            className='add_button',
        )
    
    def buttonDelOption(self, row_id):

        return html.Button(
            
        [
            
            html.I(className='bi bi-x-circle'),

        ],
        id={'type': 'del-options-btn', 'index': row_id},
        n_clicks=0,
        className='delete_button',)

##########################################################################################    
##########################################################################################
###    PAYOFF PLOT LAYOUT
##########################################################################################
##########################################################################################

class PlotOptionsLayout:
    def __init__(self):
        pass

    def layout(self):
     
        content = html.Div([self.plotPayoff()])
        
        col = dbc.Col(
            [
                dcc.Loading(
                    [
                        content
                    ],
                    overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                    custom_spinner=dbc.Spinner(color="info"),
                ),
                self.cards()
            ]
        )

        return col
    
    def plotPayoff(self):
      
        content = dcc.Graph(
            id='payoff-chart',
            style={'height': '500px', 'width': '100%'},
            config={
                'scrollZoom': True,  # Active le zoom par défilement
                'doubleClick': 'reset',
                'displaylogo': False, 
                'modeBarButtonsToAdd': [
                    'pan2d',
                    'zoomIn2d',
                    'zoomOut2d',
                    'toImage',  # Ajouter le bouton pour exporter le graphique en image
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
    
    def cards(self):
        """Création des cartes pour les métriques clés."""

        card_pl = dbc.Card(
            [
                dbc.CardHeader('Current P&L'),
                dbc.CardBody(html.P('_p&l', id='pl-value', className='card-text'))
            ]
        )

        card_breakeven = dbc.Card(
            [
                dbc.CardHeader('Break Even'),
                dbc.CardBody(html.P('_nbr', id='breakeven-value', className='card-text'))
            ]
        )

        card_max_gain = dbc.Card(
            [
                dbc.CardHeader('Max Profit (On chart)'),
                dbc.CardBody(html.P('_max_profit', id='max-gain-value', className='card-text'))
            ]
        )

        card_max_loss = dbc.Card(
            [
                dbc.CardHeader('Max Losses (On chart)'),
                dbc.CardBody(html.P('_max_losses', id='max-loss-value', className='card-text'))
            ]
        )

        card_st_var = dbc.Card(
            [
                dbc.CardHeader('Min St Variation to BE'),
                dbc.CardBody(html.P('_st_var', id='st-var-value', className='card-text'))
            ]
        )

        row = dbc.Row(
            [
                dbc.Col(card_pl, width=2),
                dbc.Col(card_max_gain, width=2),
                dbc.Col(card_max_loss, width=2),
                dbc.Col(card_breakeven, width=2),
                dbc.Col(card_st_var, width=2),
            ],
            justify="between",
            className="g-3"  
        )

        return row
    
##########################################################################################
##########################################################################################
###    MONTE CARLO SIMULATION LAYOUT
##########################################################################################
##########################################################################################

class MonteCarloSimulation:
    def __init__(self):
        pass

    def layout(self):
      
        row1 = dbc.Row(
            [
                dbc.Col(self.switchAuto(), width="auto"),
                dbc.Col(html.Div(self.datePickerRange()), width="auto", style={'min-width': '150px'}),
                dbc.Col(html.Div(self.InputMu()), width="auto"),
            ],
            className="g-3",  
            style={'margin-bottom': '20px'}  
        )

        row1b = dbc.Row(
            [
                dbc.Col(self.switchIv(), width="auto", style={'margin-right':'35px'}),
                dbc.Col(html.Div(self.InputSig()), width="auto", style={'margin-right':'10px'}),
                dbc.Col(html.Div(self.SigDrowDown()), width="auto"),
                dbc.Col(html.Div(self.maturitySelection()), width="auto"),
                dbc.Col(html.Div(self.nbSimulation()), width="auto"),
                dbc.Col(html.Div(self.launchSimButton()), width="auto"),
            ],
            className="flex-nowrap",
            style={'margin-bottom':'10px'}
        )

        col1 = dbc.Col(
            [
                dcc.Loading(
                    id="payoff-loading-distribution",
                    children=[
                        html.Div(self.plotDistribution()),
                    ],
                    overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                    custom_spinner=dbc.Spinner(color="info"),
                )
            ],
            width='100%',
        )

        row2 = dbc.Row(
            [
                col1,
            ],
            style={'margin-left':'0px'},
        )

        row3 = dbc.Container(
            [
                dbc.Row(  
                    [
                        self.cards()
                    ],
                    className='container_radius',
                    justify="between",  
                )
            ],
            fluid=True  
        )

        row4 = dbc.Row(
            [
                dcc.Loading(
                    id="payoff-loading-track",
                    children=[
                        html.Div([self.plotSimulation()]),
                    ],
                    overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                    custom_spinner=dbc.Spinner(color="info"),
                )
            ],
        )

        content = dbc.Container(
            [
                row1,
                row1b,
                row2,
                row3,
                row4
                
            ],
            fluid=True,  
        )

        content = dbc.Container(
            [
                row1,
                row1b,
                dcc.Loading(
                    id="payoff-loading-sim",
                    children=dbc.Container(
                        [
                            row2,
                            row3,
                            row4
                        ]
                    ),
                    style={'margin-left':'0px'},
                    overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                    custom_spinner=dbc.Spinner(color="info"), # Style discret
                ),
                
            ],
            fluid=True,  
        )

        return content


    def switchAuto(self):
        switch = dbc.Checklist(
            id="payoff-auto-stats-switch",
            options=[{"label": "", "value": True}],  
            value=[True], 
            switch=True,  
            style={"fontSize": "10px"},
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )
    
        return html.Div([
            switch,  
            html.Div("Auto", className="switch-title")  
        ], className="custom-switch-container")
    
    def switchIv(self):
        switch = dbc.Checklist(
            id="payoff-custom-iv-switch",
            options=[{"label": "", "value": True}],  
            value=[], 
            switch=True,  
            style={"fontSize": "10px"},
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )
    
        return html.Div([
            switch,  
            html.Div("IV", className="switch-title")  
        ], className="custom-switch-container")

    
    def datePickerRange(self):
        content = html.Div(
            [  
            dcc.DatePickerRange(
                id='payoff-sim-range-date-picker',
                max_date_allowed = date.today(),
                display_format='YYYY-MM-DD',
                className="mb-4",
            ),
            ],
            className="dbc",
        )

        return content

    def maturitySelection(self):

        content = dcc.Dropdown(
            id='payoff-sim-exp-dd',
            options=[],
            optionHeight=25,
            disabled=False,
            placeholder="Simulation Time",
            searchable=False,
            search_value='',
            className='drop_down_disabled',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return content

    def InputMu(self):
        content = html.Div(
            [
                dbc.Input(
                    id='payoff-mu-input',
                    placeholder='Select µ (annualized %)',
                    disabled=True,
                    type='text',
                    
                    ),
                dbc.Tooltip(
                "Enter the annualized yield (µ) format example : 25.57 % ",  
                target="payoff-mu-input",
                ),
            ],
            className='input_field',
        )

        return content

    def InputSig(self):

        content = html.Div(
            
            [
                dbc.Input(
                    id='payoff-sig-input',
                    placeholder='Select σ (annualized)',
                    disabled=False,
                    type='text',
                    ),
                dbc.Tooltip(
                "Enter the annualized volatility (σ) format example : 25.57 % ", 
                target="payoff-sig-input",
                ),
            ],
            className='input_field',
            id='payoff-sig-input-div',
        )

        return content
    
    def SigDrowDown(self):

        content = dcc.Dropdown(
            id='payoff-iv-dd',
            options=[],
            optionHeight=25,
            disabled=True,
            placeholder="Select IV as σ",
            searchable=False,
            search_value='',
            className='drop_down_disabled',
        )

        return content
    
    
    def nbSimulation(self):

        content = dcc.Dropdown(
            id='payoff-nbsim-dd',
            options=[
                {'label': '500', 'value':'500'},
                {'label': '1,000', 'value':'1000'},
                {'label': '5,000', 'value':'5000'},
                {'label': '10,000', 'value':'10000'},
                {'label': '25,000', 'value':'25000'},
                {'label': '50,000', 'value':'50000'},
            ],

            optionHeight=25,
            disabled=False,
            placeholder="Simulation Number",
            searchable=False,
            search_value='',
            className='drop_down',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )


        return content
    
    def launchSimButton(self):

        button = html.Button(
            
            [
                html.I(className='bi bi-rocket-takeoff'),
            ],
            id='payoff-launch-sim-button',
            n_clicks=0,
            disabled=False,
            className='check_st_button',
            title="Launch Simulation"
        )


        return button

    def plotSimulation(self):
      
        content = dcc.Graph(
            id='payoff-sim-chart',
            style={'height': '600px', 'width': '100%'},  
            figure=self.defaultFigure(),
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

    def plotDistribution(self):
      
        content = dcc.Graph(
            id='payoff-distrib-chart',
            style={'height': '600px', 'width': '100%'}, 
            figure=self.defaultFigure(),
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
    
    def defaultFigure(self):

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
            dragmode='pan',
        )
    
        return fig
    
    def cards(self):
        """Création des cartes pour les métriques clés."""


        card_params = dbc.Col(
            [
                html.P('Model Parameters'),
                html.Div(id='payoff-model-param-div', children='--'),
            ],
            width=4
        )

        card_globals = dbc.Col(
            [
                html.P('Globals'),
                html.Div(id='payoff-stats-globals-div', children='--')
            ],
            width=4
        )

        card_stats = dbc.Col(
            [
                html.P('Statistics'),
                html.Div(id='payoff-statistics-div', children='--')
            ],
            width=4
        )


        row = dbc.Row(
            [
                card_params,
                card_globals,
                card_stats
            ],
            style={'margin-top': '20px', 'margin-bottom': '20px'},
            
        )

        return row

    
##########################################################################################
###    TABS LAYOUT
##########################################################################################

class TabsLayout:
    def __init__(self, tab1, tab2):

        self.tab1 = tab1
        self.tab2 = tab2
    
    def layout(self):


        content = dbc.Tabs(
            [    
            dbc.Tab(self.tab1, label='Payoff Chart'),
            dbc.Tab(self.tab2, label='Monte Carlo Simulation'),
            ],
            style={
                'margin-top': '20px',
                'margin-bottom': '20px',
                'width': '100%',
                'display': 'flex',
                'flex-wrap': 'nowrap',
            },
            className="tabs-container"
        )

        return content
    
##########################################################################################
###    MAIN LAYOUT
##########################################################################################

class PayoffPageFrame:

    def __init__(self):
        super().__init__()

        self.header = HeaderLayout().header()
        self.setup = SetUpLayout().layout()
        self.setOptions = SetOptions().layout()
        
        #tabs list
        self.tabs1 = PlotOptionsLayout().layout()
        self.tabs2 = MonteCarloSimulation().layout()

        self.TabsLayout = TabsLayout(self.tabs1, self.tabs2).layout()

        self.layout = dbc.Col([
            self.header,  
            self.setup,
            self.setOptions,
            # self.plotOptions
            self.TabsLayout
        ],
        style={'margin-left': '40px'}
        )
    
    def render(self):
        return self.layout  


def layout():
    return PayoffPageFrame().render()
