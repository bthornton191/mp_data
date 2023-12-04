import csv
import re
from pathlib import Path
import time

import pandas as pd
import plotly.express as px
import requests
from dash import Dash, Input, Output, callback, dcc, html, dash_table

from mp_data import get_first_sends, get_grade, get_subgrade, mpl_hist, px_hist

DATA_URL = 'https://www.mountainproject.com/user/{}/tick-export'
BEN_THORNTON_URL = DATA_URL.format('112795239/ben-thornton')


def get_data(url):
    # Read in the data from mountain project
    df = pd.DataFrame(csv.reader(requests.get(url).text.splitlines()))

    # Set the first line as the header
    df = df.set_axis(df.iloc[0], axis=1).iloc[1:]

    # Tweak the data
    df = (df
          .assign(**{'Grade': df['Rating'].apply(get_grade)})                                 # Get the number grade (e.g. 11)
          .assign(**{'Subgrade': df['Rating'].apply(get_subgrade)})                           # Get the letter grade (e.g. a)
          .assign(**{'Date': pd.to_datetime(df['Date'])})                                     # Get the year of the send
          .assign(**{'Style': df['Style'].str.lower()})                                       # Change values to lowercase
          .assign(**{'Lead Style': df['Lead Style'].str.lower()})                             # Change values to lowercase
          .assign(**{'Route Type': df['Route Type'].str.lower()})                             # Change values to lowercase
          [['Date', 'Route', 'Style', 'Lead Style', 'Route Type', 'Grade', 'Subgrade']])      # Keep only certain columns

    df['Grade'] = df['Grade'].astype(int)

    return df


df = get_data(BEN_THORNTON_URL)

app = Dash('mp_data')

columns = []
for col in df.columns:
    if col == 'Date':
        columns.append({'name': col, 'id': col, 'type': 'datetime'})
    elif col == 'Grade':
        columns.append({'name': col, 'id': col, 'type': 'numeric'})
    else:
        columns.append({'name': col, 'id': col, 'type': 'text'})

app.layout = html.Div([
    html.P(id='url',
           children=BEN_THORNTON_URL,
           style={'textAlign': 'right'}),
    html.P(id='last_refresh',
           children=f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}',
           style={'textAlign': 'right'}),
    html.H1(children='Mountain Project Data', style={'textAlign': 'center'}),
    dcc.Input(id='climber-input', value='112795239/ben-thornton', type='text'),
    html.Button('Load', id='load-button', n_clicks=0),
    dash_table.DataTable(
        id='table',
        data=df.to_dict('records'),
        columns=columns,
        filter_action='native',
        sort_action='native',
        sort_mode='multi',
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Route Type} = "sport"',
                    'column_id': 'Route Type'
                },
                'color': 'blue'
            },
            {
                'if': {
                    'filter_query': '{Route Type} = "trad"',
                    'column_id': 'Route Type'
                },
                'color': 'red'
            }
        ]
    ),
    # dcc.Interval(
    #     id='interval-component',
    #     interval=1*10000,  # in milliseconds
    #     n_intervals=1
    # ),

])


@callback(Output('table', 'data'), Output('last_refresh', 'children'), Output('url', 'children'),
          Input('load-button', 'n_clicks'), Input('climber-input', 'value'))
def update_data(n, climber: str):
    url = DATA_URL.format(climber.lower().replace(' ', '-'))
    print(f'getting data from {url}')
    df = get_data(url)
    return df.to_dict('records'), f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}', url


if __name__ == '__main__':
    app.run(debug=False)
