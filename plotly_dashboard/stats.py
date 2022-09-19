from dash import html, dash_table, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask_caching import Cache
import clean_tweets_dataframe as cld
from dash.dependencies import Input, Output
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


df_tweet_og = read_data(filename="week3_processed.xlsx")
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
    df_to_clean = df_to_clean[df_to_clean.original_author != 'IndianExpress']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'British_Airways']


    return df_to_clean


df_tweet_full = clean_data(df_tweet_og)
df_tweet = df_tweet_full.query("tweet_category=='Tweet' or tweet_category== 'Reply'")

df_tweet['original_author'] = df_tweet['original_author'].apply(
    lambda x: '[' + x + ']' + '(https://twitter.com/' + str(x) + ')')

cols_use = ['original_author', 'cleaned_text', 'likes_count', 'followers_count', 'retweet_count']

columns = [{'name': 'original_author', 'id': 'original_author', 'presentation': 'markdown'},
           {'name': 'cleaned_text', 'id': 'cleaned_text', 'type': 'numeric'},
           {'name': 'polarity', 'id': 'polarity'},

           {'name': 'likes_count', 'id': 'likes_count'},
           {'name': 'followers_count', 'id': 'followers_count'},
           {'name': 'retweet_count', 'id': 'retweet_count'}]

table_css = [
    {
        'selector': f'th[data-dash-column="original_author"] span.column-header--sort',
        'rule': 'display: none',
    }
]
table_layout = dict(style_header={'backgroundColor': 'rgb(30,30,30)', 'color': 'white', 'font-size': '15px'},
                    style_data={'backgroundColor': 'rgb(50,50,50)', 'color': 'white', 'font-size': '13px',
                                'font-family': "Arial"},
                    style_cell={'overflow': 'hidden', 'textOverflow': 'ellipsis', 'minWidth': '100px',
                                'maxWidth': '350px', 'width': '100px', 'textAlign': 'left'}),

stats_layout = html.Div(
    [

        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Dropdown(id='sent_sel',
                                     options=sent_lst,
                                     value=list(SENTIMENT.keys()),
                                     multi=True,
                                     placeholder='sentiment',
                                     style={'color': 'blue'}
                                     )
                    ], md=4
                ),
                dbc.Col(html.H5("Words Cloud From Tweets",
                                style={'textAlign': 'center', 'font_family': "Times new Roman",
                                       'font_weight': 'bolder'})),
                dbc.Col()
            ]),
        dbc.Row(
            [
                dbc.Col(
                    dash_table.DataTable(id='tweets_per_user',
                                         data=df_tweet.to_dict('records'),
                                         columns=columns,
                                         css=table_css,
                                         style_data=table_layout[0]['style_data'],
                                         style_header=table_layout[0]['style_header'],
                                         style_cell=table_layout[0]['style_cell'],
                                         style_table={'overflowX': 'auto', 'height': '300px',
                                                      'overflowY': 'auto'},
                                         sort_action='native',
                                         sort_mode='multi'

                                         ),
                    md=4),
                dbc.Col(
                    html.Div(
                        html.Img(src=app.get_asset_url('cw_rdf_week3.png'), width="500", height="400")
                    ), md=4),
            ]),
        # dbc.Row(
        #     [
        #         dbc.Col(html.Div("One of four columns"), width=6, lg=3),
        #         dbc.Col(html.Div("One of four columns"), width=6, lg=3),
        #         dbc.Col(html.Div("One of four columns"), width=6, lg=3),
        #         dbc.Col(html.Div("One of four columns"), width=6, lg=3),
        #     ]
        # ),

    ]
)


@app.callback(Output('tweets_per_user', 'data'),

              Input('sent_sel', 'value'))
def filter_sentiment(sent_sel):
    if not sent_sel:
        raise PreventUpdate
    else:
        df_new = df_tweet.copy()
        df_new = df_new[df_new['sentiment'].isin(sent_sel)]

        dff = df_new.groupby(by=['original_author'], as_index=False).aggregate(
            {'cleaned_text': 'count', 'polarity': 'mean', 'likes_count': 'mean', 'followers_count': 'mean',
             'retweet_count': 'mean'})

        return dff.to_dict('records')
