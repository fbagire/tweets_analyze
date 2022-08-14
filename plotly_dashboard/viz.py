import pandas as pd
from importlib import reload
import clean_tweets_dataframe as cld
import re
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from controls import LANGUAGES, SENTIMENT
import plotly.express as px
import copy
from flask_caching import Cache
from dash.exceptions import PreventUpdate

from app import app

reload(cld)

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

# sentiment summary
df_tweet_date = df_tweet.set_index('created_at')
df_tweet_date = df_tweet_date.resample('D').mean()[['polarity', 'subjectivity']].dropna()

# sentiment average per day
sent_over_time = px.line(df_tweet_date, x=df_tweet_date.index, y=['polarity', 'subjectivity'])

lang_lst = [{'label': str(LANGUAGES[lang_in]),
             'value': str(lang_in)}
            for lang_in in LANGUAGES]
sent_lst = [{'label': str(SENTIMENT[sent_in]),
             'value': str(sent_in)}
            for sent_in in SENTIMENT]

layout = dict(title={"yref": "paper", "font": {'size': 12}, "y": 1, "xref": "paper", "x": 0.5, "pad": {'b': 20},
                     "yanchor": "bottom"},
              font={'size': 11},
              margin=dict(l=30, r=30, b=20, t=40),
              # autosize=True,
              hovermode="closest",
              plot_bgcolor="#2B2A30",
              font_color='white',
              paper_bgcolor="#2B2A30",
              legend=dict(font=dict(size=10)))

viz_layout = html.Div(
    [

        dbc.Row([
            dbc.Col(
                ['Select Original Language'

                 ], width=2, style={'color': '#0F562F', 'font-weight': 'bold', 'textAlign': 'right'}
            ),
            dbc.Col(
                [
                    dcc.Dropdown(id='lang_sel',
                                 options=lang_lst,
                                 value=list(LANGUAGES.keys()),
                                 multi=True,
                                 style={'color': 'blue'}
                                 )
                ], width=3)
        ], align='start'
        ),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='average_pola_graph',
                          style={'height': '36vh'})

            ], width=4),
            dbc.Col([
                dcc.Graph(id='hashtags_plot', animate=None, style={'height': '36vh'}),

            ], width=4),
            dbc.Col([
                dcc.Graph(id='sent_bar', style={'height': '36vh'})

            ], width=3, lg=3)

        ]),

        html.Div(
            [
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    dcc.Graph(id='mostflwd_plot',
                                              style={'height': '36vh'}),
                                ]
                            ), width=4),
                        dbc.Col(
                            html.Div(
                                [
                                    dcc.Graph(id='tweet_typepie',
                                              style={'height': '30vh'})

                                ]
                            ), width=3),
                        dbc.Col(
                            [
                                dcc.Graph(id='tweet_mentions',
                                          style={'height': '40vh'})
                            ]

                        ),
                    ]
                ),

                dcc.Store(id='store-data', data=[], storage_type='memory')
            ], id="mainContainer"
        )
    ])


# Helper Functions


def make_countdf(df, col_name, new_colname):
    df_count = pd.DataFrame(df[col_name].value_counts(ascending=True)).reset_index()
    df_count.rename(columns={'index': new_colname, col_name: 'count'}, inplace=True)
    return df_count


def filter_dataframe(df, lang_sel):
    dff = df[df['lang'].isin(lang_sel)]
    return dff


@app.callback(Output('store-data', 'data'),
              Input('lang_sel', 'value'))
def df_language(lang_sel):
    if not lang_sel:
        raise PreventUpdate
    else:
        df_selection = filter_dataframe(df_tweet, lang_sel)
        return df_selection.to_dict('records')


@app.callback(Output('sent_bar', 'figure'),
              Input('store-data', 'data'))
def make_sentiment_bar(df_selection):
    df_selection = pd.DataFrame(df_selection)
    text_grouped = df_selection.groupby('sentiment').count()['cleaned_text'].reset_index()

    fig_senti = px.bar(text_grouped, x="sentiment", y="cleaned_text", text='cleaned_text', orientation="v",
                       title='Sentiment Category Distribution',
                       template="plotly_white", color='sentiment')
    layout_sent = copy.deepcopy(layout)
    layout_sent['yaxis_title'] = "Number of Tweets"
    fig_senti.layout.update(layout_sent)
    return fig_senti


@app.callback(Output('hashtags_plot', 'figure'),
              Input('store-data', 'data'))
def make_hashtag_plot(df_selection):
    df_selection = pd.DataFrame(df_selection)

    hashtag_dfo = df_selection[['original_text', 'hashtags', 'retweet_hashtags']]
    hashtag_df = hashtag_dfo.copy()

    def find_hashtags(df_tweets):
        """This function will extract hashtags"""
        return re.findall('(#[A-Za-z]+[A-Za-z0-9-_]+)', df_tweets)

    hashtag_df['hashtag_check'] = df_selection.original_text.apply(find_hashtags)
    hashtag_df.dropna(subset=['hashtag_check'], inplace=True)
    tags_list = list(hashtag_df['hashtag_check'])
    hashtags_list_df = pd.DataFrame([tag for tags_row in tags_list for tag in tags_row], columns=['hashtag'])
    hashtags_list_df['hashtag'] = hashtags_list_df['hashtag'].str.lower()

    hash_plotdf = pd.DataFrame(
        hashtags_list_df.value_counts(ascending=True), columns=['count']).reset_index()
    hashtags_top = px.bar(hash_plotdf[len(hash_plotdf) - 10:len(hash_plotdf) + 1], x='count', y='hashtag',
                          orientation='h', title='Top 10 Hashtags',
                          text='count')
    hashtags_top.update_traces(texttemplate='%{text:.s}')
    hashtags_top.layout.update(layout)

    return hashtags_top


@app.callback(Output('average_pola_graph', 'figure'),
              Input('lang_sel', 'value'))
def make_avepolarity_plot(lang_sel):
    df_selection = filter_dataframe(df_tweet, lang_sel)
    df_tweet_date = df_selection.query("sentiment != 'Neutral'").set_index('created_at')
    df_tweet_date = df_tweet_date.resample('D').mean()[['polarity', 'subjectivity']].dropna()

    # sentiment average per day
    sent_over_time = px.line(df_tweet_date, x=df_tweet_date.index, y=['polarity', 'subjectivity'],
                             title='Average Polarity and Subjectivity Over Time')
    sent_over_time.layout.update(layout)
    return sent_over_time


@app.callback(Output('mostflwd_plot', 'figure'),
              Input('store-data', 'data'))
def make_mostflwd_plots(df_selection):
    df_selection = pd.DataFrame(df_selection)
    #     # df_selection = df_selection.query('sentiment==@sent_sel')
    d_mostflwd = df_selection[['original_author', 'followers_count']].sort_values(by='followers_count',
                                                                                  ascending=True).drop_duplicates(
        subset=['original_author'], keep='first')

    d_mostflwd['username_link'] = d_mostflwd['original_author'].apply(
        lambda x: '[' + x + ']' + '(https://twitter.com/' + str(x) + ')')

    most_flwd_plt = px.bar(d_mostflwd[len(d_mostflwd) - 20:len(d_mostflwd) + 1], y='original_author',
                           x='followers_count', title='Most followed Accounts', orientation='h')
    most_flwd_plt.layout.update(layout)
    return most_flwd_plt


@app.callback(Output('tweet_typepie', 'figure'),
              Input('lang_sel', 'value'))
def make_type_pie(lang_sel):
    if not lang_sel:
        raise PreventUpdate
    else:
        df_selection = filter_dataframe(df_tweet_full, lang_sel)
        # Type of tweet
        df_type = make_countdf(df_selection, 'tweet_category', 'tweet_type')
        # df_type = pd.DataFrame(df_selection['tweet_category'].value_counts()).reset_index()
        # df_type.rename(columns={'index': 'tweet_type', 'tweet_category': 'count'}, inplace=True)
        fig_type = px.pie(df_type, values='count', names='tweet_type', hole=0.3, title='Type of Tweet')
        fig_type.layout.update(layout)
        return fig_type


@app.callback(Output('tweet_mentions', 'figure'),
              Input('store-data', 'data'))
def mentions_count(df_selection):
    df_selection = pd.DataFrame(df_selection)
    mentions = list(df_selection['user_mentions'].dropna())

    mentions_ls = []
    for i in range(len(mentions)):
        mentions_ls.append(mentions[i].split(','))
    mention_df = pd.DataFrame([ment for ment_row in mentions_ls for ment in ment_row], columns=['mentions'])
    mention_df = make_countdf(mention_df, 'mentions', 'mentioned_user')

    mentions_plt = px.bar(mention_df[len(mention_df) - 20:len(mention_df) + 1], y='mentioned_user',
                          x='count', title='Most mentioned Accounts', orientation='h')
    mentions_plt.layout.update(layout)
    mentions_plt.update_yaxes(type='category')

    return mentions_plt
