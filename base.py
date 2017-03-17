import fin_helpers
#import csv
#import json
#import urllib.request
#import sqlite3
import random

#function from sqlite3 homepage to get back dicts of data
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

print('You can query(type any question) or change entry(type change)')

opens = ['How can I help you: ', "What's up?: ", "What do you want to know?: ", 'Something on your mind?: ', 'Ask me about your favorite video game!: ']
_bot = opens[random.randrange(0, len(opens))]
user_request = input(_bot)

if user_request == 'change':
	fin_helpers.update_db(input('What game do you think has an error?'))
else:
	ent_inte = fin_helpers.entry(user_request)
	if ent_inte != None:
		print(fin_helpers.look_up(ent_inte[0], ent_inte[1]))
print("Bye!")
