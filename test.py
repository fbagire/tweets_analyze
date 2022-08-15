from cleantext import clean

s = "¿Pos de cuál \;i- \n     %!$ orégano le puso al pozole, oiga? 🤔 Esa clase de viajes no los tenía ni Bob Marley. 🙊🐅"

print(clean(s, no_emoji=True, no_punct=True, no_line_breaks=True))
# import pygsheets
# gc = pygsheets.authorize()

# gc = pygsheets.authorize(service_file='tweet-auto-01-833e318c05c8.json')

# sh = gc.open('hh_test')
