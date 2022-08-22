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

    def drop_unwanted_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        remove rows that has column names. This error originated from
        the data retrieving.
        """
        unwanted_rows_index = df[df['retweet_count'] == 'retweet_count'].index
        df.drop(unwanted_rows_index, inplace=True)
        df = df[df['polarity'] != 'polarity']

        return df

    def drop_retweets(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        drop retweets
        """
        # df = df.query("tweet_category=='Tweet' or tweet_category== 'Reply'")
        df = df.drop_duplicates(subset=['original_text', 'original_author'])
        df = df[df.original_author != 'RepDeFiFidonia']
        df = df[df.original_author != 'republikaonline']
        return df

    def convert_to_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        convert column to datetime
        """
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')

        return df

    def convert_to_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        convert columns like polarity, subjectivity, retweet_count
        favorite_count etc to numbers
        """
        df['polarity'] = pd.to_numeric(df['polarity'], errors='coerce')
        df['subjectivity'] = pd.to_numeric(df['subjectivity'], errors='coerce')
        df['retweet_count'] = pd.to_numeric(df['retweet_count'], errors='coerce')
        df['likes_count'] = pd.to_numeric(df['likes_count'], errors='coerce')

        return df

    def remove_other_languages_tweets(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        remove non english,french, kinyarwanda tweets from lang
        """
        df['lang'] = df['lang'].replace('in', value='kiny')
        df['lang'] = df['lang'].replace('tl', value='kiny')
        # df['lang'] = df['lang'].replace('de', value='kiny')
        df['lang'] = df['lang'].replace('ht', value='kiny')

        df.query("lang == 'en' | lang =='fr' | lang == 'kiny' ", inplace=True)

        return df

    def treat_special_characters(self, df: pd.DataFrame) -> pd.DataFrame:
        """"
        Remove special characters and redundant characters which cause one location to come out many times
        """
        df['place'] = df['place'].str.lower()
        df['place'] = df['place'].replace(r'^.*xico.*', value='Mexico', regex=True)
        df['place'] = df['place'].replace(r'(^.*[kK]igali.*)|(^.*wanda.*)', value='Rwanda', regex=True)
        df['place'] = df['place'].replace(r'(^.*[Kk]inshasa.*)|(.*congo.*)|(.*drc.*)|(.*rdc.*)|(.*démocratique du.*)',
                                          value='DRC Congo',
                                          regex=True)
        df['place'] = df['place'].replace('bukavu', 'DR Congo', regex=True)
        df['place'] = df['place'].replace('goma', 'DR Congo', regex=True)
        return df


if __name__ == "__main__":
    tweet_df = pd.read_excel("processed_tweet_data.xlsx", engine='openpyxl')
    cleaner = CleanTweets(tweet_df)

"""To use this class, use it's instance "cleaner" and call every needed method.
    eg.: cleaner.drop_duplicate() return a new df with duplicate rows removed"""
