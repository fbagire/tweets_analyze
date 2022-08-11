from app import app
from dash import html, dcc
import dash_bootstrap_components as dbc
from controls import LANGUAGES, SENTIMENT
from app import app

lang_lst = [{'label': str(LANGUAGES[lang_in]),
             'value': str(lang_in)}
            for lang_in in LANGUAGES]
sent_lst = [{'label': str(SENTIMENT[sent_in]),
             'value': str(sent_in)}
            for sent_in in SENTIMENT]


dbc.Row(dbc.Col(html.Div(
    [
        "Select Sentiment",
        dcc.RadioItems(id='sent_sel',
                       options=sent_lst,
                       value='Positive')
    ]), width=6))
