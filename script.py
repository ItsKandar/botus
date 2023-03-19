import discord
import random
import requests
from mots import mots_fr

TOKEN = 'MTA4NjM0NDU3NDY4OTA5NTc0MQ.GOx7nq.7a7JHR_U0oZqUhV1821JzhyspdMBOTjFIN4d1E'
CHANNEL_ID = [1083664002070089748, 1086348326074593350, 1087094319787278466]
DEV_ID = [482880124442640384, 227735537065132032]

word = ''
correct_letters = []
guessed_letters = []
tries = 0

def resetTries():
    tries = 0
    return tries
    
def new_word():
    global word
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

class MyClient(discord.Client):

    new_word()
    resetTries()

    # Confirme la connexion
    async def on_ready(self):
        print('Logged in as', self.user)

    # Detecte les messages
    async def on_message(self, message):
        global tries
        global correct_letters
        global guessed_letters

        if message.author.id in DEV_ID: #admin commands :)

            if message.content == '$adadd': #ajoute un channel
                CHANNEL_ID.append(message.channel.id)
                await message.channel.send('Channel ajouté!')

            if message.content == '$adremove': #enleve un channel
                CHANNEL_ID.remove(message.channel.id)
                await message.channel.send('Channel enlevé!')

            if message.content == '$admot': #montre le mot
                await message.channel.send('Le mot est : ' + word.upper() + ' !')

            if message.content == '$adwin': #gagne la partie
                await message.channel.send('Bravo, vous avez trouvé! Le mot etait bien "' + word.upper() + '" !')
                new_word()

            if message.content == '$adlose': #perd la partie
                await message.channel.send('Vous avez perdu! Le mot etait "' + word.upper() + '".')
                new_word()

            if message.content == '$adreset': #remet le nombre d'essais a 0
                resetTries()
                await message.channel.send('Nombre d\'essais remis a 0!')

            if message.content == '$adviewtries': #montre le nombre d'essais
                await message.channel.send('Nombre d\'essais : ' + str(tries))
            
            if message.content == '$adletters': #montre les lettres correctes
                await message.channel.send('Lettres correctes : ' + str(correct_letters))

            if message.content=='$adviewguessed': #montre les lettres essayees
                await message.channel.send('Lettres essayees : ' + str(guessed_letters))
            
            if message.content == '$adviewchannels': #montre les channels
                await message.channel.send('Channels : ' + str(CHANNEL_ID))
            
            if message.content == '$adresetguessed': #retire les lettres essayees
                guessed_letters = []
                await message.channel.send('Lettres essayees retirees!')
                    
            if message.content == '$adhelp': #affiche la liste des commandes admin
                await message.channel.send(':spy: Commandes secretes :spy:: \n\n $adadd : Ajoute le channel \n $adremove : Retire le channel \n $adviewtries : Montre le nombre d\'essais \n $adviewchannels : Montre les channels \n $admot : Montre le mot \n $adwin : Gagne la partie \n $adlose : Perd la partie \n $adreset : Remet le nombre d\'essais a 0 \n $adletters : Montre les lettres correctes \n $adviewguessed : Montre les lettres essayees \n $adresetguessed : Retire les lettres essayees \n $adhelp : Affiche cette liste')

        #verifie que le channel est bien motus
        if message.channel.id in CHANNEL_ID:

            #ignore lui meme
            if message.author == self.user: 
                return
            
            if message.content == '$ping': #ping
                await message.channel.send('Bonjour {}'.format(message.author.mention)+"!")

            if message.content.lower() == '$help': #help
                await message.channel.send('Voici la liste des commandes disponibles: \n\n $start : Commence une nouvelle partie \n $mot : Montre le mot \n $fin : Termine la partie \n $mo mo : motus! \n $help : Affiche cette liste')

            if message.content.lower() == '$mo mo': #mo mo motus!
                await message.channel.send('motus!')

            if message.content.lower() == '$start': #commence la partie
                new_word()
                await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
            
            if message.content.lower() == '$mot': #montre le mot
                await message.channel.send(game_status())

            if message.content.lower() == '$fin': #fini la partie
                await message.channel.send('Le mot etait "' + word.upper() + '".')
                new_word()

            elif len(message.content) == len(word) and message.content.isalpha(): #verifie que le mot respecte les conditions
                
                if message.content.lower() == str(word): #verifie si l'utilisateur a gagne
                        await message.channel.send('Bravo, vous avez gagné! Le mot etait bien "' + word.upper() + '" !')
                        new_word()
                        return
                elif tries>=6: #verifie si l'utilisateur a perdu
                    await message.channel.send('Vous avez perdu! Le mot etait "' + word.upper() + '".')
                    new_word()
                    return
                else:
                    tries+=1 #ajoute un essai
                    for letter in message.content.lower():
                        if letter in correct_letters: #verifie que la lettre est dans le mot
                            if letter in guessed_letters: #verifie que la lettre n'a pas deja ete essayee
                                pass
                            else: #si la lettre est correcte et n'a pas deja ete essayee
                                guessed_letters.append(letter)
                        else:
                            if letter in guessed_letters: 
                                pass
                            else: #si la lettre est incorrecte et n'a pas deja ete essayee
                                guessed_letters.append(letter) 
                    else:
                        await message.channel.send(game_status()+ '\n\n' + str(tries)+ '/6 essais.\n' + 'Lettres essayées : ' + ', '.join(guessed_letters).upper())
            
            
client = MyClient()

client.run(TOKEN) #run bot