import streamlit as st
import pandas as pd
from importlib import reload
import plotly.express as px
import clean_tweets_dataframe as cld
import re
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

reload(cld)

st.set_page_config(page_title="Tweets Analysis Dashboard",
                   page_icon=":bar_chart:", layout="wide")


# Cached function to Read and Clean the Data
@st.cache
def read_data(filename):
    df_func = pd.read_excel(filename, engine='openpyxl', index_col=0, dtype={'tweet_id': 'str'})
    return df_func


df_tweet_og = read_data(filename="processed_tweet_data.xlsx")
cleaner = cld.CleanTweets(df_tweet_og)


@st.cache
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
# df_tweet.drop(['', 'retweet_hashtags'], axis=1, inplace=True)

# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")

lang = st.sidebar.multiselect(
    "Select the language:",
    options=df_tweet["lang"].unique(),
    default=['en', 'fr', 'kiny']
)

df_selection = df_tweet.query("lang ==@lang")

# ----- Find the start and End date of the tweets under analysis ------
start_date = df_selection.created_at.head(1)
start_date = start_date.loc[start_date.index[0]].date()

end_date = df_selection.created_at.tail(1)
end_date = end_date.loc[end_date.index[0]].date()
st.markdown("<h1 style='text-align: center; color: grey'><font size='6'>Tweets Analysis Dashboard</font></h1>",
            unsafe_allow_html=True)

# ---- MAINPAGE ----
# st.markdown("##")
# Sentiment Analysis Summary

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

# --- Make First Three Columns to print figures
left_column, middle_column, right_column = st.columns(3)

with left_column:
    st.markdown(
        "<h4 style= 'text-align: center'><font size='3'> Average Polarity and Subjectivity Over Time </font></h4>",
        unsafe_allow_html=True)
    left_column.plotly_chart(sent_over_time, use_container_width=True)

with middle_column:
    st.markdown("<h4 style= 'text-align: center'><font size='3'> Top 10 Hashtags </font> </h4>", unsafe_allow_html=True)
    middle_column.plotly_chart(hashtags_top, use_container_width=True)
with right_column:
    st.markdown("<h4 style= 'text-align: center'><font size='3'> Sentiment Category Distribution</font> </h4>",
                unsafe_allow_html=True)
    right_column.plotly_chart(fig_senti, use_container_width=True)

# st.markdown("---")
d_mostflwd = df_selection[['original_author', 'followers_count']].sort_values(by='followers_count',
                                                                              ascending=True).drop_duplicates(
    subset=['original_author'], keep='first')

d_mostflwd['username_link'] = d_mostflwd['original_author'].apply(
    lambda x: '[' + x + ']' + '(https://twitter.com/' + str(x) + ')')

left_column1, middle_column1, right_column1 = st.columns(3)
most_flwd_plt = px.bar(d_mostflwd[len(d_mostflwd) - 30:len(d_mostflwd) + 1], y='original_author', x='followers_count',
                       orientation='h')
with left_column1:
    st.markdown("<h4 style= 'text-align: center'><font size='3'> Most followed Accounts </font></h4>",
                unsafe_allow_html=True)

left_column1.plotly_chart(most_flwd_plt, use_container_width=True)
for i in range(len(d_mostflwd) - 1, len(d_mostflwd) - 10, -1):
    st.markdown(d_mostflwd['username_link'].iloc[i])

d_mostloc = pd.DataFrame(df_selection['place'].value_counts(ascending=True)).reset_index()
d_mostloc.rename(columns={"place": "count", "index": "place"}, inplace=True)
most_loc_plt = px.bar(d_mostloc[len(d_mostloc) - 30:len(d_mostloc) + 1], y='place', x='count', orientation='h')
with middle_column1:
    st.markdown("<h4 style= 'text-align: center'><font size='3'> Location by Most Tweets</font></h4>",
                unsafe_allow_html=True)
middle_column1.plotly_chart(most_loc_plt, use_container_width=True)

with right_column1:
    st.markdown("<h4 style= 'text-align: center'><font size='3'> WordCloud:Most Frequent Words In Tweets</font></h4>",
                unsafe_allow_html=True)
right_column1.image('cw_rdf.png', use_column_width=True)

# ---Make a selection box fro either (Positive, Negative, Neutral)
sent_choice = st.selectbox("Select Sentiment to See",
                           ("Positive", "Negative", "Neutral"))

df_neg = df_selection.query('sentiment==@sent_choice')
df_neg = df_neg.groupby(by=['original_author']).aggregate(
    {'cleaned_text': 'count', 'likes_count': 'mean', 'followers_count': 'mean', 'friends_count': 'mean'})
df_neg.reset_index(inplace=True)
df_neg.rename(columns={'cleaned_text': str(sent_choice) + '_tweets'}, inplace=True)
#
st.markdown("---")
left3, right3 = st.columns(2)
with left3:
    st.dataframe(df_neg)
st.markdown("---")

# ---- Print Source Data at the Bottom of the Page -----
st.caption("Source Data")

df_selection = df_selection[
    df_selection.columns.difference(['original_text', 'polarity', 'subjectivity', 'possibly_sensitive'])]
gb = GridOptionsBuilder.from_dataframe(df_selection)
gb.configure_pagination(paginationAutoPageSize=True)  # Add pagination
gb.configure_side_bar()  # Add a sidebar
gb.configure_selection('multiple', use_checkbox=True,
                       groupSelectsChildren="Group checkbox select children")  # Enable multi-row selection
gridOptions = gb.build()
grid_response = AgGrid(
    df_selection,
    gridOptions=gridOptions,
    data_return_mode='AS_INPUT',
    update_mode='MODEL_CHANGED',
    fit_columns_on_grid_load=False,
    theme='dark',  # Add theme color to the table
    enable_enterprise_modules=True,
    height=700,
    reload_data=True
)

df_selection = grid_response['data']
selected = grid_response['selected_rows']
df = pd.DataFrame(selected)  # Pass the selected rows to a new dataframe df

#
# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
