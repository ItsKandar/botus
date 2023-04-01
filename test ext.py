import discord
from discord.ext import commands
import sqlite3
import random
from mots.mots import mots_fr
from config import RE_TOKEN, BLACKLIST, DEV_ID, DEV_TOKEN, DEVMODE

# Créer ou ouvrir la base de données SQLite
conn = sqlite3.connect("servers.db")
c = conn.cursor()

# Créer la table "servers" et ses columns si elles n'existent pas déjà
def column_exists(cursor, table_name, column_name):
    cursor.execute("PRAGMA table_info({})".format(table_name))
    columns = cursor.fetchall()
    for column in columns:
        if column[1] == column_name:
            return True
    return False

c.execute("CREATE TABLE IF NOT EXISTS servers (id TEXT PRIMARY KEY, prefix TEXT)")
conn.commit()

if not column_exists(c, "servers", "channel_id"):
    c.execute("ALTER TABLE servers ADD COLUMN channel_id TEXT")

if not column_exists(c, "servers", "quoifeur"):
    c.execute("ALTER TABLE servers ADD COLUMN quoifeur INTEGER")

conn.commit()



CHANNEL_NAME = 'motus'
TOKEN=''
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

if DEVMODE:
    TOKEN=DEV_TOKEN
else:
    TOKEN=RE_TOKEN

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

# Récupère le préfixe du serveur
async def get_prefix(bot, message):
    guild_id = message.guild.id
    c.execute("SELECT prefix FROM servers WHERE id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        prefix = "!"
        c.execute("INSERT INTO servers VALUES (?, ?)", (guild_id, prefix))
        conn.commit()
    else:
        prefix = row[0]
    return prefix

async def get_channel_id(bot, message):
    guild_id = message.guild.id
    c.execute("SELECT channel_id FROM servers WHERE id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        channel_id = message.channel.id
        c.execute("INSERT INTO servers VALUES (?, ?)", (guild_id, channel_id))
        conn.commit()
    else:
        channel_id = row[0]
    return channel_id

async def get_quoifeur(bot, message):
    guild_id = message.guild.id
    c.execute("SELECT quoifeur FROM servers WHERE id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        quoifeur = 0
        c.execute("INSERT INTO servers VALUES (?, ?)", (guild_id, quoifeur))
        conn.commit()
    else:
        quoifeur = row[0]
    return quoifeur


bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# Confirme la connexion
@bot.event
async def on_ready():
    print('Logged in as', bot.user)
    await bot.change_presence(activity=discord.Game(name='Maintenant sur le cloud!'))

# Detecte les messages
@bot.command()
async def set_prefix(ctx, prefix: str):
    guild_id = ctx.guild.id
    c.execute("UPDATE servers SET prefix=? WHERE id=?", (prefix, guild_id))
    conn.commit()
    await ctx.send(f"Préfixe mis à jour: {prefix}")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latence: {latency}ms")

# Surveiller les messages mentionnant le bot pour la commande get_prefix
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        prefix = await get_prefix(bot, message)
        await message.channel.send(f"Le préfixe actuel pour ce serveur est : `{prefix}`")

    await bot.process_commands(message)

@bot.event
async def on_message(message):
    global tries
    global correct_letters
    global guessed_letters

    #ignore lui meme ou utilisateur blacklisté
    if message.author == bot.user or message.author in BLACKLIST: 
        return

    # Faites pas attention
    if get_quoifeur == 1:
        if 'quoi' in message.content.lower() or 'cwa' in message.content.lower() or 'kwa' in message.content.lower() or 'qwa' in message.content.lower() or 'koi' in message.content.lower():
            await message.channel.send('FEUR')

        if 'ui' in message.content.lower():
            roll = random.randint(0, 10)
            if roll <= 1:
                await message.channel.send('STITI :star2:')
            else:
                await message.channel.send('FI')


    if message.author.id in DEV_ID: #admin commands :)

        if bot.user in message.mentions:
            prefix = await get_prefix(bot, message)
            await message.channel.send(f"Le préfixe actuel pour ce serveur est : `{prefix}`")

        await bot.process_commands(message)

        if message.content == '$adcreate': #crée un channel #motus si il n'yen a pas encore
            CHANNELS = []
            for salon in message.guild.text_channels:
                CHANNELS.append(salon.name)
            if CHANNEL_NAME not in CHANNELS: #verifie si le channel existe deja
                await message.guild.create_text_channel(CHANNEL_NAME) #crée le channel
                await message.channel.send('Channel créé!')
            else:
                await message.channel.send('Le channel existe deja!')

        if message.content == '$adrestart': #restart bot
            await message.channel.send('Redemarrage en cours...')
            await bot.close()
            await bot.start(TOKEN)

        if message.content == '$adstop':
            await message.channel.send('Arret en cours...')
            await bot.close()

        if message.content == '$adquoifeur':
            quoifeur = 1
            guild_id = message.guild.id
            c.execute("UPDATE servers SET quoifeur=? WHERE id=?", (quoifeur, guild_id))
            conn.commit()
            await message.channel.send('Quoifeur activé!')

        if message.content == '$adquoifeuroff':
            quoifeur = 0
            guild_id = message.guild.id
            c.execute("UPDATE servers SET quoifeur=? WHERE id=?", (quoifeur, guild_id))
            conn.commit()
            await message.channel.send('Quoifeur désactivé!')

        if '$adsay' in message.content:
            await message.channel.send(message.content[7:])
            await message.delete()

        if '$adstatus' in message.content:
            await bot.change_presence(activity=discord.Game(name=message.content[9:]))
            await message.channel.send('Status changé!')

        if message.content[:12] == '$adblacklist': #blacklist quelqu'un
            BLACKLIST.append(message.mentions[0])
            await message.channel.send('Utilisateur blacklisté!')
        
        if message.content[:14] == '$adunblacklist': #unblacklist quelqu'un
            if message.mentions[0] in BLACKLIST:
                BLACKLIST.remove(message.mentions[0])
                await message.channel.send('Utilisateur unblacklisté!')
            else:
                await message.channel.send('Cet utilisateur n\'est pas blacklisté!')

        if message.content == '$admot': #montre le mot
            await message.author.send('Le mot est : ' + word.upper() + ' !')
            await message.channel.send('Le mot a été envoyé en DM!')

        if message.content == '$adwin': #gagne la partie
            await message.channel.send('Bravo, vous avez trouvé! Le mot etait bien "' + word.upper() + '" !')
            new_word()
            tries = 0
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
        

        if message.content == '$adlose': #perd la partie
            await message.channel.send('Vous avez perdu! Le mot etait "' + word.upper() + '".')
            new_word()
            tries = 0
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
        

        if message.content == '$adreset': #remet le nombre d'essais a 0
            resetTries()
            await message.channel.send('Nombre d\'essais remis a 0!')

        if message.content == '$adviewtries': #montre le nombre d'essais
            await message.channel.send('Nombre d\'essais : ' + str(tries))
        
        if message.content == '$adletters': #montre les lettres correctes
            await message.channel.send('Lettres correctes : ' + str(correct_letters))

        if message.content=='$adviewguessed': #montre les lettres essayees
            await message.channel.send('Lettres essayees : ' + str(guessed_letters))
        
        if message.content == '$adresetguessed': #retire les lettres essayees
            guessed_letters = []
            await message.channel.send('Lettres essayees retirees!')
                
        if message.content == '$adhelp': #envoie en DM les commandes admins
            await message.author.send(':spy: Commandes secretes :spy:: \n\n $adviewtries : Montre le nombre d\'essais \n $admot : Montre le mot \n $adwin : Gagne la partie \n $adlose : Perd la partie \n $adreset : Remet le nombre d\'essais a 0 \n $adletters : Montre les lettres correctes \n $adviewguessed : Montre les lettres essayees \n $adresetguessed : Retire les lettres essayees\n $adblacklist : Blackliste quelqu\'un \n $adunblacklist : Unblackliste quelqu\'un \n $adstatus : Change le status du bot \n $adsay : Fait dire quelque chose au bot \n $adcreate : Crée un channel #motus \n $adstop : Arrete le bot \n $adhelp : Affiche cette liste \n $adrestart : Redemarre le bot \n $adquoifeur : Active le quoifeur \n $adquoifeuroff : Desactive le quoifeur')
            await message.channel.send('Commandes admins secrètes envoyé en mp :ok_hand: :spy:')

    #verifie que le channel est bien motus
    if message.channel.name == CHANNEL_NAME:
        
        if message.content == '$ping': #ping
            await message.channel.send('Bonjour {}'.format(message.author.mention)+"!")

        if message.content.lower() == '$help': #help
            await message.channel.send('Voici la liste des commandes disponibles: \n\n $start : Commence une nouvelle partie \n $mot : Montre le mot \n $fin : Termine la partie \n $mo mo : motus! \n $help : Affiche cette liste \n $ping : Ping! \n $bug : Signale un bug \n $suggest : Suggere un mot \n $server : Envoie le lien du serveur support')

        if message.content.lower() == '$mo mo': #mo mo motus!
            await message.channel.send('motus!')

        if message.content.lower() == '$server': #envoie le lien du serveur support
            await message.channel.send('Voici le lien du serveur Motus! : https://discord.gg/4M6596sjZa')

        if '$bug' in message.content.lower()[:4]: #report un bug
            if message.content.lower()[5:] == "":
                await message.channel.send("Merci de decrire le bug!")
                return
            await bot.get_channel(1090643512220983346).send("**<@&1090635527058898944>\nBUG REPORT DE " + message.author.mention +" aka " + str(message.author) + " dans le channel #"  + str(message.channel) + "**\n\n**LIEN DU REPORT**\n" + message.jump_url + "\n\n**MESSAGE**\n" + message.content[5:])
            # add a reaction (:white_check_mark:) to the message sent in 1090271020956516393
            await message.add_reaction('\U00002705') #white check mark

        if message.content.lower() == '$start': #commence la partie
            new_word()
            tries = 0
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
        
        if message.content.lower() == '$mot': #montre le mot
            await message.channel.send(game_status())

        if "$suggest" in message.content.lower()[:8]: #suggestion
            if message.content.lower()[9:] == "":
                await message.channel.send("Vous n'avez pas donné de suggestions!")
                return
            elif message.content.lower()[9:] in mots_fr:
                await message.channel.send("Ce mot est déjà dans la liste!")
                return
            await bot.get_channel(1090643533922304041).send("**<@&1090635527058898944>\nSUGGESTION DE " + message.author.mention +" aka " + str(message.author) + " dans le channel #"  + str(message.channel) + "**\n\n**LIEN DE LA SUGGESTION**\n" + message.jump_url + "\n\n**MESSAGE**\n" + message.content[9:])
            await message.add_reaction('\U00002705') #white check mark
        
        if message.content.lower() == '$fin': #fini la partie
            await message.channel.send('Le mot etait "' + word.upper() + '".')
            new_word()
            tries = 0
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())

        elif len(message.content) == len(word) and message.content.isalpha(): #verifie que le mot respecte les conditions
            
            correct=0
            for letter in correct_letters: #Si les lettres de guessed_letters peuvent former le mot 
                if letter in guessed_letters:
                    correct+=1
            if correct==len(word):
                await message.channel.send('Bravo, vous avez gagné! Le mot etait bien "' + word.upper() + '" ! :tada:')
                new_word()
                tries = 0
                await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
                return

            if message.content.lower() == str(word): #verifie si l'utilisateur a gagne
                    await message.channel.send('Bravo, vous avez gagné! Le mot etait bien "' + word.upper() + '" ! :tada:')
                    new_word()
                    tries = 0
                    await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
                    return
            elif tries>=6: #verifie si l'utilisateur a perdu
                await message.channel.send('Vous avez perdu! Le mot etait "' + word.upper() + '".')
                new_word()
                tries = 0
                await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
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
        

bot.run(TOKEN) #run bot