import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

RE_YDS = re.compile(r'5\.(\d{1,2})\s*([abcd\+])?\s*R?', flags=re.IGNORECASE)
RE_VERMIN = re.compile(r'V(.+)\s*R?', flags=re.IGNORECASE)


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
            pass

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
