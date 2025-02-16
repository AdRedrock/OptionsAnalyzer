import dash_bootstrap_components as dbc
from dash import html

class SideBar:
    def __init__(self):
        pass

    def sidebar(self):

        sidebar = html.Div(
                [
                    html.Div(self.buttonOpenCanvas()),
                    html.Hr(className='sidebar_divider'),
                    dbc.Nav(
                        [
                            dbc.NavLink(
                                        [html.I(className='bi bi-pie-chart-fill', style={"margin-right": "10px", "font-size": "20px"})], 
                                        href='/metrics', 
                                        active='exact'),

                            dbc.NavLink(
                                        [html.I(className='bi bi-graph-up', style={"margin-right": "10px", "font-size": "20px"})], 
                                        href='/payoff', 
                                        active='exact'),

                            dbc.NavLink(
                                [html.I(className='bi bi-database-fill-down', style={"margin-right": "10px", "font-size": "20px"})], 
                                        href='/import', 
                                        active='exact'),
                            dbc.NavLink(
                                [html.I(className='bi bi-gear-fill', style={"margin-right": "10px", "font-size": "20px"})], 
                                        href='/settings', 
                                        active='exact'),
                        ],
                        vertical=True,
                        pills=True,
                    ),
                ],
                className="sidebar_style", 
            )
        
        return sidebar


    def buttonOpenCanvas(self):
        button = html.Button(
            [
                html.I(className='bi bi-list', style={'font-size': '30px'}),
            ],
            id='sidebar-canvas-button',
            n_clicks=0,
            className="sidebar-open-button",  
            style={
                'margin-bottom': '20px',
                'display': 'flex',        
                'align-items': 'center', 
                'justify-content': 'center', 
                'gap': '4px'
            }
        )
        return button

    def sidebarCanvas(self):

        sidebar = html.Div(  
                dbc.Offcanvas(
                    html.Div(
                        [
                            html.H1('Options Analyzer', className='sidebar_title'),
                            html.Hr(className='sidebar_divider'),
                            dbc.Nav(
                                [
                
                                    dbc.NavLink(
                                                [html.I(className='bi bi-pie-chart-fill', style={"margin-right": "8px", "font-size": "20px"}),'Market Metrics'], 
                                                href='/metrics', 
                                                active='exact'),

                                    dbc.NavLink(
                                                [html.I(className='bi bi-graph-up', style={"margin-right": "8px", "font-size": "20px"}),'Pay-Off Analysis'], 
                                                href='/payoff', 
                                                active='exact'),

                                    dbc.NavLink(
                                        [html.I(className='bi bi-database-fill-down', style={"margin-right": "8px", "font-size": "20px"}), 'Import Data'], 
                                                href='/import', 
                                                active='exact'),
                                    dbc.NavLink(
                                        [html.I(className='bi bi-gear-fill', style={"margin-right": "8px", "font-size": "20px"}), 'Settings'], 
                                                href='/settings', 
                                                active='exact'),
                                ],
                                vertical=True,
                                pills=True,
                            ),
                        ],
                        className="offcanvas_sidebar_style", 
                    ),
                    scrollable=False,
                    id="sidebar-offcanvas",
                    is_open=False,
                    className="offcanvas_sidebar_style", 
                    style={'width':'19rem'},
            ),
            
            
        )
            
        return sidebar
    

