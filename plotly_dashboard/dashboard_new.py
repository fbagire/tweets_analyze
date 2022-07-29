import pandas as pd
from importlib import reload
import plotly.express as px
import clean_tweets_dataframe as cld
import re

reload(cld)

from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
from controls import LANGUAGES, SENTIMENT
import plotly.express as px
import pandas as pd

app = Dash(__name__)
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

# Top 10 Hashtags by language (default: english)
hashtag_df = df_tweet[['original_text', 'hashtags', 'retweet_hashtags']]


def find_hashtags(df_tweets):
    """This function will extract hashtags"""
    return re.findall('(#[A-Za-z]+[A-Za-z0-9-_]+)', df_tweets)


hashtag_df['hashtag_check'] = df_tweet.original_text.apply(find_hashtags)
hashtag_df.dropna(subset=['hashtag_check'], inplace=True)
tags_list = list(hashtag_df['hashtag_check'])
hashtags_list_df = pd.DataFrame([tag for tags_row in tags_list for tag in tags_row], columns=['hashtag'])
hashtags_list_df['hashtag'] = hashtags_list_df['hashtag'].str.lower()

hash_plotdf = pd.DataFrame(
    hashtags_list_df.value_counts(ascending=True), columns=['count']).reset_index()
hashtags_top = px.bar(hash_plotdf[len(hash_plotdf) - 10:len(hash_plotdf) + 1], x='count', y='hashtag', orientation='h',
                      text='count', width=800)
hashtags_top.update_traces(texttemplate='%{text:.s}')

# lang_lst = [df_tweet.lang.dropna().unique()]
lang_lst = [{'label': str(LANGUAGES[lang_in]),
             'value': str(lang_in)}
            for lang_in in LANGUAGES]
sent_lst = [{'label': str(SENTIMENT[sent_in]),
             'value': str(sent_in)}
            for sent_in in SENTIMENT]
# sent_lst = [df_tweet.sentiment.dropna().unique()]
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
                                     className="dcc_control"),
                        html.P('Select Sentiment'),
                        dcc.RadioItems(id='sent_sel',
                                       options=sent_lst,
                                       value='Positive'),
                    ], style={'width': '50%', 'display': 'flex'}
                ),
                html.Div(
                    [
                        dcc.Graph(id='hashtags_plot'),
                        dcc.Graph(id='sent_bar')
                    ], style={'width': '30%', 'display': 'flex'})
            ])
    ], id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    })


# Helper Functions

def filter_dataframe(df, lang_sel):
    dff = df[df['lang'].isin(lang_sel)]
    return dff


@app.callback(Output('sent_bar', 'figure'),
              Input('lang_sel', 'value'))
def make_sentiment_bar(lang_sel):
    dff = filter_dataframe(df_tweet, lang_sel)
    text_grouped = dff.groupby('sentiment').count()['cleaned_text'].reset_index()

    fig_senti = px.bar(text_grouped, x="sentiment", y="cleaned_text", orientation="v",
                       template="plotly_white", color='sentiment')
    fig_senti.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False)))
    return fig_senti


# def get_selectedf(lang_sel):
#     dff = filter_dataframe(df_tweet, lang_sel)
#     return dff


#


if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
