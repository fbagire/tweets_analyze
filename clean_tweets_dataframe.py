import pandas as pd
import string

class CleanTweets:
    """
    This class takes twitter dataframe generated by extract_dataframe.py and clean it
    The class methods takes df arguments and they all return a cleaned dataset

    Arguments:
    -----------

    df= A twitter Dataset

    Returns:
    --------
    A dataframe
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        print('Automation in Action...!!!')

    def drop_unwanted_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        remove rows that has column names. This error originated from
        the data retrieving.
        """
        unwanted_rows_index = df[df['retweet_count'] == 'retweet_count'].index
        df.drop(unwanted_rows_index, inplace=True)
        df = df[df['polarity'] != 'polarity']

        return df

    def drop_duplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        drop duplicated rows
        """
        df = df.drop_duplicates(subset=['cleaned_text'])

        return df

    def convert_to_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        convert column to datetime
        """
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')

        df = df[df['created_at'] >= '2020-12-31']

        return df

    def convert_to_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        convert columns like polarity, subjectivity, retweet_count
        favorite_count etc to numbers
        """
        df['polarity'] = pd.to_numeric(df['polarity'], errors='coerce')
        df['subjectivity'] = pd.to_numeric(df['subjectivity'], errors='coerce')
        df['retweet_count'] = pd.to_numeric(df['retweet_count'], errors='coerce')
        df['favorite_count'] = pd.to_numeric(df['favorite_count'], errors='coerce')

        return df

    def remove_non_english_tweets(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        remove non english tweets from lang
        """

        df.query("lang == 'en' | lang =='fr' ", inplace=True)

        return df

    def treat_special_characters(self, df: pd.DataFrame) -> pd.DataFrame:
        """"
        Remove special characters and redundant characters which cause one location to come out many times
        """
        df['place'] = df['place'].str.capitalize()
        df['place'] = df['place'].replace(r'^.*xico.*', value='Mexico', regex=True)
        df['place'] = df['place'].replace(r'(^.*igali.*)|(^.*wanda.*)', value='Rwanda', regex=True)

        return df


if __name__ == "__main__":
    tweet_df = pd.read_csv("processed_tweet_data.csv")
    cleaner = CleanTweets(tweet_df)

"""To use this class, use it's instance "cleaner" and call every needed method.
    eg.: cleaner.drop_duplicate() return a new df with duplicate rows removed"""
