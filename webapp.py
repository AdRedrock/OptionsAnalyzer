from dash import Dash, html, dcc, Input, State, Output
import dash_bootstrap_components as dbc
from src.gui.pages.sidebar import SideBar

from src.gui.pages.marketMetrics import layout as metrics_layout
from src.gui.pages.payoff import layout as payoff_layout
from src.gui.pages.importData import layout as import_layout
from src.gui.pages.settings import layout as settings_layout

import src.gui.callbacks.callBackSettings
import src.gui.callbacks.callBackImportData
import src.gui.callbacks.callBackMarketMetrics
import src.gui.callbacks.callBackPayoff

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

app = Dash(
    __name__,
    title='Options Analyzer',
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP, "assets/styles.css", dbc_css],
    suppress_callback_exceptions=True,
)

sidebar = SideBar()
app.css.config.serve_locally = True

app.layout = html.Div([
    dcc.Location(id='url', refresh=False, pathname='/metrics'),

    html.Div([
     
        html.Div(
            sidebar.sidebar(),
            id="sidebar",
        ),

        html.Div(
            sidebar.sidebarCanvas(),
        ),

        html.Div([
            html.Div(
                id='metrics-container',
                style={'display': 'none'},
                children=metrics_layout() if callable(metrics_layout) else metrics_layout
            ),
            html.Div(
                id='payoff-container',
                style={'display': 'none'},
                children=payoff_layout() if callable(payoff_layout) else payoff_layout
            ),
            html.Div(
                id='import-container',
                style={'display': 'none'},
                children=import_layout() if callable(import_layout) else import_layout
            ),
            html.Div(
                id='settings-container',
                style={'display': 'none'},
                children=settings_layout() if callable(settings_layout) else settings_layout
            ),
        ], 
        id="main-content",
        style={
            "margin-left": "50px",  
            "margin-right": "20px", 
            "padding": "20px",
        })
    ])
])



@app.callback(
    Output("sidebar-offcanvas", "is_open", allow_duplicate=True),
    Input("sidebar-canvas-button", "n_clicks"),
    [State("sidebar-offcanvas", "is_open")],
    prevent_initial_call=True  # Add this to prevent the callback from firing on initial page load
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(
    [Output('metrics-container', 'style'),
     Output('payoff-container', 'style'),
     Output('import-container', 'style'),
     Output('settings-container', 'style')],
    Input('url', 'pathname')
)
def display_page(pathname):
    hiding_style = {'display': 'none'}
    showing_style = {'display': 'block'}
    
    styles = [hiding_style, hiding_style, hiding_style, hiding_style]
    
    if pathname == '/metrics':
        styles[0] = showing_style
    elif pathname == '/payoff':
        styles[1] = showing_style
    elif pathname == '/import':
        styles[2] = showing_style
    elif pathname == '/settings':
        styles[3] = showing_style
    
    return styles

if __name__ == '__main__':
    app.run(debug=True)