import streamlit as st
import pandas as pd
from importlib import reload
import plotly.express as px
import clean_tweets_dataframe as cld
import re

reload(cld)

st.set_page_config(page_title="Tweets Analysis Dashboard",
                   page_icon=":bar_chart:", layout="wide")

df_tweet = pd.read_csv('processed_tweet_data.csv', index_col=0)

# Data Preparation and Filtering
cleaner = cld.CleanTweets(df_tweet)
df_tweet = cleaner.drop_unwanted_column(df_tweet)
df_tweet = cleaner.drop_duplicate(df_tweet)
df_tweet = cleaner.convert_to_datetime(df_tweet)
df_tweet = cleaner.convert_to_numbers(df_tweet)
df_tweet = cleaner.treat_special_characters(df_tweet)
df_tweet = df_tweet[df_tweet.original_author != 'republikaonline']
df_tweet = df_tweet[df_tweet.original_author != 'dwnews']

# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")

lang = st.sidebar.multiselect(
    "Select the language:",
    options=df_tweet["lang"].unique(),
    default=['en', 'fr', 'kiny']
)

df_selection = df_tweet.query("lang ==@lang")

start_date = df_selection.created_at.head(1)
start_date = start_date.loc[start_date.index[0]].date()

end_date = df_selection.created_at.tail(1)
end_date = end_date.loc[end_date.index[0]].date()

st.markdown("##")
st.markdown("<h1 style='text-align: center; color: grey;'>Tweets Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: white;'> by Faith Bagire </h3>", unsafe_allow_html=True)

# ---- MAINPAGE ----
st.markdown("##")

# Sentiment Analysis Summary


# st.markdown("""---""")

text_grouped = df_selection.groupby('sentiment').count()['cleaned_text'].reset_index()

fig_senti = px.bar(text_grouped, x="sentiment", y="cleaned_text", orientation="v",
                   template="plotly_white", color='sentiment')
fig_senti.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=(dict(showgrid=False)))

# sentiment summary
df_tweet_date = df_selection.set_index('created_at')
df_tweet_date = df_tweet_date.resample('D').mean()[['polarity', 'subjectivity']].dropna()

# sentiment average per day
sent_over_time = px.line(df_tweet_date, x=df_tweet_date.index, y=['polarity', 'subjectivity'], width=500, height=500)

# Top 10 Hashtags by language (default: english)
hashtag_df = df_selection[['original_text', 'hashtags', 'retweet_hashtags']]


# @st.cache  # 👈 This function will be cached


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
hashtags_top = px.bar(hash_plotdf[len(hash_plotdf) - 10:len(hash_plotdf) + 1], x='count', y='hashtag', orientation='h',
                      text='count', width=800)
hashtags_top.update_traces(texttemplate='%{text:.s}')

left_column, middle_column, right_column = st.columns(3)

with left_column:
    st.markdown("<h4 style= 'text-align: center'> Average Polarity and Subjectivity Over Time </h4>",
                unsafe_allow_html=True)
    left_column.plotly_chart(sent_over_time, use_container_width=True)

with middle_column:
    st.markdown("<h4 style= 'text-align: center'> Top 10 Hashtags </h4>", unsafe_allow_html=True)
    middle_column.plotly_chart(hashtags_top, use_container_width=True)
with right_column:
    st.markdown("<h4 style= 'text-align: center'> Sentiment Category Distribution </h4>", unsafe_allow_html=True)
    right_column.plotly_chart(fig_senti, use_container_width=True)

st.markdown("---")
d_mostflwd = df_selection[['original_author', 'followers_count']].sort_values(by='followers_count',
                                                                              ascending=True).drop_duplicates(
    subset=['original_author'], keep='first')

d_mostflwd['username_link'] = d_mostflwd['original_author'].apply(
    lambda x: '[' + x + ']' + '(https://twitter.com/' + str(x) + ')')

left_column1, middle_column1, right_column1 = st.columns(3)
most_flwd_plt = px.bar(d_mostflwd[len(d_mostflwd) - 30:len(d_mostflwd) + 1], y='original_author', x='followers_count',
                       orientation='h')
with left_column1:
    st.markdown("<h4 style= 'text-align: center'> Most followed Accounts </h4>", unsafe_allow_html=True)

left_column1.plotly_chart(most_flwd_plt, use_container_width=True)
for i in range(len(d_mostflwd) - 1, len(d_mostflwd) - 10, -1):
    st.markdown(d_mostflwd['username_link'].iloc[i])

d_mostloc = pd.DataFrame(df_selection['place'].value_counts(ascending=True)).reset_index()
d_mostloc.rename(columns={"place": "count", "index": "place"}, inplace=True)
most_loc_plt = px.bar(d_mostloc[len(d_mostloc) - 30:len(d_mostloc) + 1], y='place', x='count', orientation='h')
with middle_column1:
    st.markdown("<h4 style= 'text-align: center'> Location by Most Tweets</h4>", unsafe_allow_html=True)
middle_column1.plotly_chart(most_loc_plt, use_container_width=True)

with right_column1:
    st.markdown("#### WordCloud:Most Frequent Words In Tweets")

right_column1.image('cw_rdf.png', use_column_width=True)

## Negative Tweeps
st.markdown("---")
df_neg = df_selection.query('sentiment=="Negative"')
df_neg = df_neg.groupby(by=['original_author']).aggregate(
    {'cleaned_text': 'count', 'likes_count': 'mean', 'followers_count': 'mean', 'friends_count': 'mean'})

df_neg.reset_index(inplace=True)

df_neg.rename(columns={'cleaned_text': 'negative_tweets'}, inplace=True)

left3, right3 = st.columns(2)
with left3:
    st.dataframe(df_neg)
st.markdown("---")

st.caption("Source Data")

st.dataframe(df_selection)

# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
