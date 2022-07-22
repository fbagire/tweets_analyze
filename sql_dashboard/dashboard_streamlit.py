import streamlit as st
import pandas as pd
import mysql.connector as mysql
import plotly.express as px
import seaborn as sns
from clean_tweets_dataframe import CleanTweets
import pandas.io.sql as sqlio
import re

st.set_page_config(page_title="Tweets Analysis Dashboard",
                   page_icon=":bar_chart:", layout="wide")
st.markdown("##")
st.markdown("<h1 style='text-align: center; color: grey;'>Tweets Analysis Dashboard</h1>", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: white;'> by Faith Bagire </h3>", unsafe_allow_html=True)

conn = mysql.connect(host='localhost', user='root', password='fefe@888', database='tweets', buffered=True)
cursor = conn.cursor()

query = '''SELECT * FROM tweetinformation'''
df_tweet = sqlio.read_sql_query(query, conn)

# Data Preparation and Filtering
cleaner = CleanTweets(df_tweet)
df_tweet = cleaner.drop_unwanted_column(df_tweet)
df_tweet = cleaner.drop_duplicate(df_tweet)
df_tweet = cleaner.convert_to_datetime(df_tweet)
df_tweet = cleaner.convert_to_numbers(df_tweet)

# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")

lang = st.sidebar.multiselect(
    "Select the language:",
    options=df_tweet["language"].unique(),
    default=['en', 'de', 'fr', 'es']
)

df_selection = df_tweet.query("language ==@lang")

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
sns.countplot(x='sentiment', data=df_tweet)

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
# @st.cache  # 👈 This function will be cached
def hashtag_pre(df=df_selection):
    hashtag_df = df[['cleaned_text', 'hashtags']]

    hashtag_df['hashtags'] = hashtag_df['hashtags'].astype('str')
    hashtag_df['hashtags'] = hashtag_df.hashtags.apply(lambda x: x.split(', '))

    tags_list = list(hashtag_df['hashtags'])
    hashtags_list_df = pd.DataFrame([tag for tags_row in tags_list for tag in tags_row], columns=['hashtag'])
    hashtags_list_df['hashtag'] = hashtags_list_df['hashtag'].str.lower()
    hashtags_list_df.drop(hashtags_list_df[hashtags_list_df['hashtag'] == '0'].index, inplace=True)
    return hashtags_list_df


hash_plotdf = pd.DataFrame(hashtag_pre().value_counts()[:10], columns=['count']).reset_index()
hashtags_top = px.bar(hash_plotdf, x='hashtag', y='count', width=500, height=500)

left_column, middle_column, right_column = st.columns(3)
left_column.plotly_chart(sent_over_time, use_container_width=True)
middle_column.plotly_chart(hashtags_top, use_container_width=True)
right_column.plotly_chart(fig_product_sales, use_container_width=True)

st.markdown("---")

left_column1, right_column1 = st.columns(2)
# You can use a column just like st.sidebar:
left_column1.button('Press me!')

# Or even better, call Streamlit functions inside a "with" block:
with right_column1:
    chosen = st.radio(
        'Sorting hat',
        ("Gryffindor", "Ravenclaw", "Hufflepuff", "Slytherin"))
    st.write(f"You are in {chosen} house!")

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
