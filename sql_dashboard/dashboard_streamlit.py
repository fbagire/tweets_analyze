import streamlit as st
import pandas as pd
from importlib import reload
import plotly.express as px
from translate import Translator
import seaborn as sns
import clean_tweets_dataframe as cld
import re

reload(cld)
st.set_page_config(page_title="Tweets Analysis Dashboard",
                   page_icon=":bar_chart:", layout="wide")
st.markdown("##")
st.markdown("<h1 style='text-align: center; color: grey;'>Tweets Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: white;'> by Faith Bagire </h3>", unsafe_allow_html=True)

df_tweet = pd.read_csv('processed_tweet_data.csv')
# Data Preparation and Filtering
cleaner = cld.CleanTweets(df_tweet)
df_tweet = cleaner.drop_unwanted_column(df_tweet)
df_tweet = cleaner.drop_duplicate(df_tweet)
df_tweet = cleaner.convert_to_datetime(df_tweet)
df_tweet = cleaner.convert_to_numbers(df_tweet)


# df_tweet = cleaner.remove_non_english_tweets(df_tweet)
# df_tweet = cleaner.treat_special_characters(df_tweet)


def remove_non_english_tweets(df):
    """
    remove non english tweets from lang
    """

    df.query("lang == 'en' | lang =='fr' ", inplace=True)

    return df


df_tweet = remove_non_english_tweets(df_tweet)


def treat_special_characters(df):
    """"
    Remove special characters and redundant characters which cause one location to come out many times
    """
    df['place'] = df['place'].str.capitalize()
    df['place'] = df['place'].replace(r'^.*xico.*', value='Mexico', regex=True)
    df['place'] = df['place'].replace(r'(^.*igali.*)|(^.*wanda.*)', value='Rwanda', regex=True)

    return df


df_tweet = treat_special_characters(df_tweet)

translator = Translator(from_lang="french", to_lang="english")

# def translate_french_tweets(df):


# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")

lang = st.sidebar.multiselect(
    "Select the language:",
    options=df_tweet["lang"].unique(),
    default=['en']
)

df_selection = df_tweet.query("lang ==@lang")

# ---- MAINPAGE ----
st.markdown("##")

# Sentiment Analysis Summary

left_column, middle_column, right_column = st.columns(3)
with left_column:
    st.subheader("Average Polarity and Subjectivity Over time:")
with middle_column:
    st.subheader("Top 10 Hashtags by language (default: english)")
with right_column:
    st.subheader("Sentiment class distribution:")
st.markdown("""---""")

text_grouped = df_tweet.groupby('sentiment').count()['cleaned_text'].reset_index()
# sns.countplot(x='sentiment', data=df_tweet)

fig_product_sales = px.bar(text_grouped, x="sentiment", y="cleaned_text", orientation="v",
                           template="plotly_white", width=500, height=500
                           )
fig_product_sales.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=(dict(showgrid=False)))

# sentiment summary
df_tweet_date = df_tweet.set_index('created_at')
df_tweet_date = df_tweet_date.resample('D').mean()[['polarity', 'subjectivity']].dropna()

# sentiment average per day
sent_over_time = px.line(df_tweet_date, x=df_tweet_date.index, y=['polarity', 'subjectivity'], width=500, height=500)

# Top 10 Hashtags by language (default: english)
hashtag_df = df_tweet[['original_text', 'hashtags', 'retweet_hashtags']]


@st.cache  # 👈 This function will be cached
def find_hashtags(df_tweet):
    '''This function will extract hashtags'''
    return re.findall('(#[A-Za-z]+[A-Za-z0-9-_]+)', df_tweet)


hashtag_df['hashtag_check'] = df_tweet.original_text.apply(find_hashtags)
hashtag_df.dropna(subset=['hashtag_check'], inplace=True)
tags_list = list(hashtag_df['hashtag_check'])
hashtags_list_df = pd.DataFrame([tag for tags_row in tags_list for tag in tags_row], columns=['hashtag'])
hashtags_list_df['hashtag'] = hashtags_list_df['hashtag'].str.lower()

hash_plotdf = pd.DataFrame(
    hashtags_list_df.value_counts(ascending=True), columns=['count']).reset_index()
hashtags_top = px.bar(hash_plotdf[len(hash_plotdf) - 10:len(hash_plotdf) + 1], x='count', y='hashtag', orientation='h',
                      text='count', width=800)
hashtags_top.update_traces(texttemplate='%{text:.2s}')

left_column, middle_column, right_column = st.columns(3)
left_column.plotly_chart(sent_over_time, use_container_width=True)
middle_column.plotly_chart(hashtags_top, use_container_width=True)
right_column.plotly_chart(fig_product_sales, use_container_width=True)

st.markdown("---")
d_mostflwd = df_tweet[['original_author', 'followers_count']].sort_values(by='followers_count',
                                                                          ascending=True).drop_duplicates(
    subset=['original_author'], keep='first')

left_column1, right_column1 = st.columns(2)
most_flwd_plt = px.bar(d_mostflwd[len(d_mostflwd) - 30:len(d_mostflwd) + 1], y='original_author', x='followers_count',
                       orientation='h')
# most_flwd_plt.update_traces(texttemplate='%{text:.2s}', textfont_size=20)
with left_column1:
    st.subheader("Most followed Accounts")
left_column1.plotly_chart(most_flwd_plt)

d_mostloc = df_tweet['place'].value_counts(ascending=False)
most_loc_plt = px.bar()
with right_column1:
    st.subheader("Location by Most Tweets")
    right_column1.plotly_chart(most_loc_plt)

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
