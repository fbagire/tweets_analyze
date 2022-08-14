from dash import html, dash_table, dcc, MATCH
import plotly.express as px
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_caching import Cache
import clean_tweets_dataframe as cld
from dash.dependencies import Input, Output, State
import pandas as pd
from controls import LANGUAGES, SENTIMENT
from app import app

pd.options.mode.chained_assignment = None

lang_lst = [{'label': str(LANGUAGES[lang_in]),
             'value': str(lang_in)}
            for lang_in in LANGUAGES]
sent_lst = [{'label': str(SENTIMENT[sent_in]),
             'value': str(sent_in)}
            for sent_in in SENTIMENT]

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})


@cache.memoize()
def read_data(filename):
    # Load  Tweets and Clean them
    df_func = pd.read_excel(filename, engine='openpyxl', index_col=0, dtype={'tweet_id': 'str'})
    return df_func


df_tweet_og = read_data(filename="processed_tweet_data.xlsx")
cleaner = cld.CleanTweets(df_tweet_og)


@cache.memoize()
def clean_data(df_to_clean):
    # Data Preparation and Filtering
    df_to_clean = cleaner.drop_unwanted_column(df_to_clean)
    df_to_clean = cleaner.drop_retweets(df_to_clean)
    df_to_clean = cleaner.convert_to_datetime(df_to_clean)
    df_to_clean = cleaner.convert_to_numbers(df_to_clean)
    df_to_clean = cleaner.treat_special_characters(df_to_clean)
    df_to_clean = df_to_clean[df_to_clean.original_author != 'dwnews']
    df_to_clean = df_to_clean[df_to_clean.original_author != '123_INFO_DE']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'rogue_corq']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'Noticieros_MEX']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'EUwatchers']

    return df_to_clean


df_tweet_full = clean_data(df_tweet_og)
df_tweet = df_tweet_full.query("tweet_category=='Tweet' or tweet_category== 'Reply'")

df_tweet['original_author'] = df_tweet['original_author'].apply(
    lambda x: '[' + x + ']' + '(https://twitter.com/' + str(x) + ')')

df_tweet['tweet_url'] = df_tweet['tweet_url'].apply(
    lambda x: '[' + x + ']' + '(' + str(x) + ')')

table_cols = [
    {'name': i, 'id': i, 'presentation': 'markdown'} if i in ['original_author', 'tweet_url'] else {
        'name': i, 'id': i}
    for i in
    df_tweet.columns]

cols_sort = df_tweet.select_dtypes('number').columns

for i, col in enumerate(table_cols):
    if list(table_cols[i].values())[0] in cols_sort:
        table_cols[i]['sortable'] = True
    else:
        table_cols[i]['sortable'] = False

non_sortable_column_ids = [col['id'] for col in table_cols if col.pop('sortable') is False]
table_css = [
                {
                    'selector': f'th[data-dash-column="{col}"] span.column-header--sort',
                    'rule': 'display: none',
                }
                for col in non_sortable_column_ids
            ] + [{'selector': '.dash-table-tooltip',
                  'rule': 'background-color: grey; font-family: monospace; color: white'}]
source_layout = html.Div(
    [
        dbc.Row([
            dash_table.DataTable(
                id='source-table',
                data=df_tweet.to_dict('records'),
                columns=table_cols,
                css=table_css,
                hidden_columns=['original_text', 'possibly_sensitive', 'retweet_hashtags', 'polarity', 'subjectivity',
                                'tweet_category', 'tweet_id'],
                sort_action="native",
                sort_mode='multi',
                # sort_by=[],

                style_cell={
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'minWidth': '100px', 'maxWidth': '350px', 'width': '100px',
                    'textAlign': 'left'
                },
                style_table={'overflowX': 'auto', 'height': '300px', 'overflowY': 'auto'},

                tooltip_data=[
                    {
                        column: {'value': str(value), 'type': 'markdown'}
                        for column, value in row.items()
                    } for row in df_tweet.to_dict('records')
                ],
                tooltip_duration=None,
                virtualization=True,
                fixed_rows={'headers': True},
                style_header={'backgroundColor': 'rgb(30,30,30)',
                              'color': 'white',
                              'font-size': '15px',
                              },
                style_data={'backgroundColor': 'rgb(50,50,50)',
                            'color': 'white',
                            'font-size': '13px',
                            'font-family': "Arial",
                            },
                style_data_conditional=[{
                    'if': {
                        'state': 'active'
                    },
                    'backgroundColor': 'rgba(0, 116, 217, 0.3)',

                }],
            )

        ]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Button("Download data", id="btn_csv"),
                                dcc.Download(id="download-dataframe-csv"),
                            ]
                        )
                    ], align='end', width=2),

                dbc.Col(
                    [
                        dcc.Dropdown(id='sent_sel',
                                     options=sent_lst,
                                     value=list(SENTIMENT.keys()),
                                     multi=True,
                                     style={'color': 'blue'})
                    ], width=4, align='start')
            ]
        )
    ])


@app.callback(Output('source-table', 'data'),
              Input('sent_sel', 'value'))
def filter_sentiment(sent_sel):
    if not sent_sel:
        raise PreventUpdate
    else:
        dff = df_tweet.copy()
        dff = dff[dff['sentiment'].isin(sent_sel)]
        return dff.to_dict('records')


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    return dcc.send_data_frame(df_tweet.to_csv, "tweets.csv")
