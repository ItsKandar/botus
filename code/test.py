import discord
import random
import requests
from mots import mots_fr

TOKEN = 'MTA4NjM0NDU3NDY4OTA5NTc0MQ.GOx7nq.7a7JHR_U0oZqUhV1821JzhyspdMBOTjFIN4d1E'
CHANNEL_ID = 1086348326074593350
DICTIONARY_API_URL = 'https://api.dictionaryapi.dev/api/v2/entries/fr/'

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == '$the_ping_cmd':
            await message.channel.send('Pinging {}'.format(message.author.mention))

client = MyClient()
client.run(TOKEN)