import pandas as pd
from importlib import reload
import clean_tweets_dataframe as cld
import re
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from controls import LANGUAGES, SENTIMENT
import plotly.express as px
import copy

reload(cld)

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


# Load  Tweets and Clean them
def read_data(filename):
    df_func = pd.read_excel(filename, engine='openpyxl', index_col=0, dtype={'tweet_id': 'str'})
    return df_func


df_tweet_og = read_data(filename="processed_tweet_data.xlsx")
cleaner = cld.CleanTweets(df_tweet_og)


def clean_data(df_to_clean):
    # Data Preparation and Filtering
    df_to_clean = cleaner.drop_unwanted_column(df_to_clean)
    df_to_clean = cleaner.drop_duplicate(df_to_clean)
    df_to_clean = cleaner.convert_to_datetime(df_to_clean)
    df_to_clean = cleaner.convert_to_numbers(df_to_clean)
    df_to_clean = cleaner.treat_special_characters(df_to_clean)
    df_to_clean = df_to_clean[df_to_clean.original_author != 'republikaonline']
    df_to_clean = df_to_clean[df_to_clean.original_author != 'dwnews']

    return df_to_clean


df_tweet = clean_data(df_tweet_og)

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

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(
        l=30,
        r=30,
        b=20,
        t=40
    ),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation='h'),
    title='Satellite Overview',
    zoom=7,
)

app.layout = html.Div(
    [
        dcc.Store(id='aggregate_data'),
        html.Div(
            [
                html.H2('Twitter Analysis Dashboard', style={'textAlign': 'center', 'color': '#0F562F'}),
            ]
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P('Select Original Language'),
                        dcc.Dropdown(id='lang_sel',
                                     # options=[{'label': i, 'value': i} for i in lang_lst],
                                     options=lang_lst,
                                     value=list(LANGUAGES.keys()),
                                     multi=True,
                                     searchable=True,
                                     className="dcc_control")
                    ], style={'width': '50%', 'display': 'flex'}
                ),
                html.Div(
                    [
                        dcc.Graph(id='average_pola_graph',
                                  style={'width': '70vh', 'height': '45vh'}),
                        dcc.Graph(id='hashtags_plot', style={'width': '65vh', 'height': '45vh'}),
                        dcc.Graph(id='sent_bar', style={'width': '70vh', 'height': '45vh'})
                    ], style={'display': 'flex'})
            ], className='row'),
        html.Div(
            [
                dbc.Row(dbc.Col(html.Div(
                    [
                        "Select Sentiment",
                        dcc.RadioItems(id='sent_sel',
                                       options=sent_lst,
                                       value='Positive')
                    ]), width=6)),
                dbc.Row(
                    [
                        dbc.Col(html.Div([
                            dcc.Graph(id='mostflwd_plot')
                        ]), width="auto"),
                        dbc.Col(html.Div("One of three columns")),
                        dbc.Col(html.Div("One of three columns")),
                    ]
                ),
            ]
        )
    ], id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    }
)


# Helper Functions

def filter_dataframe(df, lang_sel):
    dff = df[df['lang'].isin(lang_sel)]
    return dff


@app.callback(Output('sent_bar', 'figure'),
              Input('lang_sel', 'value'))
def make_sentiment_bar(lang_sel):
    layout_sent = copy.deepcopy(layout)
    df_selection = filter_dataframe(df_tweet, lang_sel)
    text_grouped = df_selection.groupby('sentiment').count()['cleaned_text'].reset_index()

    fig_senti = px.bar(text_grouped, x="sentiment", y="cleaned_text", orientation="v",
                       title='Sentiment Category Distribution',
                       template="plotly_white", color='sentiment')
    fig_senti.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False)))
    return fig_senti


@app.callback(Output('hashtags_plot', 'figure'),
              Input('lang_sel', 'value'))
def make_hashtag_plot(lang_sel):
    df_selection = filter_dataframe(df_tweet, lang_sel)
    hashtag_df = df_selection[['original_text', 'hashtags', 'retweet_hashtags']]

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
                          text='count', width=800)
    hashtags_top.update_traces(texttemplate='%{text:.s}')

    return hashtags_top


@app.callback(Output('average_pola_graph', 'figure'),
              Input('lang_sel', 'value'))
def make_avepolarity_plot(lang_sel):
    # sentiment summary
    df_selection = filter_dataframe(df_tweet, lang_sel)
    df_tweet_date = df_selection.set_index('created_at')
    df_tweet_date = df_tweet_date.resample('D').mean()[['polarity', 'subjectivity']].dropna()

    # sentiment average per day
    sent_over_time = px.line(df_tweet_date, x=df_tweet_date.index, y=['polarity', 'subjectivity'],
                             title='Average Polarity and Subjectivity Over Time')

    return sent_over_time


@app.callback(Output('mostflwd_plot', 'figure'),
              [Input('lang_sel', 'value'),
               Input('sent_sel', 'value')])
def make_mostflwd_plots(lang_sel, sent_sel):
    df_selection = filter_dataframe(df_tweet, lang_sel)
    df_selection = df_selection.query('sentiment==`sent_sel`')
    d_mostflwd = df_selection[['original_author', 'followers_count']].sort_values(by='followers_count',
                                                                                  ascending=True).drop_duplicates(
        subset=['original_author'], keep='first')

    d_mostflwd['username_link'] = d_mostflwd['original_author'].apply(
        lambda x: '[' + x + ']' + '(https://twitter.com/' + str(x) + ')')

    most_flwd_plt = px.bar(d_mostflwd[len(d_mostflwd) - 30:len(d_mostflwd) + 1], y='original_author',
                           x='followers_count',
                           orientation='h')
    return most_flwd_plt


if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
