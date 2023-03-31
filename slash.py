import discord
from discord import app_commands
from discord.ext import commands
import random
from mots.mots import mots_fr
from config import RE_TOKEN, DEV_TOKEN, BLACKLIST, DEV_ID, DEVMODE

if DEVMODE:
    TOKEN=DEV_TOKEN
else:
    TOKEN=RE_TOKEN

CHANNEL_NAME = 'motus'

word = ''
correct_letters = []
guessed_letters = []
tries = 0

def resetTries():
    tries = 0
    return tries
    
def new_word():
    global word
    global guessed_letters
    global tries
    word = random.choice(mots_fr)
    correct_letters = list(set(list(word.lower())))
    guessed_letters = []
    resetTries()
    return word, correct_letters, guessed_letters, tries

def game_status():
    word_status = ''
    for letter in word.lower():
        if letter in guessed_letters:
            word_status += ' :regional_indicator_' + letter.lower() + ': '
        else:
            word_status += ' :black_large_square: '
    return word_status

bot = commands.Bot(command_prefix='$', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print('Bot is ready.')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {synced} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name='ping', description='Pong!')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong!')

@bot.tree.command(name='momo', description='Motus!')
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Motus!')


@bot.tree.command(name='say', description='Renvoie ton message')
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

async def on_message(message):

    if 'quoi' in message.content.lower() or 'cwa' in message.content.lower() or 'kwa' in message.content.lower() or 'qwa' in message.content.lower() or 'koi' in message.content.lower():
        roll = random.randint(0, 10)
        if roll <= 0.69:
            await message.channel.send('COUBAKA :star2:')
        if roll <= 3:
            await message.channel.send('COUBE :star:')
        else:
            await message.channel.send('FEUR')
        

bot.run(TOKEN)