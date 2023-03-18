import discord
import random
import requests
from mots import mots_fr

TOKEN = 'MTA4NjM0NDU3NDY4OTA5NTc0MQ.GOx7nq.7a7JHR_U0oZqUhV1821JzhyspdMBOTjFIN4d1E'
CHANNEL_ID = 1086348326074593350
DICTIONARY_API_URL = 'https://api.dictionaryapi.dev/api/v2/entries/fr/'

word = ''
correct_letters = []
guessed_letters = []

def new_word():
    global word
    word = random.choice(mots_fr)
    correct_letters = list(set(list(word.lower())))
    guessed_letters = []
    return word

def game_status():
    word_status = ''
    for letter in word.lower():
        if letter in guessed_letters:
            word_status += ' ' + letter.upper() + ' '
        else:
            word_status += ' :black_large_square: '
    return word_status

new_word()

class MyClient(discord.Client):
    

    #jsp
    async def on_ready(self):
        print('Logged in as', self.user)

    # Ping
    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content == '$ping':
            await message.channel.send('Pinging {}'.format(message.author.mention))
        
        elif message.channel.id == CHANNEL_ID:
            if message.content.lower() == '$mo mo':
                await message.channel.send('motus!')

            elif message.content.lower() == '$start': #start game
                new_word()
                await message.channel.send('Nouveau mot: \n' + game_status())
            
            elif message.content.lower() == '$mot': #montre le mot
                await message.channel.send(game_status())
            
            elif len(message.content) == 1 and message.content.isalpha():
                letter = message.content.lower()
                if letter in guessed_letters: #verifie si la lettre a deja ete essayee
                    await message.channel.send('Vous avez déjà essayé la lettre ' + ":regional_indicator_"+letter.lower()+":" + '.')
                elif letter in correct_letters: #verifie que la lettre est dans le mot
                    guessed_letters.append(letter)
                    await message.channel.send(game_status())
                else:
                    guessed_letters.append(letter)
                    await message.channel.send(game_status())
            
            elif message.content.lower() == '$fin': #end game
                await message.channel.send('Le mot etait ' + word + '.')
                new_word()
client = MyClient()
client.run(TOKEN)

#coucou yusan