import discord
import random
import requests
from mots import mots_fr

TOKEN = 'MTA4NjM0NDU3NDY4OTA5NTc0MQ.GOx7nq.7a7JHR_U0oZqUhV1821JzhyspdMBOTjFIN4d1E'
CHANNEL_ID = 1083664002070089748
TEST_CHANNEL_ID = 1086348326074593350

word = ''
correct_letters = []
guessed_letters = []

def new_word():
    global tries
    global word
    tries = 0
    word = random.choice(mots_fr)
    correct_letters = list(set(list(word.lower())))
    guessed_letters = []
    return word

def game_status():
    word_status = ''
    for letter in word.lower():
        if letter in guessed_letters:
            word_status += ' :regional_indicator_' + letter.lower() + ': '
        else:
            word_status += ' :black_large_square: '
    return word_status

new_word()

class MyClient(discord.Client):
    

    # Confirme la connexion
    async def on_ready(self):
        print('Logged in as', self.user)

    # Detecte les messages
    async def on_message(self, message):
    
        if message.channel.id == CHANNEL_ID or TEST_CHANNEL_ID: #verifie que le channel est bien motus

            if message.author == self.user: #ne repond pas a lui meme
                return

            if message.author.id == 482880124442640384: #admin commands :)
                if message.content == '$admot':
                    await message.channel.send('Le mot est : ' + word.upper() + ' !')
                if message.content == '$adwin':
                    await message.channel.send('Bravo, vous avez trouvé! Le mot etait bien "' + word.upper() + '" !')
                    new_word()

            if message.content == '$ping': #ping
                await message.channel.send('Bonjour {}'.format(message.author.mention)+"!")

            if message.content.lower() == '$help': #help
                await message.channel.send('Voici la liste des commandes disponibles: \n\n $start : Commence une nouvelle partie \n $mot : Montre le mot \n $fin : Termine la partie \n $mo mo : motus! \n $help : Affiche cette liste')

            if message.content.lower() == '$mo mo': #mo mo motus!
                await message.channel.send('motus!')

            elif message.content.lower() == '$start': #commence la partie
                new_word()
                await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
            
            elif message.content.lower() == '$mot': #montre le mot
                await message.channel.send(game_status())
            
            elif len(message.content) == len(word) and message.content.isalpha(): #verifie que le mot respecte les conditions
                tries=0 # A modifier
                if message.content.lower() == str(word):
                        await message.channel.send('Bravo, vous avez gagné! Le mot etait bien "' + word.upper() + '" !')
                        new_word()
                        return
                elif tries>=6:
                    await message.channel.send('Vous avez perdu! Le mot etait "' + word.upper() + '".')
                    new_word()
                    return
                else:
                    tries+=1
                    for letter in message.content.lower():
                        if letter in correct_letters: #verifie que la lettre est dans le mot
                            if letter in guessed_letters:
                                pass
                            else:
                                guessed_letters.append(letter)
                        else:
                            if letter in guessed_letters:
                                pass
                            else:
                                guessed_letters.append(letter)
                    else:
                        await message.channel.send(game_status()+ '\n\n' + str(tries)+ '/6 essais.\n' + str(correct) + ' lettres correctes.\n' + 'Lettres essayées : ' + ', '.join(guessed_letters).upper())
            
            elif message.content.lower() == '$fin': #fini la partie
                await message.channel.send('Le mot etait "' + word.upper() + '".')
                new_word()

client = MyClient()

client.run(TOKEN) #run bot