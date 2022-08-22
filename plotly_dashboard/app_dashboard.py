import dash_bootstrap_components as dbc
from dash import Dash, dcc, html
from dash.dependencies import Output, Input
from app import app
import pandas as pd
from flask_caching import Cache
# Connect to the layout and callbacks of each tab
from viz import viz_layout
from stats import stats_layout
from source_tab import source_layout

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})
TIMEOUT = 60


@cache.memoize()
def read_data(filename):
    # Load  Tweets and Clean them
    df_func = pd.read_excel(filename, engine='openpyxl', index_col=0, dtype={'tweet_id': 'str'})
    return df_func


df_selection = read_data(filename="week3_processed.xlsx")

# ----- Find the start and End date of the tweets under analysis ------
end_date = df_selection.created_at.head(1)
end_date = end_date.loc[end_date.index[0]].date()

start_date = df_selection.created_at.tail(2)
start_date = start_date.loc[start_date.index[0]].date()

app_tabs = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(label="Visualization", tab_id="tab-viz", labelClassName="text-success font-weight-bold",
                        activeLabelClassName="fw-bold text-danger"),
                dbc.Tab(label="Stats Summary", tab_id="tab-stats", labelClassName="text-success font-weight-bold",
                        activeLabelClassName="fw-bold text-danger"),
                dbc.Tab(label="Source Data", tab_id="tab-source", labelClassName="text-success font-weight-bold",
                        activeLabelClassName="fw-bold")
            ],
            id="tabs",
            active_tab="tab-stats",
            persistence=True,
            persistence_type='session'
        ),
    ], className="mt-3"
)

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.H3('Twitter Analysis Dashboard',
                            style={'textAlign': 'center', 'font_family': "Times new Roman", 'font_weight': 'bolder',
                                   'color': '#0F562F'}),
                    html.P('Tweets between {} // {}'.format(start_date, end_date)
                           )
                ]
            )
        ),

        dbc.Row(dbc.Col(app_tabs, width=12), className="mb-3"),
        html.Div(id='content', children=[])

    ]
)


@app.callback(

    Output("content", "children"),
    [Input("tabs", "active_tab")]
)
def switch_tab(tab_chosen):
    if tab_chosen == "tab-viz":
        return viz_layout
    elif tab_chosen == "tab-source":
        return source_layout
    elif tab_chosen == "tab-stats":
        return stats_layout
    return html.P("No Content for now...")


if __name__ == '__main__':
    app.run_server(debug=True)
