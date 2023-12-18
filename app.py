"""
Notes
-----
* Anything that is used as an input to a callback must be in this
"""
import logging
import time
from logging.handlers import WatchedFileHandler

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, callback, clientside_callback
from dash import html
from components.footer import FOOTER
from components.header import HEADER
from mp_data import get_data


APP_NAME = 'mp_tick_data'
DBC_CSS = 'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css'


def setup_logging():
    """Setup logging to file and console."""
    # Set up logging to file
    handler = WatchedFileHandler(f'{APP_NAME}.log')
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s', '%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel('DEBUG')
    # Remove existing handlers for this file name, if any
    for old_handler in [h for h in root.handlers if (isinstance(h, WatchedFileHandler)
                                                     and h.baseFilename == handler.baseFilename)]:
        root.handlers.remove(old_handler)
    root.addHandler(handler)
    return logging.getLogger(__name__)


PROFILE_INPUT = html.Div(
    dbc.Stack([
        dbc.Label("Profile URL", html_for="profile-url-input"),
        dbc.Input(id='profile-url-input',
                  placeholder='https://www.mountainproject.com/user/<user-id>/<first>-<last>',
                  type='url',
                  inputmode='url',),
        dbc.Button(html.I(className='fa-solid fa-arrows-rotate'), id='load-button', n_clicks=0),
    ],
        direction='horizontal', gap=1),
    style={'margin': '30px', })

TICK_TABLE = dag.AgGrid(
    id='table',
    rowData=get_data(None).to_dict('records'),
    columnDefs=[{'field': col} for col in get_data(None).columns],
    dashGridOptions={"rowSelection": "multiple"},
    style={'height': '100%'},
    defaultColDef={"flex": 1, "minWidth": 150, "sortable": True, "resizable": True, "filter": True},
)


APP = Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB, dbc.icons.FONT_AWESOME, DBC_CSS])
SERVER = APP.server
APP.layout = dbc.Container(
    children=[HEADER,
              PROFILE_INPUT,
              TICK_TABLE,
              FOOTER],
    fluid=True,
    className="dbc dbc-ag-grid",
    style={'height': '1000px'})


# --------------------------------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------------------------------
# This callback is used to update the data in the table. It is triggered by the load button and the
# profile url input.
@callback(Output('table', 'rowData'),
          Output('last_refresh', 'children'),
          Output('url', 'children'),
          Input('load-button', 'n_clicks'),
          Input('profile-url-input', 'value'))
def update_data(n, url: str):
    """Updates the data in the table. Triggered by the load button and the profile url input. If the
    url is empty, the table will be empty. If the url is not empty, the table will be populated with
    the data from the url. The url is expected to be a mountain project tick export url. 

    Parameters
    ----------
    n : int
        Number of times the load button has been clicked
    url : str
        Mountain project tick export url

    Returns
    -------
    DataFrame
        The data to be displayed in the table
    str
        The last refresh time
    str
        The url that was used to get the data
    """
    if url is not None and url.strip() != '':
        url = f'{url}/tick-export'
        print(f'getting data from {url}')
        t_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    else:
        t_str = ''
        url = ''

    return get_data(url).to_dict('records'), f'Last Refresh: {t_str}', str(url)


# --------------------------------------------------------------------------------------------------
# This callback is used to change from light mode to dark mode. It is triggered by the switch.
# --------------------------------------------------------------------------------------------------
clientside_callback(
    """
    (switchOn) => {
       switchOn
         ? document.documentElement.setAttribute('data-bs-theme', 'light')
         : document.documentElement.setAttribute('data-bs-theme', 'dark')
       return window.dash_clientside.no_update
    }
    """,
    Output("switch", "id"),
    Input("switch", "value"),
)

if __name__ == '__main__':
    APP.run_server(debug=True, host="0.0.0.0", port=8080, use_reloader=False)
