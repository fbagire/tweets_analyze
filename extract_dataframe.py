import json
import pandas as pd
from textblob import TextBlob
import numpy as np
import re


def read_json(json_tweets_file: str) -> list:
    """
    json file reader to open and read json files into a list of tweets
    Args:
    -----
    json_tweets_file: str - path of a json file
    
    Returns
    -------
    A list of all tweets from a json file(input)
    """

    tweets_list = []
    file_use = open(json_tweets_file, 'r')

    for tweets in file_use:
        tweets_list.append(json.loads(tweets))

    file_use.close()

    return len(tweets_list), tweets_list


class TweetDfExtractor:
    """
    this function will parse tweets json into a pandas dataframe
    
    Return
    ------
    dataframe
    """

    def __init__(self, tweets_list):

        self.tweets_list = tweets_list

    # # an example function
    def find_statuses_count(self) -> list:
        statuses_count = [x['user']['statuses_count'] for x in self.tweets_list]
        return statuses_count

    def find_full_text(self) -> list:
        text = []
        for tweet in self.tweets_list:

            # if 'extended_tweet' in tweet.keys():
            #     # Store the extended tweet text if the tweet is a thread otherwise store just the text'
            #     text.append(tweet['extended_tweet']['text'])
            if 'text' in tweet.keys():
                text.append(tweet['text'])
            elif 'referenced_tweets' in tweet.keys():
                text.append(tweet['referenced_tweets'][0]['text'])
            else:
                text.append(np.nan)
        return text

    def text_cleaner(self, text: list) -> list:
        clean_text = []
        for tweet_text in text:
            tweet_text = re.sub("^RT ", "", tweet_text)
            # mentions and hashtags
            tweet_text = re.sub("@[A-Za-z0-9:_]+", "", tweet_text)
            tweet_text = re.sub("#[A-Za-z0-9_]+", "", tweet_text)
            # remove links
            tweet_text = re.sub("http\S+", "", tweet_text)
            tweet_text = re.sub(r"www.\S+", "", tweet_text)
            tweet_text = re.sub("^ ", "", tweet_text)

            clean_text.append(tweet_text)
        return clean_text

    def find_sentiments(self, text: list) -> list:

        polarity = []
        subjectivity = []
        sentiment_class = []
        for tweet in text:
            blob = TextBlob(tweet)
            sentiment = blob.sentiment
            polarity.append(sentiment.polarity)
            subjectivity.append(sentiment.subjectivity)

            if sentiment.polarity > 0:
                sentiment_class.append('Positive')
            elif sentiment.polarity < 0:
                sentiment_class.append('Negative')
            else:
                sentiment_class.append('Neutral')

        return polarity, subjectivity, sentiment_class

    def find_created_time(self) -> list:
        created_at = [x['created_at'] for x in self.tweets_list]

        return created_at

    def find_source(self) -> list:
        source = [x['source'] for x in self.tweets_list]

        return source

    def find_screen_name(self) -> list:
        screen_name = []
        for tweet in self.tweets_list:
            try:
                screen_name.append(tweet['author']['username'])
            except KeyError:
                screen_name.append(np.nan)
        return screen_name

    def find_followers_count(self) -> list:
        followers_count = []
        for tweet in self.tweets_list:
            try:
                followers_count.append(tweet['author']['public_metrics']['followers_count'])
            except KeyError:
                followers_count.append(np.nan)
        return followers_count

    def find_friends_count(self) -> list:
        friends_count = []
        for tweet in self.tweets_list:
            try:
                friends_count.append(tweet['author']['public_metrics']['following_count'])
            except KeyError:
                friends_count.append(np.nan)
        return friends_count

    def is_sensitive(self) -> list:

        is_sensitive = [tweet['possibly_sensitive'] if 'possibly_sensitive' in tweet.keys() else None for tweet in
                        self.tweets_list]

        return is_sensitive

    def find_likes_count(self) -> list:
        likes_count = []
        for tweet in self.tweets_list:
            try:
                likes_count.append(tweet['public_metrics']['like_count'])
            except KeyError:
                likes_count.append(0)

        return likes_count

    def find_retweet_count(self) -> list:

        retweet_count = []
        for tweet in self.tweets_list:
            # if 'public_metrics' in tweet.keys():
            try:
                retweet_count.append(tweet['public_metrics']['retweet_count'])
            except KeyError:
                retweet_count.append(0)

        return retweet_count

    def find_hashtags(self) -> list:
        hashtags = []
        for tweet in self.tweets_list:
            if 'entities' in tweet.keys() and 'hashtags' in tweet['entities'].keys():
                hashtags.append(", ".join([hashtag['tag'] for hashtag in tweet['entities']['hashtags']]))
            else:
                hashtags.append(np.nan)
        return hashtags

    def find_retweet_hashtags(self) -> list:
        retweet_hashtags = []
        for tweet in self.tweets_list:
            if 'referenced_tweets' in tweet.keys():
                try:
                    retweet_hashtags.append(", ".join(
                        [hashtag['tag'] for hashtag in tweet['referenced_tweets'][0]['entities']['hashtags']]))
                except:
                    retweet_hashtags.append(np.nan)
            else:
                retweet_hashtags.append(np.nan)

        return retweet_hashtags

    def find_mentions(self) -> list:

        mentions = []
        for tweet in self.tweets_list:
            if 'entities' in tweet.keys() and 'mentions' in tweet['entities'].keys():
                mentions.append(", ".join([mention['username'] for mention in tweet['entities']['mentions']]))
            else:
                mentions.append(np.nan)

        return mentions

    def find_lang(self) -> list:
        lang = []
        for tweet in self.tweets_list:
            try:
                lang.append(tweet['lang'])
            except KeyError:
                lang.append(np.nan)
        return lang

    def find_location(self) -> list:
        location = []
        for tweet in self.tweets_list:
            try:
                location.append(tweet['author']['location'])
            except KeyError:
                location.append(np.nan)
        return location

    def get_tweet_id(self) -> list:
        tweet_id = []
        for tweet in self.tweets_list:
            try:
                tweet_id.append(str(tweet['id']))
            except KeyError:
                tweet_id.append(np.nan)
        return tweet_id

    def get_tweet_url(self) -> list:
        tweet_url = []
        for tweet in self.tweets_list:
            if 'referenced_tweets' in tweet:
                try:
                    tweet_url.append(", ".join([url['expanded_url'] for url in tweet['entities']['urls']]))
                except KeyError:
                    tweet_url.append(np.nan)
            else:
                tweet_url.append(np.nan)
        return tweet_url

    def get_tweet_df(self, save=False) -> pd.DataFrame:
        save = True
        """required column to be generated you should be creative and add more features"""
        columns = ['created_at', 'source', 'original_text', 'cleaned_text', 'polarity', 'polarity_clean',
                   'subjectivity', 'subjectivity_clean', 'lang', 'likes_count', 'retweet_count',
                   'original_author', 'followers_count', 'friends_count', 'possibly_sensitive', 'hashtags',
                   'user_mentions', 'place', 'tweet_url', 'tweet_id']

        created_at = self.find_created_time()
        source = self.find_source()
        text = self.find_full_text()
        text_new = self.text_cleaner(text)
        polarity, subjectivity, _ = self.find_sentiments(text_new)
        _, _, sentiment = self.find_sentiments(text_new)
        lang = self.find_lang()
        likes_count = self.find_likes_count()
        retweet_count = self.find_retweet_count()
        screen_name = self.find_screen_name()
        follower_count = self.find_followers_count()
        friends_count = self.find_friends_count()
        sensitivity = self.is_sensitive()
        hashtags = self.find_hashtags()
        retweet_hashtags = self.find_retweet_hashtags()
        mentions = self.find_mentions()
        location = self.find_location()
        tweet_url = self.get_tweet_url()
        tweet_id = self.get_tweet_id()

        data_dic = {'created_at': created_at, 'source': source, 'original_text': text, 'cleaned_text': text_new,
                    'polarity': polarity, 'subjectivity': subjectivity, 'sentiment': sentiment, 'lang': lang,
                    'likes_count': likes_count, 'retweet_count': retweet_count, 'original_author': screen_name,
                    'followers_count': follower_count, 'friends_count': friends_count,
                    'possibly_sensitive': sensitivity, 'hashtags': hashtags, 'retweet_hashtags': retweet_hashtags,
                    'user_mentions': mentions, 'place': location,
                    'tweet_url': tweet_url, 'tweet_id': tweet_id}

        df = pd.DataFrame.from_dict(data_dic, orient='index')
        df = df.transpose()
        if save:
            df.to_excel('processed_tweet_data.xlsx', index=False)
            print('File Successfully Saved.!!!')

        return df


if __name__ == "__main__":
    _, tweet_list = read_json("data/tweets_flat.json")

    tweety = TweetDfExtractor(tweet_list)
    df = tweety.get_tweet_df()
