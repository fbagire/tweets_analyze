import pandas as pd
import clean_tweets_dataframe as cld
import re
from dash import dcc, dash_table, html
from flask_caching import Cache
from dash.dependencies import Input, Output
from controls import LANGUAGES, SENTIMENT
import plotly.express as px
import copy
from dash.exceptions import PreventUpdate
from dash import Dash
import dash_bootstrap_components as dbc
from wordcloud import WordCloud, STOPWORDS
from cleantext import clean
import matplotlib.pyplot as plt

pd.options.mode.chained_assignment = None

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.DARKLY],
           title='Twitter Analysis',
           meta_tags=[{'name': 'viewport',
                       'content': 'width=device-width, initial-scale=1.0'}]
           )

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


df_tweet_og = read_data("./week7_final.xlsx")

# ----- Find the start and End date of the tweets under analysis ------
end_date = df_tweet_og.created_at.head(1)
end_date = end_date.loc[end_date.index[0]].date()
start_date = df_tweet_og.created_at.tail(2)
start_date = start_date.loc[start_date.index[0]].date()

cleaner = cld.CleanTweets(df_tweet_og)

wrong_auth = ['dwnews', '123_INFO_DE', 'rogue_corq', 'Noticieros_MEX', 'EUwatchers', 'IndianExpress', 'IndianExpress',
              'British_Airways']


@cache.memoize()
def clean_data(df_to_clean):
    # Data Preparation and Filtering
    df_to_clean = cleaner.drop_unwanted_column(df_to_clean)
    df_to_clean = cleaner.drop_retweets(df_to_clean)
    df_to_clean = cleaner.convert_to_datetime(df_to_clean)
    df_to_clean = cleaner.convert_to_numbers(df_to_clean)
    df_to_clean = cleaner.treat_special_characters(df_to_clean)
    df_to_clean = df_to_clean[~df_to_clean['original_author'].isin(wrong_auth)]
    return df_to_clean


df_tweet_full = clean_data(df_tweet_og)
df_tweet = df_tweet_full.query("tweet_category=='Tweet' or tweet_category== 'Reply'")
df_tweet['original_author1'] = df_tweet['original_author']
df_tweet['original_author'] = df_tweet['original_author'].apply(
    lambda x: '[' + x + ']' + '(https://twitter.com/' + str(x) + ')')

df_tweet['tweet_url'] = df_tweet['tweet_url'].apply(
    lambda x: '[' + x + ']' + '(' + str(x) + ')')

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

# text Preprocessing
df_tweet['cleaned_text'] = df_tweet['cleaned_text'].apply(lambda x: clean(x,
                                                                          no_emoji=True, lower=True,
                                                                          no_punct=True,
                                                                          no_line_breaks=True,
                                                                          strip_lines=True,
                                                                          no_currency_symbols=True))

all_words = ' '.join(df_tweet.cleaned_text.values)

wordcloud_obj = WordCloud(width=1000, height=600, stopwords=STOPWORDS).generate(all_words)
plt.figure(figsize=(10, 5))
plt.axis('off')
fgg = plt.imshow(wordcloud_obj)
fgg.figure.savefig('cw_rdf.png', bbox_inches='tight', pad_inches=0)

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
            active_tab="tab-viz",
            persistence=True,
            persistence_type='session'
        ),
    ], className="mt-3"
)

app.layout = dbc.Container(
    [
        dbc.Row([
            dbc.Col(
                [
                    html.H3('Twitter Analysis Dashboard',
                            style={'textAlign': 'center', 'font_family': "Times new Roman", 'font_weight': 900,
                                   'color': '#0F562F'})
                ]
            ),
            dbc.Col(
                [
                    html.A('Contact Author', href='https://www.linkedin.com/in/fbagire/'),
                    html.Br(),
                    html.A('Tweets between {} :: {}'.format(start_date, end_date))
                ]
            )
        ]),

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
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            ['Select Original Language'],
                            width=2, style={'color': '#0F562F', 'font-weight': 'bold', 'textAlign': 'right'}
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
                    ], align='start'),
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
    elif tab_chosen == "tab-source":
        return html.Div(
            [
                dbc.Row([
                    dash_table.DataTable(
                        id='source-table',
                        data=df_tweet.to_dict('records'),
                        columns=table_cols,
                        css=table_css,
                        hidden_columns=['original_text', 'possibly_sensitive', 'retweet_hashtags', 'polarity',
                                        'subjectivity',
                                        'tweet_category', 'tweet_id'],
                        sort_action="native",
                        sort_mode='multi',
                        # sort_by=[],
                        filter_action="native",
                        filter_options={'case': 'insensitive'},

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
    elif tab_chosen == "tab-stats":
        return html.Div(
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
                                html.Img(src=app.get_asset_url('assets/cw_rdf.png'), width="500", height="400")
                            ), md=4),
                    ]),
            ]
        )
    return html.P("No Content for now...")


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
    fig_senti.update_layout(layout_sent)
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

    hash_plotdf = pd.DataFrame(hashtags_list_df.value_counts(ascending=True), columns=['count']).reset_index()
    hashtags_top = px.bar(hash_plotdf.tail(10),
                          x='count',
                          y='hashtag',
                          orientation='h',
                          title='Top 10 Hashtags',
                          text='count')
    hashtags_top.update_traces(texttemplate='%{text:.s}')
    hashtags_top.update_layout(layout)

    return hashtags_top


@app.callback(Output('average_pola_graph', 'figure'),
              Input('lang_sel', 'value'))
def make_avepolarity_plot(lang_sel):
    df_selection = filter_dataframe(df_tweet, lang_sel)
    df_tweet_date = df_selection.query("sentiment != 'Neutral'").set_index('created_at')
    df_tweet_date = df_tweet_date.resample('D').mean()[['polarity', 'subjectivity']].dropna()

    # sentiment average per day
    sent_over_time = px.line(df_tweet_date, x=df_tweet_date.index, y=['polarity', 'subjectivity'],
                             labels={'value': 'Sentiment', 'created_at': 'Date'},
                             title='Average Polarity and Subjectivity Over Time')
    sent_over_time.update_layout(layout)
    return sent_over_time


@app.callback(Output('mostflwd_plot', 'figure'),
              Input('store-data', 'data'))
def make_mostflwd_plots(df_selection):
    df_selection = pd.DataFrame(df_selection)
    d_mostflwd = df_selection[['original_author1', 'followers_count']].sort_values(by='followers_count',
                                                                                   ascending=True).drop_duplicates(
        subset=['original_author1'], keep='first')
    most_flwd_plt = px.bar(d_mostflwd.tail(20), y='original_author1',
                           x='followers_count', title='Most followed Accounts', orientation='h',
                           labels={'original_author1': 'Author', 'followers_count': 'Number of Followers'})
    most_flwd_plt.update_layout(layout)
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
        fig_type = px.pie(df_type, values='count', names='tweet_type', hole=0.3, title='Type of Tweet')
        fig_type.update_layout(layout)
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

    mentions_plt = px.bar(mention_df.tail(20), y='mentioned_user',
                          x='count', title='Most mentioned Accounts', orientation='h',
                          labels={'mentioned_user': 'User mentioned', 'count': 'Number of Mentions'})
    mentions_plt.update_layout(layout)
    mentions_plt.update_yaxes(type='category')

    return mentions_plt


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
def func():
    return dcc.send_data_frame(df_tweet.to_csv, "tweets.csv")


@app.callback(Output('tweets_per_user', 'data'),
              Input('sent_sel', 'value'))
def filter_sentimentb(sent_sel):
    if not sent_sel:
        raise PreventUpdate
    else:
        df_new = df_tweet.copy()
        df_new = df_new[df_new['sentiment'].isin(sent_sel)]

        dff = df_new.groupby(by=['original_author'], as_index=False).aggregate(
            {'cleaned_text': 'count', 'polarity': 'mean', 'likes_count': 'mean', 'followers_count': 'mean',
             'retweet_count': 'mean'})

        return dff.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True)
