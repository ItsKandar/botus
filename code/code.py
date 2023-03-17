import discord
import random
import requests
from mots import mots_fr

TOKEN = 'MTA4NjM0NDU3NDY4OTA5NTc0MQ.GOx7nq.7a7JHR_U0oZqUhV1821JzhyspdMBOTjFIN4d1E'
CHANNEL_ID = 1086348326074593350
DICTIONARY_API_URL = 'https://api.dictionaryapi.dev/api/v2/entries/fr/'

client = discord.Client()

word = ''
correct_letters = []
guessed_letters = []

def new_word():
    global word
    word = random.choice(mots_fr)
    return word

def game_status():
    word_status = ''
    for letter in word.lower():
        if letter in guessed_letters:
            word_status += ' ' + letter.upper() + ' '
        else:
            word_status += ' _ '
    return word_status

new_word()

#jsp
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

# Ping
@client.event
async def on_message(message):
    if message.channel.id == CHANNEL_ID:
        if message.content.lower() == 'mo mo':
            await message.channel.send('motus!')

#Le Motus
@client.event
async def on_message(message):
    global guessed_letters
    if message.channel.id == CHANNEL_ID:
        if message.content.lower() == 'nouveau mot':
            new_word()
            await message.channel.send('Nouveau mot: ' + game_status())
        elif message.content.lower() == 'status':
            await message.channel.send(game_status())
        elif len(message.content) == 1 and message.content.isalpha():
            letter = message.content.lower()
            if letter in guessed_letters:
                await message.channel.send('Vous avez déjà deviné la lettre ' + letter.upper() + '.')
            elif letter in correct_letters:
                guessed_letters.append(letter)
                await message.channel.send('Correct! ' + game_status())
            else:
                guessed_letters.append(letter)
                await message.channel.send('Incorrect! ' + game_status())
        elif message.content.lower() == 'guess word':
            await message.channel.send('Le mot est ' + word + '.')

client.run(TOKEN)