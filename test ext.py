import discord
from discord.ext import commands
import sqlite3
import random
from mots.mots import mots_fr
from mots.dico import dico_fr
from config import RE_TOKEN, DEV_ID, DEV_TOKEN, DEVMODE

# Créer ou ouvrir la base de données SQLite
conn = sqlite3.connect("botus.db")
c = conn.cursor()

# Fonction qui verifie si une colonne existe dans une table
def column_exists(cursor, table_name, column_name):
    cursor.execute("PRAGMA table_info({})".format(table_name))
    columns = cursor.fetchall()
    for column in columns:
        if column[1] == column_name:
            return True
    return False

# Créer les table "servers" et "users" si elles n'existent pas déjà
c.execute("CREATE TABLE IF NOT EXISTS servers (server_id INTEGER PRIMARY KEY, prefix TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, wins INTEGER)")

# Créer les collumns de "servers" si elles n'existent pas déjà
if not column_exists(c, "servers", "channel_id"):
    c.execute("ALTER TABLE servers ADD COLUMN channel_id INTEGER")

if not column_exists(c, "servers", "quoifeur"):
    c.execute("ALTER TABLE servers ADD COLUMN quoifeur INTEGER")

if not column_exists(c, "servers", "mot"):
    c.execute("ALTER TABLE servers ADD COLUMN mot TEXT")

if not column_exists(c, "servers", "tries"):
    c.execute("ALTER TABLE servers ADD COLUMN tries INTEGER")

if not column_exists(c, "servers", "guessed_letters"):
    c.execute("ALTER TABLE servers ADD COLUMN guessed_letters TEXT")

if not column_exists(c, "servers", "correct_letters"):
    c.execute("ALTER TABLE servers ADD COLUMN correct_letters TEXT")

conn.commit()

# Créer les collums d'users si elles n'existent pas déjà

if not column_exists(c, "users", "loses"):
    c.execute("ALTER TABLE users ADD COLUMN loses INTEGER")

if not column_exists(c, "users", "is_blacklisted"):
    c.execute("ALTER TABLE users ADD COLUMN is_blacklisted INTEGER")

conn.commit()


CHANNEL_NAME = 'botus'
TOKEN=''
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

if DEVMODE:
    TOKEN=DEV_TOKEN
else:
    TOKEN=RE_TOKEN

async def resetTries(guild_id):
    c.execute("UPDATE servers SET tries=0 WHERE server_id=?", (guild_id,))
    conn.commit()

async def add_tries(guild_id):
    c.execute("UPDATE servers SET tries=tries+1 WHERE server_id=?", (guild_id,))
    conn.commit()
    
async def new_word(guild_id):
    word = random.choice(mots_fr)
    await reset_correct_letters(guild_id)
    await reset_guessed_letters(guild_id)
    await resetTries(guild_id)
    await add_mot(guild_id, word)
    return word

async def get_wins(user_id):
    c.execute("SELECT wins FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row is None:
        return 0  # renvoie une valeur par défaut de 0 si aucune ligne ne correspond à l'utilisateur spécifié
    else:
        wins = row[0]
        return wins
    
async def reset_wins(user_id):
    c.execute("UPDATE users SET wins=0 WHERE user_id=?", (user_id,))
    conn.commit()

async def get_loses(user_id):
    c.execute("SELECT loses FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row is None:
        loses = 0
        c.execute("INSERT INTO users (user_id, loses) VALUES (?, ?)", (user_id, loses))
        conn.commit()
    else:
        loses = row[0]
    return loses

async def add_win(user_id):
    wins = await get_wins(user_id)
    if wins is not None:
        c.execute("UPDATE users SET wins=wins+1 WHERE user_id=?", (user_id,))
        conn.commit()
    else:
        try:
            c.execute("INSERT INTO users (user_id, wins) VALUES (?, ?)", (user_id, 1))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

async def add_lose(user_id):
    await get_loses(user_id)
    c.execute("UPDATE users SET loses=loses+1 WHERE user_id=?", (user_id,))
    conn.commit()

async def get_leaderboard():
    leaderboard=""
    c.execute("SELECT user_id, wins FROM users WHERE wins IS NOT NULL ORDER BY wins DESC")
    rows = c.fetchall()
    for row in rows:
        user_id = row[0]
        wins = row[1]
        if wins is not None:
            user = await bot.fetch_user(user_id)
            username = user.name
            tag = user.discriminator
            leaderboard += f"{username}#{tag} : {wins} victoires\n"
    return leaderboard


async def game_status(guild_id):
    word = await get_mot(guild_id)
    word_status = ''
    for letter in word.lower():
        if letter in await get_guessed_letters(guild_id):
            word_status += ' :regional_indicator_' + letter.lower() + ': '
        else:
            word_status += ' :black_large_square: '
    return word_status

async def get_users():
    c.execute("SELECT user_id FROM users")
    rows = c.fetchall()
    return rows

async def get_servers():
    c.execute("SELECT server_id FROM servers")
    rows = c.fetchall()
    return rows

# Récupère le préfixe du serveur
async def get_prefix(guild_id):
    c.execute("SELECT prefix FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        prefix = "$"
        c.execute("INSERT INTO servers (server_id, prefix) VALUES (?, ?)", (guild_id, prefix))
        conn.commit()
    else:
        prefix = row[0]
    return prefix

# Recupère le channel_id du serveur
async def get_channel_id(guild_id):
    c.execute("SELECT channel_id FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        channel_id = None
        c.execute("INSERT INTO servers (server_id, channel_id) VALUES (?, ?)", (guild_id, channel_id))
        conn.commit()
    else:
        channel_id = row[0]
    return channel_id

# Recuperer le mot du serveur
async def get_mot(guild_id):
    c.execute("SELECT mot FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        mot = new_word(guild_id)
        c.execute("INSERT INTO servers (server_id, mot) VALUES (?, ?)", (guild_id, mot))
        conn.commit()
    else:
        mot = row[0]
    return mot

async def add_mot(guild_id, mot):
    c.execute("UPDATE servers SET mot=? WHERE server_id=?", (mot, guild_id))
    c.execute("UPDATE servers SET correct_letters=? WHERE server_id=?", (mot, guild_id))
    conn.commit()

# Recupere les lettres correctes
async def get_correct_letters(guild_id):
    c.execute("SELECT correct_letters FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        correct_letters = ""
        c.execute("INSERT INTO servers (server_id, correct_letters) VALUES (?, ?)", (guild_id, correct_letters))
        conn.commit()
    else:
        correct_letters = row[0]
    return correct_letters

async def reset_correct_letters(guild_id):
    c.execute("UPDATE servers SET correct_letters=? WHERE server_id=?", ("", guild_id))
    conn.commit()

# Recuperer les lettres déjà essayées
async def get_guessed_letters(guild_id):
    c.execute("SELECT guessed_letters FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        guessed_letters = ""
        c.execute("INSERT INTO servers (server_id, guessed_letters) VALUES (?, ?)", (guild_id, guessed_letters))
        conn.commit()
    else:
        guessed_letters = row[0]
    return guessed_letters

async def add_guessed_letters(guild_id, letter):
    c.execute("UPDATE servers SET guessed_letters=? WHERE server_id=?", (letter, guild_id))
    conn.commit()

async def reset_guessed_letters(guild_id):
    c.execute("UPDATE servers SET guessed_letters=? WHERE server_id=?", ("", guild_id))
    conn.commit()

# Recupere le nombre de tries
async def get_tries(guild_id):
    c.execute("SELECT tries FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        tries = 0
        c.execute("INSERT INTO servers (server_id, tries) VALUES (?, ?)", (guild_id, tries))
        conn.commit()
    else:
        tries = row[0]
    return tries

# Recupère l'option quoifeur du serveur
async def get_quoifeur(guild_id):
    c.execute("SELECT quoifeur FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        quoifeur = 0
        c.execute("INSERT INTO servers (server_id, quoifeur) VALUES (?, ?)", (guild_id, quoifeur))
        conn.commit()
    else:
        quoifeur = row[0]
    return quoifeur

# Verifie si l'user est blacklisté ou non
async def is_blacklisted(user_id):
    c.execute("SELECT is_blacklisted FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row is None:
        is_blacklisted = 0
        c.execute("INSERT INTO users (user_id, is_blacklisted) VALUES (?, ?)", (user_id, is_blacklisted))
        conn.commit()
    else:
        is_blacklisted = row[0]
    return is_blacklisted

async def blacklist(user_id):
    c.execute("UPDATE users SET is_blacklisted=1 WHERE user_id=?", (user_id,))
    conn.commit()

async def unblacklist(user_id):
    c.execute("UPDATE users SET is_blacklisted=0 WHERE user_id=?", (user_id,))
    conn.commit()

bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

# Confirme la connexion
@bot.event
async def on_ready():
    print('Logged in as', bot.user)
    await bot.get_channel(1092509916238979182).send("Bot démarré avec succès!")
    await bot.change_presence(activity=discord.Game(name='Bo bo botus!'))

# Detecte les messages
@bot.command()
async def set_prefix(ctx, prefix: str):
    guild_id = ctx.guild.id
    c.execute("UPDATE servers SET prefix=? WHERE server_id=?", (prefix, guild_id))
    conn.commit()
    await ctx.send(f"Préfixe mis à jour: {prefix}")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latence: {latency}ms")

@bot.command()
async def start(ctx):
    if await get_channel_id(ctx.guild.id) is None:
        await ctx.channel.send("Veuillez définir un channel avec la commande `set`")
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        await new_word(ctx.guild.id)
        await ctx.channel.send('Nouveau mot (' + str(len(await get_mot(ctx.guild.id))) + ' lettres) : \n' + await game_status(ctx.guild.id))
    else:
        await ctx.channel.send('ERREUR')
        
@bot.command()
async def fin(ctx):
    if await get_channel_id(ctx.guild.id) is None:
        await ctx.channel.send("Veuillez définir un channel avec la commande `set`")
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        await ctx.channel.send('Le mot etait "' + str(await get_mot(ctx.guild.id)).upper() + '".')
        await new_word(ctx.guild.id)
        await ctx.channel.send('Nouveau mot (' + str(len(await get_mot(ctx.guild.id))) + ' lettres) : \n' + await game_status(ctx.guild.id))

@bot.command()
@commands.has_permissions(administrator=True)
async def quoifeur(ctx, arg):
    if arg=='on':
        quoifeur = 1
        guild_id = ctx.guild.id
        c.execute("UPDATE servers SET quoifeur=? WHERE server_id=?", (quoifeur, guild_id))
        conn.commit()
        await ctx.channel.send('Quoifeur activé!')
    elif arg=='off':
        quoifeur = 0
        guild_id = ctx.guild.id
        c.execute("UPDATE servers SET quoifeur=? WHERE server_id=?", (quoifeur, guild_id))
        conn.commit()
        await ctx.channel.send('Quoifeur désactivé!')
    else:
        await ctx.channel.send('Argument invalide! (on/off)')

@bot.command()
@commands.has_permissions(administrator=True)
async def set(ctx, channel: discord.TextChannel):
    guild_id = ctx.guild.id
    channel_id = channel.id
    c.execute("UPDATE servers SET channel_id=? WHERE server_id=?", (channel_id, guild_id))
    conn.commit()
    await ctx.send(f"Channel de jeu mis à jour: {channel}")

@bot.command()
@commands.has_permissions(administrator=True)
async def create(ctx):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=CHANNEL_NAME)
    if not existing_channel:
        print(f'Creation du channel {CHANNEL_NAME}')
        await guild.create_text_channel(CHANNEL_NAME)

@bot.command()
async def bug(ctx, *, arg):
    await bot.get_channel(1090643512220983346).send("**<@&1090635527058898944>\nBUG REPORT DE " + str(ctx.message.author.display_name) + "**\n\n**LIEN DU REPORT**\n" + ctx.message.jump_url + "\n\n**MESSAGE**\n" + arg)
    await ctx.channel.send('Le bug a été signalé, merci!')

@bot.command()
async def suggest(ctx, *, arg):
    if arg.lower() in mots_fr:
        await ctx.channel.send('Le mot "' + arg.upper() + '" est déjà dans la liste!')
    else:
        await bot.get_channel(1090643533922304041).send("**<@&1090635527058898944>\nSUGGESTION DE " + str(ctx.message.author.display_name) + "**\n\n**LIEN DE LA SUGGESTION**\n" + ctx.message.jump_url + "\n\n**MESSAGE**\n" + arg)
        await ctx.channel.send('La suggestion a été envoyée, merci!')

@bot.command()
async def mot(ctx):
    status = await game_status(ctx.guild.id)
    await ctx.channel.send(status)

@bot.command()
async def bobo(ctx):
    await ctx.channel.send('Botus!')

@bot.command()
async def stats(ctx):
    if await get_wins(ctx.author.id) is None:
        await ctx.channel.send('Vous n\'avez pas encore de victoires!')
    else:
        await ctx.channel.send('Vous avez **' + str(await get_wins(ctx.author.id)) + '** victoires.')

@bot.command()
async def classement(ctx):
    await ctx.channel.send('**CLASSEMENT GLOBAL**\n\n' + str(await get_leaderboard()))

@bot.command()
async def server(ctx):
    await ctx.channel.send('Voici le lien du serveur Botus! : https://discord.gg/4M6596sjZa')
    
class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        ctx = self.context
        is_admin = ctx.author.guild_permissions.administrator

        embed = discord.Embed(title="Liste des commandes !", color=discord.Color.blue())

        if is_admin:
            embed.add_field(name="Commandes Admins", value="`set` : définir le channel de jeu\n`create` : créer le channel de jeu\n`quoifeur (on/off)` : activer/désactiver le quoifeur\n`prefix` : définir le préfixe du bot", inline=False)

        embed.add_field(name="Commandes de jeu", value="`start` : commence une partie\n`fin` : finit une partie\n`mot` : affiche le mot en cours\n`bobo` : botus!\n`stats` : affiche vos statistiques\n`classement` : affiche le classement global\n`server` : affiche le lien du serveur Botus\n`bug` : signaler un bug\n`suggest` : proposer un mot\n`help` : affiche cette liste", inline=False)

        await ctx.send(embed=embed)

bot.help_command = CustomHelpCommand()

class MessageConverter(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            message = await commands.MessageConverter().convert(ctx, argument)
        except commands.BadArgument:
            raise commands.BadArgument('Message introuvable.') from None
        else:
            return message


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
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas les permissions nécessaires pour effectuer cette commande")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Vous n'avez pas spécifié assez d'arguments")
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Commande inconnue")
    else:
        raise error

# Regarde si la commande existe

@bot.event
async def on_message(message):
    global tries
    global guessed_letters

    #ignore lui meme ou utilisateur blacklisté
    if message.author == bot.user or await is_blacklisted(message.author.id):
        return

    if bot.user in message.mentions:
        prefix = await get_prefix(message.guild.id)
        if prefix==None:
            prefix = "$"
        await message.channel.send(f"Le préfixe actuel pour ce serveur est : `{prefix}`")

    # Faites pas attention
    if await get_quoifeur(message.guild.id) == 1:
        if 'quoi' in message.content.lower() or 'cwa' in message.content.lower() or 'kwa' in message.content.lower() or 'qwa' in message.content.lower() or 'koi' in message.content.lower() or 'koa' in message.content.lower():
            roll = random.randint(0, 10)
            if roll <= 0.69:
                await message.channel.send('COUBAKA :star2:')
            elif 0.69 > roll <= 3:
                await message.send ('COUBEH :star:')
            elif roll > 3:
                await message.channel.send('FEUR')

        if 'ui' in message.content.lower():
            roll = random.randint(0, 10)
            if roll <= 1:
                await message.channel.send('STITI :star2:')
            else:
                await message.channel.send('FI')


    if message.author.id in DEV_ID: #admin commands :)

        await bot.process_commands(message)

        if message.content == '$adcreate': #crée un channel #botus si il n'yen a pas encore
            guild_id = message.guild.id
            channel_id = await get_channel_id(guild_id)
            if channel_id is None:
                await message.channel.send('Création du channel en cours...')
                channel = await message.guild.create_text_channel(CHANNEL_NAME)
                await channel.send('Channel créé!')
                c.execute("INSERT INTO servers VALUES (?, ?)", (guild_id, channel.id))
                conn.commit()
            else:
                await message.channel.send('Le channel existe déjà!')

        if message.content == '$adset': #set le channel #botus
            guild_id = message.guild.id
            channel_id = message.channel.id
            c.execute("UPDATE servers SET channel_id=? WHERE server_id=?", (channel_id, guild_id))
            conn.commit()
            await message.channel.send('Channel défini!')

        if message.content == '$adrestart': #restart bot
            await message.channel.send('Redemarrage en cours...')
            await bot.close()
            await bot.start(TOKEN)

        if message.content == '$adstop':
            await message.channel.send('Arret en cours...')
            await bot.close()

        if message.content == "$adgetchannelid":
            await message.channel.send(await get_channel_id(message.guild.id))
        
        if message.content == '$adquoifeur on':
            quoifeur = 1
            guild_id = message.guild.id
            c.execute("UPDATE servers SET quoifeur=? WHERE server_id=?", (quoifeur, guild_id))
            conn.commit()
            await message.channel.send('Quoifeur activé!')

        if message.content == '$adquoifeur off':
            quoifeur = 0
            guild_id = message.guild.id
            c.execute("UPDATE servers SET quoifeur=? WHERE server_id=?", (quoifeur, guild_id))
            conn.commit()
            await message.channel.send('Quoifeur désactivé!')

        if '$adsay' in message.content:
            await message.channel.send(message.content[7:])
            await message.delete()

        if '$adstatus' in message.content:
            await bot.change_presence(activity=discord.Game(name=message.content[9:]))
            await message.channel.send('Status changé!')

        if message.content[:12] == '$adblacklist': #blacklist quelqu'un
            user_id = message.mentions[0].id
            if await is_blacklisted(user_id) == False:
                await blacklist(user_id)
                await message.channel.send('Utilisateur blacklisté!')
            elif await is_blacklisted(user_id) == True:
                await message.channel.send('Cet utilisateur est déjà blacklisté!')
            else:
                await message.channel.send('Une erreur est survenue!')
        
        if message.content[:14] == '$adunblacklist': #unblacklist quelqu'un
            user_id = message.mentions[0].id
            if await is_blacklisted(user_id) == True:
                await unblacklist(user_id)
            elif await is_blacklisted(user_id) == False:
                await message.channel.send('Cet utilisateur n\'est pas blacklisté!')
            else:
                await message.channel.send('Une erreur est survenue!')

        if '$adaddwins' in message.content:
            user_id = message.mentions[0].id
            await add_win(user_id)
            await message.channel.send('1 victoire ajoutée a ' + message.mentions[0].name + '!')
        
        if message.content == '$admot': #montre le mot
            guild_id = message.content[7:]
            word = await get_mot(guild_id)
            await message.author.send('Le mot est : ' + word.upper() + ' !')
            await message.channel.send('Le mot a été envoyé en DM!')

        if message.content == '$adwin': #gagne la partie
            guild_id=message.content[7:]
            word= await get_mot(guild_id)
            await message.channel.send('Bravo, vous avez trouvé! Le mot etait bien "' + word.upper() + '" !')
            await new_word(guild_id)
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status(guild_id))

        if message.content == '$adlose': #perd la partie
            guild_id=message.content[8:]
            word = await get_mot(guild_id)
            await message.channel.send('Vous avez perdu! Le mot etait "' + word.upper() + '".')
            await new_word(guild_id)
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
        
        if message.content == '$adreset': #remet le nombre d'essais a 0
            guild_id=message.content[9:]
            await resetTries(guild_id)
            await message.channel.send('Nombre d\'essais remis a 0!')

        if message.content == '$adviewtries': #montre le nombre d'essais
            guild_id=message.content[12:]
            tries = await get_tries(guild_id)
            await message.channel.send('Nombre d\'essais : ' + str(tries))

        if message.content=='$adviewguessed': #montre les lettres essayees
            guild_id=message.content[15:]
            guessed_letters = await get_guessed_letters(guild_id)
            await message.channel.send('Lettres essayees : ' + str(guessed_letters))
        
        if message.content == '$adresetguessed': #retire les lettres essayees
            guessed_letters = []
            await message.channel.send('Lettres essayees retirees!')
            
        if message.content == '$adletters': #montre les lettres correctes
            guild_id=message.content[11:]
            message.channel.send (await get_correct_letters(guild_id))

        if message.content == '$adresetletters':
            guild_id=message.content[14:]
            await reset_correct_letters(guild_id)
            message.channel.send (await get_correct_letters(guild_id))

        if message.content == '$adgetusers':
            await message.channel.send(await get_users())

        if message.content == '$adgetservers':
            await message.channel.send(await get_servers())

        if message.content == '$adhelp': #envoie en DM les commandes admins
            await message.author.send(':spy: Commandes secretes :spy:: \n\n $adblacklist : Blackliste un utilisateur \n $adunblacklist : Unblackliste un utilisateur \n $adaddwins : Ajoute une victoire a un utilisateur \n $admot : Montre le mot \n $adwin : Gagne la partie \n $adlose : Perd la partie \n $adreset : Remet le nombre d\'essais a 0 \n $adviewtries : Montre le nombre d\'essais \n $adviewguessed : Montre les lettres essayees \n $adresetguessed : Retire les lettres essayees \n $adletters : Montre les lettres correctes \n $adresetletters : Retire les lettres correctes \n $adgetusers : Montre la liste des utilisateurs \n $adgetservers : Montre la liste des serveurs \n $adhelp : Envoie en DM les commandes admins')
            await message.channel.send('Commandes admins secrètes envoyé en mp :ok_hand: :spy:')

    #verifie que le channel est bien botus
    if message.channel.id == await get_channel_id(message.guild.id) and message.content.lower() in dico_fr:

        if len(message.content) == len(await get_mot(message.guild.id)) and message.content.isalpha(): #verifie que le mot respecte les conditions
            status=""
            correct=0
            
            if await get_tries(message.guild.id)>=6: #verifie si l'utilisateur a perdu
                await message.channel.send('Vous avez perdu! Le mot etait "' + str(await get_mot(message.guild.id)).upper() + '".')
                await add_lose(message.author.id)
                await new_word(message.guild.id)
                await resetTries(message.guild.id)
                await message.channel.send('Nouveau mot (' + str(len(await get_mot(message.guild.id))) + ' lettres) : \n' + await game_status(message.guild.id))
                return
            
            else:
                await add_tries(message.guild.id) #ajoute un essai
                mot_emote=""
                for letter in message.content: #ajoute les lettres dans mot_emote
                    mot_emote+=":regional_indicator_"+letter.lower()+": "
                for letter_pos in range(len(message.content)): #verifie que chaque lettre est correcte
                    if message.content[letter_pos].lower() in str(await get_correct_letters(message.guild.id)).lower():
                        if message.content[letter_pos].lower() == str(await get_correct_letters(message.guild.id))[letter_pos].lower():
                            # ajoute un carré rouge a status
                            status+=":red_square: "
                            correct+=1
                            if correct==len(await get_mot(message.guild.id)):
                                await message.channel.send('Bravo, vous avez gagné! Le mot etait bien "' + str(await get_mot(message.guild.id)).upper() + '" ! :tada:')
                                await add_win(message.author.id)
                                await new_word(message.guild.id)
                                await resetTries(message.guild.id)
                                await message.channel.send('Nouveau mot (' + str(len(await get_mot(message.guild.id))) + ' lettres) : \n' + await game_status(message.guild.id))
                                return
                        else:
                            # ajoute un carré jaune
                            status+=":yellow_square: "
                    else:
                        # ajoute un carré noir
                        status+=":black_large_square: "
                await message.channel.send(mot_emote + "\n" + status + "\n" + str(await get_tries(message.guild.id))+'/6 essais')

            # else:
            #     await add_tries(message.guild.id) #ajoute un essai
            #     for letter in message.content.lower():
            #         if letter in await get_correct_letters(message.guild.id): #verifie que la lettre est dans le mot
            #             if letter in await get_guessed_letters(message.guild.id): #verifie que la lettre n'a pas deja ete essayee
            #                 pass
            #             else: #si la lettre est correcte et n'a pas deja ete essayee
            #                 await add_guessed_letters(message.guild.id, letter)
            #         else:
            #             if letter in await get_guessed_letters(message.guild.id): 
            #                 pass
            #             else: #si la lettre est incorrecte et n'a pas deja ete essayee
            #                 await add_guessed_letters(message.guild.id, letter)
            #     else:
            #         await message.channel.send(game_status(message.guild.id)+ '\n\n' + str(await get_tries)+ '/6 essais.\n' + 'Lettres essayées : ' + str(await get_guessed_letters(message.guild.id)).upper() + '.')
        

bot.run(TOKEN) #run bot