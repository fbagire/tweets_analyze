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
    df_to_clean = df_to_clean[df_to_clean.original_author != 'republikaonline']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'dwnews']
    df_to_clean = df_to_clean[df_to_clean.original_author != '123_INFO_DE']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'rogue_corq']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'Noticieros_MEX']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'RepDeFiFidonia']
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

stats_layout = html.Div(
    [

    ]
)


