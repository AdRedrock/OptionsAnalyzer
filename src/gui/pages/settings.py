import dash_bootstrap_components as dbc
from dash import html, dcc

from src.config.constant import PERSISTENCE_TYPE, UTC_DICT
from src.import_data.utils import LoadingData

class HeaderLayout:
    def __init__(self):
        pass 
    
    def header(self):
        content = html.Div(
         
            children=[
                html.H1("Settings", className="head_title"),  
                html.Hr(className='head_divider'), 
                dbc.Alert(id='settings-msgbox', children='Test', color="info", is_open=False, dismissable=True, fade=True, class_name='alert-dismissible'),
            ]
        )
        return content
    

class GlobalSettings:
    def __init__(self):
        self.class_LoadingData = LoadingData()
        self.current_timezone = self.class_LoadingData.load_settings_json()


    def layout(self):

        row = dbc.Col(
            children=[
                html.H2("Time Zone"),
                html.Div(self.timeZoneDropDown())
            ],
            style={'gap':'20px'},
        ),
           
        content = html.Div(row)

        return content

    def timeZoneDropDown(self):

        dropdown_options = [{"label": key, "value": UTC_DICT[key]} for key in UTC_DICT]

        select_box = dcc.Dropdown(
            id='settings-timezone-selection',
            value=self.current_timezone,
            options=dropdown_options,
            optionHeight=25,
            disabled=False,
            placeholder="Select a timezone",
            searchable=True,
            search_value=self.current_timezone,
            className='drop_down',
            persistence=True,
            persistence_type=PERSISTENCE_TYPE,
        )

        return select_box

##########################################################################################
###    FINAL LAYOUT
##########################################################################################

class SettingsPageFrame:

    def __init__(self):
        super().__init__()

        self.header = HeaderLayout().header()
        self.GlobalSettings = GlobalSettings().layout()

        self.layout = dbc.Col(
            [
            self.header, 
            self.GlobalSettings 
        ],
        style={'margin-left': '40px'}
        )
    
    def render(self):
        return self.layout  


def layout():
    return SettingsPageFrame().render()


