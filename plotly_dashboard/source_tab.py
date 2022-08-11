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
    df_to_clean = df_to_clean[df_to_clean.original_author != 'republikaonline']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'dwnews']
    df_to_clean = df_to_clean[df_to_clean.original_author != '123_INFO_DE']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'rogue_corq']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'Noticieros_MEX']

    return df_to_clean


df_tweet_full = clean_data(df_tweet_og)
df_tweet = df_tweet_full.query("tweet_category=='Tweet' or tweet_category== 'Reply'")

source_layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    ['Tweets as a Table'
                     ], width=2, style={'color': '#0F562F', 'font-weight': 'bold', 'textAlign': 'right'}
                )]),
        dbc.Row([
            dash_table.DataTable(
                id='source-table',
                data=df_tweet.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df_tweet.columns],
                filter_action="native",
                hidden_columns=['original_text', 'possibly_sensitive', 'retweet_hashtags', 'polarity', 'subjectivity',
                                'tweet_category', 'tweet_id'],
                style_cell={'color': '#2B2A30', 'textAlign': 'left'},
                style_table={'color': '#2B2A30'},
                page_size=30,

            )

        ])
    ]
)

# @app.callback(Output('memory-table', 'data'),
#               Input('store-data', 'data'))
# def get_df(data):
#     if data is None:
#         raise PreventUpdate
#
#     return pd.DataFrame(data)

# dbc.Row(dbc.Col(html.Div(
#     [
#         "Select Sentiment",
#         dcc.RadioItems(id='sent_sel',
#                        options=sent_lst,
#                        value='Positive')
#     ]), width=6))
