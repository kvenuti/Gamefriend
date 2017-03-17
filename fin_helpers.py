import csv
import json
import urllib.request
import sqlite3

#function from sqlite3 homepage to get back dicts of data
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn = sqlite3.connect('game_info.sqlite')
conn.row_factory = dict_factory
cursor = conn.cursor()

STANDARD = "https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/f309213f-335e-4573-b429-330045fa5c63?subscription-key=6d598c367cdc4bf8b76637d376198dd1&verbose=true&q="

#takes in question and reutrns all pertinent information
def entry(query):
	new_query = query.replace(" ", "%20")
	req = STANDARD + ("".join(new_query))
	#req = req + '&verbose=true'  -  this was uesed in the old luis
	resp = urllib.request.urlopen(req).read().decode("utf-8")
	json_out = json.loads(resp)
	#this part important
	out_entities = extract_entities(json_out)
	out_intent = extract_intent(json_out)

	if bool(out_entities) == False:
		print("I didn't recognize a game name??? ")
	elif out_intent == 'None':
		print("I didn't recognize what you wanted to know about %s." % out_entities['GameName'].lower())
	else:
		return out_entities, out_intent
	return None
#extracts all entities in statmenet
def extract_entities(json_out):
	entities = {}
	for ent in json_out['entities']:
		title = ent['entity']
		type_t = ent['type']
		entities[type_t] = title
	return entities

#extracts intent in statmenet and must have above .3 confidence
def extract_intent(json_out):
	score = 0.0
	place = 0
	for index, tent in enumerate(json_out['intents']):
		if tent['score'] > score and tent['score'] >= .3:
			score = tent['score']
			place = index
	return json_out['intents'][place]['intent']

#looks up stuff in sqlite3 database
def look_up(entities, intent):
	ent_game = entities['GameName'].lower()

	_fullselection = cursor.execute('''SELECT * FROM game_tables WHERE game_name = ?''', (ent_game, ))
	#this now returns a dictionary
	full_selection = _fullselection.fetchone()

	if(full_selection is None):
		answer = input("Sorry, I haven't heard of that game. Want to add the information? Y/N: ")
		if answer.lower() == 'y':
			return add_to_db(ent_game)
		return
	#checking with console question
	if intent == 'GamePlatforms':
		_consoleselection = cursor.execute('''SELECT * FROM console_type WHERE console_type_id = ?''', (full_selection['for_console'], ))
		console_selection = _consoleselection.fetchone()
		if entities['ConsoleType'] == console_selection['console_type_name']:
			#return(entities['ConsoleType'] ,console_selection['console_type_name'])
			#should be able to ask it what consoles is it avaulble for
			#it found the console type
			return 'Yes'
		else:
			return 'No, only availble on ' + console_selection['console_type_name']
	elif intent == 'GameMaker':
		_consoleselection = cursor.execute('''SELECT * FROM game_maker WHERE game_maker_id = ?''', (full_selection['for_maker'], ))
		console_selection = _consoleselection.fetchone()
		if entities['GameCreator'] == console_selection['game_maker_name']:
			#it found the creator
			return 'Yes'
		else:
			return 'No, ' + console_selection['game_maker_name'] + ' made it'
	elif intent == 'GamePrice':
		return str(full_selection['game_price']) + '$'
	elif intent == 'GameOpinion':
		return full_selection['game_summary']
	elif intent == 'GamePop':
		return str(full_selection['game_pop'])
	else:
		return "I messed up!"

def add_to_db(name):
	entry_dic = {'game_summary': "What's the game summary?",
	'console_type_name': "What consoles is it availble for?",
	'game_pop': "How many people play the game?",
	'game_price': "How much does it cost?",
	'game_maker_name': "Who made it?"}

	for key, value in entry_dic.items():
		#add back in
		temp = input(value)
		entry_dic[key] = temp

	entry_dic['game_name'] = name

	maker = entry_dic['game_maker_name'].lower()
	console = entry_dic['console_type_name'].lower()

	try:
		entry_dic['game_price'] = int(entry_dic['game_price'])
	except:
		print("Game price needs to be a number, please re-enter!")
		add_to_db(name)
		return
	try:
		entry_dic['game_pop'] = int(entry_dic['game_pop'])
	except:
		print("Game population needs to be a number, please re-enter!")
		add_to_db(name)
		return

	cursor.execute('''INSERT OR IGNORE INTO game_maker (game_maker_name) VALUES (?)''', (maker, ))
	_sql_maker = cursor.execute('''SELECT game_maker_id FROM game_maker WHERE game_maker_name = ?''', (maker, ))
	#had to add here because of fetchone messing with doing at the same time
	sql_maker = _sql_maker.fetchone()

	cursor.execute('''INSERT OR IGNORE INTO console_type (console_type_name) VALUES (?)''', (console, ))
	_sql_console = cursor.execute('''SELECT console_type_id FROM console_type WHERE console_type_name = ?''', (console, ))
	sql_console = _sql_console.fetchone()

	cursor.execute('''INSERT INTO game_tables (game_name, game_summary,
				game_pop, game_price, for_console, for_maker)
	 			VALUES (?, ?, ?, ?, ?, ?)''', (entry_dic['game_name'], entry_dic['game_summary'],
				entry_dic['game_pop'], entry_dic['game_price'], sql_console['console_type_id'], sql_maker['game_maker_id']))
	conn.commit()
	return "Added!"

def update_db(game_name):
	game_name = game_name.lower()

	#check if in db
	_gameselection = cursor.execute('''SELECT * FROM game_tables WHERE game_name = ?''', (game_name, ))
	game_selection = _gameselection.fetchone()
	if(game_selection is None):
		answer = input("Sorry, I haven't heard of that game. Want to add the information? Y/N: ")
		if answer.lower() == 'y':
			return add_to_db(ent_game)
		return

	comps = {'Game Summary':'game_summary',
	'Console':'console_type_name',
	'Game Population':'game_pop',
	'Game Price':'game_price',
	'Game Maker':'game_maker_name'}

	name_inc = input('What is wrong with %s ? Please type one in at a time: %a. ' % (game_name, list(comps.keys())))
	if(name_inc in list(comps.keys()) == False):
		print("That's not one of the options")
		update_db(game_name)
		return

	error_term = comps[name_inc]
	update_term = input('What should %s be? ' % name_inc)
	if error_term == 'console_type_name':
		update_term = update_term.lower()
		cursor.execute('''INSERT OR IGNORE INTO console_type (console_type_name) VALUES (?)''', (update_term, ))

		_consoleselection = cursor.execute('''SELECT console_type_id FROM console_type WHERE console_type_name = ?''', (update_term, ))
		console_selection = _consoleselection.fetchone()

		cursor.execute('''UPDATE game_tables SET for_console = ? WHERE game_name = ?''', (console_selection['console_type_id'], game_name, ))
		conn.commit()
		print("Changed!")

	elif error_term == 'game_maker_name':
		update_term = update_term.lower()
		cursor.execute('''INSERT OR IGNORE INTO game_maker (game_maker_name) VALUES (?)''', (update_term, ))

		_makerselection = cursor.execute('''SELECT game_maker_id FROM game_maker WHERE game_maker_name = ?''', (update_term, ))
		maker_selection = _makerselection.fetchone()

		cursor.execute('''UPDATE game_tables SET for_maker = ? WHERE game_name = ?''', (maker_selection['game_maker_id'], game_name, ))
		conn.commit()
		print("Changed!")

	elif(error_term == 'game_price' or error_term == 'game_pop'):
		try:
			update_term = int(update_term)
		except:
			print("You need a number for %s!" % name_inc)
			update_db(game_name)
			return
		#otherwise pretty simple
		cursor.execute('''UPDATE game_tables SET %s = ? WHERE game_name = ?''' % error_term, (update_term, game_name, ))
		conn.commit()
		print("Changed!")

	elif(error_term == 'game_summary'):
		cursor.execute('''UPDATE game_tables SET %s = ? WHERE game_name = ?''' % error_term, (update_term, game_name, ))
		conn.commit()
		print("Changed!")

	ans = input('Want to change something else for %s ? Y/N: ' % game_name)
	if ans.lower() == 'y':
		update_db(game_name)
		return
	return