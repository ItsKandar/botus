import discord
from discord import app_commands
from discord.ext import commands
import random
from mots.mots import mots_fr
from config import TOKEN, BLACKLIST, DEV_IDs

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


@bot.tree.command(name='say', description='Renvoie ton message')
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

bot.run(TOKEN)