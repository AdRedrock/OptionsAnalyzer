import dash

from dash import Input, Output

from src.import_data.utils import LoadingData

class GlobalsSettingsCallBack:
    def __init__(self):
        pass

##########################################################################################
###    CALL BACK Timezone Settings
##########################################################################################

    @dash.callback(
            Output('settings-msgbox', 'children'),
            Output('settings-msgbox', 'color'),
            Output('settings-msgbox', 'is_open'),
            Input('settings-timezone-selection', 'value'),
    )
    def update_timeZoneDropDown(new_timezone):

        LoadingData().change_settings_json(new_timezone)

        message = f'Time zone is set to {new_timezone}'
        color = 'info'

        return message, color, True