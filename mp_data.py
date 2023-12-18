import csv
import logging
import re

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

RE_YDS = re.compile(r'5\.(\d{1,2})\s*([abcd\+])?\s*R?', flags=re.IGNORECASE)
RE_VERMIN = re.compile(r'V(.+)\s*R?', flags=re.IGNORECASE)
COLUMNS = ['Date', 'Route', 'Style', 'Lead Style', 'Route Type', 'Grade', 'Subgrade']
LOG = logging.getLogger(__name__)


def get_data(url: str):

    if url is not None and url.strip() != '':
        # Read in the data from mountain project
        df = pd.DataFrame(csv.reader(requests.get(url).text.splitlines()))

        # Set the first line as the header
        df = df.set_axis(df.iloc[0], axis=1).iloc[1:]

        # Tweak the data
        df = (df
              .assign(**{'Grade': df['Rating'].apply(get_grade)})                                 # Get the number grade (e.g. 11)
              .assign(**{'Subgrade': df['Rating'].apply(get_subgrade)})                           # Get the letter grade (e.g. a)
              #   .assign(**{'Date': pd.to_datetime(df['Date'])})                                     # Get the year of the send
              .assign(**{'Style': df['Style'].str.lower()})                                       # Change values to lowercase
              .assign(**{'Lead Style': df['Lead Style'].str.lower()})                             # Change values to lowercase
              .assign(**{'Route Type': df['Route Type'].str.lower()})                             # Change values to lowercase
              [COLUMNS])      # Keep only certain columns

    else:
        df = pd.DataFrame(columns=COLUMNS)

    return df


def get_subgrade(rating):
    if (match := RE_YDS.match(rating)) is not None:
        try:
            groups = match.groups()
        except Exception:
            pass
        if len(groups) < 2:
            return None
        else:
            return groups[1]

    elif match := RE_VERMIN.match(rating) is not None:
        return None

    else:
        raise ValueError('Grade not recognized')


def get_grade(rating):
    if (match := RE_YDS.match(rating)) is not None:
        try:
            grade = int(match.groups()[0])
        except Exception:
            LOG.warning(f'Could not parse grade from {rating}')

    elif (match := RE_VERMIN.match(rating.replace('-easy', '0'))) is not None:
        grade = int(re.split('[-+]', match.groups()[0])[0])

    else:
        raise ValueError('Grade not recognized')

    return grade


def get_first_sends(df: pd.DataFrame, route_type=None):
    """Get a list of all the first-time sends.

    Parameters
    ----------
    df : DataFrame
        DataFrame of ticks
    route_type : str, optional
        Must be 'Sport', 'Trad', 'TR'. Set to None to return all., by default None

    Returns
    -------
    DataFrame
        DataFrame of first-time sends.
    """
    df = (df
          [(df['Style'] == 'lead') & (~df['Lead Style'].isin(['fell/hung', '']))]
          .drop_duplicates('Route')
          .sort_values('Date'))

    if route_type is not None:
        df = df[df['Route Type'].str.contains(route_type, flags=re.IGNORECASE)]

    return df


def mpl_hist(df: pd.DataFrame, route_type=None):
    """Returns a matplotlib figure of a histogram of route difficulties grouped by year.

    Parameters
    ----------
    df : DataFrame
        DataFrame of ticks

    Returns
    -------
    Figure
        Histogram of route difficulties grouped by year
    """
    df = get_first_sends(df, route_type)
    bins = list(range(df['Grade'].min(), df['Grade'].max()+2))

    _, ax = plt.subplots()
    for year in df['Date'].dt.year.unique()[::-1]:
        _ = (df[df['Date'].dt.year == year]
             .hist(column='Grade', bins=bins, ax=ax, label=year, alpha=0.75))

    ax.legend()

    return ax


def px_hist(df: pd.DataFrame, route_type=None):
    df = get_first_sends(df, route_type)
    df['Year'] = df['Date'].dt.year
    fig = (px.histogram(df,
                        x='Grade',
                        nbins=int(df['Grade'].max() - df['Grade'].min()),
                        facet_row='Year',
                        width=1000,
                        height=1000,
                        color='Year',
                        range_x=[df['Grade'].min(), df['Grade'].max()],
                        range_y=[0, df.groupby(['Year', 'Grade'])['Date'].count().max()])
           .update_yaxes(title_text='Sends')
           .for_each_annotation(lambda s: s.update(text=s.text.split('=')[-1])))

    return fig


def px_hist_3d(df: pd.DataFrame, route_type=None):
    df = get_first_sends(df, route_type)
    df['Year'] = df['Date'].dt.year

    hist_data = (df
                 .groupby(['Year', 'Grade'])['Route']
                 .count()
                 .sort_index(ascending=False)
                 .to_frame()
                 .reset_index()
                 .rename(columns={'Route': 'Count'}))

    return (go.Figure(data=[go.Surface(x=hist_data['Grade'],
                                       y=hist_data['Year'],
                                       z=hist_data['Count'])]))
