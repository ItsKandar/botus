# Il faut que je reorganise ce script (un jour)

import random
import sqlite3
import unicodedata
import discord
from discord import app_commands
from discord.ext import commands
import requests
from mots.mots import mots_fr
from mots.secret import mots_fr as mots_volaille
from mots.dico import dico_fr
from config import DEVMODE, DEV_TOKEN, RE_TOKEN, DEV_ID, BLACKLIST
CHANNEL_NAME = "botus"

def normalize(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )


###### DB #######

############################################J########################
# Crée les tables et les collumns de la db si elles n'existent pas #
####################################################################

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

def create_db():
    # Créer les table "servers" et "users" si elles n'existent pas déjà
    c.execute("CREATE TABLE IF NOT EXISTS servers (server_id INTEGER PRIMARY KEY, prefix TEXT)")
    print(column_exists(c, "servers", "channel_id"))
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, wins INTEGER)")

    # Créer les collumns de "servers" si elles n'existent pas déjà
    if not column_exists(c, "servers", "channel_id"):
        c.execute("ALTER TABLE servers ADD COLUMN channel_id INTEGER")

    if not column_exists(c, "servers", "quoifeur"):
        c.execute("ALTER TABLE servers ADD COLUMN quoifeur INTEGER")

    if not column_exists(c, "servers", "parties"):
        c.execute("ALTER TABLE servers ADD COLUMN parties INTEGER")

    if not column_exists(c, "servers", "mot"):
        c.execute("ALTER TABLE servers ADD COLUMN mot TEXT")

    if not column_exists(c, "servers", "tries"):
        c.execute("ALTER TABLE servers ADD COLUMN tries INTEGER")

    if not column_exists(c, "servers", "guessed_letters"):
        c.execute("ALTER TABLE servers ADD COLUMN guessed_letters TEXT")

    if not column_exists(c, "servers", "correct_letters"):
        c.execute("ALTER TABLE servers ADD COLUMN correct_letters TEXT")

    if not column_exists(c, "servers", "secret"):
        c.execute("ALTER TABLE servers ADD COLUMN secret BIT default 0")

    if not column_exists(c, "servers", "word_length"):
        c.execute("ALTER TABLE servers ADD COLUMN word_length INTEGER DEFAULT 0")

    if not column_exists(c, "servers", "volaille"):
        c.execute("ALTER TABLE servers ADD COLUMN volaille INTEGER DEFAULT 0")

    if not column_exists(c, "servers", "server_wins"):
        c.execute("ALTER TABLE servers ADD COLUMN server_wins INTEGER DEFAULT 0")

    conn.commit()

    # Créer les collums d'users si elles n'existent pas déjà

    if not column_exists(c, "users", "loses"):
        c.execute("ALTER TABLE users ADD COLUMN loses INTEGER")

    c.execute("""CREATE TABLE IF NOT EXISTS user_server_wins (
        user_id INTEGER,
        server_id INTEGER,
        wins INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, server_id)
    )""")

    c.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER PRIMARY KEY)")

    conn.commit()

###### FIN DB #######

create_db()

blacklisted_users = set(BLACKLIST)
blacklisted_users.update(row[0] for row in c.execute("SELECT user_id FROM blacklist").fetchall())

###### FONCTIONS #######

async def resetTries(guild_id):
    c.execute("UPDATE servers SET tries=0 WHERE server_id=?", (guild_id,))
    conn.commit()

async def add_tries(guild_id):
    c.execute("UPDATE servers SET tries=tries+1 WHERE server_id=?", (guild_id,))
    conn.commit()
    
async def get_parties(guild_id):
    c.execute("SELECT parties FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        parties = 0
        c.execute("INSERT INTO servers (server_id, parties) VALUES (?, ?)", (guild_id, parties))
        conn.commit()
    else:
        parties = row[0]
    return parties

async def add_partie(guild_id):
    await get_parties(guild_id)
    c.execute("UPDATE servers SET parties=parties+1 WHERE server_id=?", (guild_id,))
    conn.commit()

async def get_wins(user_id):
    c.execute("SELECT wins FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row is None:
        wins = 0
        c.execute("INSERT INTO users (user_id, wins) VALUES (?, ?)", (user_id, wins))
        conn.commit()
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
    await get_wins(user_id)
    c.execute("UPDATE users SET wins=COALESCE(wins,0)+1 WHERE user_id=?", (user_id,))
    conn.commit()

async def add_lose(user_id):
    await get_loses(user_id)
    c.execute("UPDATE users SET loses=COALESCE(loses,0)+1 WHERE user_id=?", (user_id,))
    conn.commit()

async def add_server_win(guild_id):
    c.execute("UPDATE servers SET server_wins=COALESCE(server_wins,0)+1 WHERE server_id=?", (guild_id,))
    conn.commit()

async def get_server_wins(guild_id):
    c.execute("SELECT server_wins FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    return (row[0] or 0) if row else 0

async def add_user_server_win(user_id, guild_id):
    c.execute("""INSERT INTO user_server_wins (user_id, server_id, wins) VALUES (?, ?, 1)
                 ON CONFLICT(user_id, server_id) DO UPDATE SET wins=wins+1""", (user_id, guild_id))
    conn.commit()

async def get_server_leaderboard(guild_id, bot):
    leaderboard = ""
    c.execute("SELECT user_id, wins FROM user_server_wins WHERE server_id=? AND wins > 0 ORDER BY wins DESC", (guild_id,))
    rows = c.fetchall()
    for i, row in enumerate(rows, 1):
        user = await bot.fetch_user(row[0])
        wins = row[1]
        leaderboard += f"**{i}.** {user.name} : {wins} victoire{'s' if wins > 1 else ''}\n"
    return leaderboard if leaderboard else "Aucune victoire enregistrée sur ce serveur!"

async def get_global_leaderboard(bot):
    leaderboard = ""
    c.execute("SELECT user_id, wins FROM users WHERE wins IS NOT NULL AND wins > 0 ORDER BY wins DESC")
    rows = c.fetchall()
    for i, row in enumerate(rows, 1):
        user = await bot.fetch_user(row[0])
        wins = row[1]
        leaderboard += f"**{i}.** {user.name} : {wins} victoire{'s' if wins > 1 else ''}\n"
    return leaderboard if leaderboard else "Aucune victoire enregistrée pour l'instant!"


async def game_status(guild_id):
    word = str(await get_mot(guild_id))
    word_status = ""
    word_status += '(' + str(len(word)) + ' lettres) : \n'
    word_status += ' :regional_indicator_' + word[0].lower() + ': '  # affiche la première lettre du mot
    for pos in range(1,len(word)):
        if word[pos] in await get_guessed_letters(guild_id):
            word_status += ' :regional_indicator_' + word[pos].lower() + ': '
        else:
            word_status += ' :black_large_square: '
    return word_status

async def get_users(bot):
    # récupère l'ID et le pseudonyme des utilisateurs
    c.execute("SELECT user_id FROM users")
    rows = c.fetchall()
    users = []
    for row in rows:
        user_id = row[0]
        user = await bot.fetch_user(user_id)
        users.append((user_id, user.name))
    return users


async def get_servers(bot):
    # récupère l'ID et le nom des serveurs
    c.execute("SELECT server_id FROM servers")
    rows = c.fetchall()
    servers = []
    for row in rows:
        guild_id = row[0]
        guild = await bot.fetch_guild(guild_id)
        servers.append((guild_id, guild.name))
    return servers

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
async def get_mot(guild_id) -> str:
    c.execute("SELECT mot FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    if row is None:
        mot = await new_word(guild_id)
        c.execute("INSERT INTO servers (server_id, mot) VALUES (?, ?)", (guild_id, mot))
        conn.commit()
    else:
        mot = str(row[0])
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

async def get_secret(guild_id):
    c.execute("SELECT secret FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    return (row[0] or 0) if row else 0

async def set_secret(guild_id, value):
    c.execute("UPDATE servers SET secret=? WHERE server_id=?", (value, guild_id))
    conn.commit()

async def get_volaille(guild_id):
    c.execute("SELECT volaille FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    return (row[0] or 0) if row else 0

async def get_word_length(guild_id):
    c.execute("SELECT word_length FROM servers WHERE server_id=?", (guild_id,))
    row = c.fetchone()
    return (row[0] or 0) if row else 0

###### FIN FONCTIONS #######

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

if DEVMODE:
    TOKEN=DEV_TOKEN
else:
    TOKEN=RE_TOKEN

async def new_word(guild_id, override_length=None):
    volaille = await get_volaille(guild_id)
    length = override_length if override_length is not None else await get_word_length(guild_id)
    word_list = mots_volaille if volaille else mots_fr
    if length > 0:
        filtered = [w for w in word_list if len(normalize(w)) == length]
        word = normalize(random.choice(filtered if filtered else word_list))
    else:
        word = normalize(random.choice(word_list))
    await reset_correct_letters(guild_id)
    await reset_guessed_letters(guild_id)
    await resetTries(guild_id)
    await add_mot(guild_id, word)
    await add_partie(guild_id)
    await set_secret(guild_id, 0)
    return word

bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

@bot.tree.interaction_check
async def global_interaction_check(interaction: discord.Interaction) -> bool:
    if interaction.user.id in blacklisted_users:
        await interaction.response.send_message("Vous êtes banni de Botus.", ephemeral=True)
        return False
    return True

async def get_bot():
    return bot


# Confirme la connexion
@bot.event
async def on_ready():
    print('Logged in as', bot.user)
    await bot.get_channel(1092509916238979182).send("Bot démarré avec succès!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {synced} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    await bot.change_presence(activity=discord.Game(name='Bo bo botus!'))

# Commandes
    
@bot.tree.command(name='invite', description='Envoie le lien d\'invitation du bot')
async def invite(ctx):
    await ctx.response.send_message("Pour inviter Botus, utilisez ce lien: https://discord.com/api/oauth2/authorize?client_id=1086344574689095741&permissions=8&scope=applications.commands%20bot", ephemeral=True)

@bot.tree.command(name='ping', description='Affiche la latence du bot')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.response.send_message(f"Pong! Latence: {latency}ms")

@bot.tree.command(name='start', description='Démarre une partie (optionnel : choisir le nombre de lettres)')
async def start(ctx, nb_lettres: int | None = None):
    if nb_lettres is not None and (nb_lettres < 2 or nb_lettres > 20):
        await ctx.response.send_message("Nombre de lettres invalide! (entre 2 et 20)", ephemeral=True)
        return
    if await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        await new_word(ctx.guild.id, override_length=nb_lettres)
        await ctx.response.send_message('Nouveau mot ' + await game_status(ctx.guild.id))
    else:
        await ctx.response.send_message(f"Channel incorrect!, le channel defini est <#{await get_channel_id(ctx.guild.id)}>", ephemeral=True)

@bot.tree.command(name='fin', description='Termine une partie')
async def fin(ctx):
    if await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`")
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        mot = str(await get_mot(ctx.guild.id)).upper()
        await new_word(ctx.guild.id)
        new_mot = str(await get_mot(ctx.guild.id))
        await ctx.response.send_message('Le mot etait "' + mot + '".\nNouveau mot (' + str(len(new_mot)) + ' lettres) : \n' + await game_status(ctx.guild.id))
    else:
        await ctx.response.send_message(f"Channel incorrect!, le channel defini est <#{await get_channel_id(ctx.guild.id)}>", ephemeral=True)

@bot.tree.command(name='quoifeur', description='Active/Désactive le quoifeur')
@app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.default_permissions(administrator=True)
async def quoifeur(ctx, arg: str):
    valid_args = {'on': 1, 'off': 0}
    if arg not in valid_args:
        await ctx.response.send_message('Argument invalide! (on/off)', ephemeral=True)
        return
    quoifeur = valid_args[arg]
    guild_id = ctx.guild.id
    c.execute("UPDATE servers SET quoifeur=? WHERE server_id=?", (quoifeur, guild_id))
    conn.commit()
    await ctx.response.send_message(f"Quoifeur {'activé' if quoifeur else 'désactivé'}!")

@bot.tree.command(name='longueur', description='Définit la longueur des mots (0 = aléatoire)')
@app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.default_permissions(administrator=True)
async def longueur(ctx, taille: int):
    if taille < 0 or taille > 20:
        await ctx.response.send_message('Taille invalide! (0-20, 0 = aléatoire)', ephemeral=True)
        return
    guild_id = ctx.guild.id
    c.execute("UPDATE servers SET word_length=? WHERE server_id=?", (taille, guild_id))
    conn.commit()
    if taille == 0:
        await ctx.response.send_message("Longueur des mots : aléatoire. Le prochain mot appliquera ce réglage.")
    else:
        await ctx.response.send_message(f"Longueur des mots définie sur **{taille}** lettres. Le prochain mot appliquera ce réglage.")

@bot.tree.command(name='set', description='Définit le channel de jeu')
@app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.default_permissions(administrator=True)
async def set(ctx, channel: discord.TextChannel):
    guild_id = ctx.guild.id
    channel_id = channel.id
    c.execute("UPDATE servers SET channel_id=? WHERE server_id=?", (channel_id, guild_id))
    conn.commit()
    await ctx.response.send_message(f"Channel de jeu mis à jour: {channel}")

@bot.tree.command(name='create', description='Crée le channel de jeu')
@app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.default_permissions(administrator=True)
async def create(ctx):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=CHANNEL_NAME)
    if not existing_channel:
        print(f'Creation du channel {CHANNEL_NAME}')
        await guild.create_text_channel(CHANNEL_NAME)
    else:
        await ctx.response.send_message('Le channel existe déjà!', ephemeral=True)
        
@bot.tree.command(name="setmot", description="Impose le mot à deviner (hors classement)")
@app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.default_permissions(administrator=True)
async def setmot(ctx, mot: str):
    if len(mot) < 2 or len(mot) > 20 or not mot.isalpha():
        await ctx.response.send_message("Mot invalide! Le mot doit avoir entre 2 et 20 lettres (lettres uniquement).", ephemeral=True)
        return
    guild_id = ctx.guild.id
    await add_mot(guild_id, normalize(mot))
    await resetTries(guild_id)
    await reset_guessed_letters(guild_id)
    await set_secret(guild_id, 1)
    await ctx.channel.send(await game_status(guild_id))
    await ctx.response.send_message(f"Le mot a été défini sur '{mot.upper()}' ! (cette partie ne compte pas dans le classement)", ephemeral=True)

@bot.tree.command(name='bug', description='Signale un bug')
async def bug(ctx, message: str):
    await bot.get_channel(1090643512220983346).send("**<@&1090635527058898944>\nBUG REPORT DE " + str(ctx.user.display_name) + "**\n\n**LIEN DU REPORT**\n" + "a debug" + "\n\n**MESSAGE**\n" + message)
    await ctx.response.send_message('Le bug a été signalé, merci!', ephemeral=True)

@bot.tree.command(name='suggest', description='Suggère une nouvelle fonctionnalité')
async def suggest(ctx, message: str):
    await bot.get_channel(1090643533922304041).send("**<@&1090635527058898944>\nSUGGESTION DE " + str(ctx.user.display_name) + " DANS LE SERVEUR **__" + ctx.guild.name + "__\n\n**MESSAGE**\n" + message)
    await ctx.response.send_message('La suggestion a été envoyée, merci!', ephemeral=True)

@bot.tree.command(name='mot', description='Affiche le mot en cours')
async def mot(ctx):
    if await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        status = await game_status(ctx.guild.id)
        await ctx.response.send_message(status)
    else:
        await ctx.response.send_message("Channel incorrect!", ephemeral=True)

@bot.tree.command(name='bobo', description='Botus!')
async def bobo(ctx):
    await ctx.response.send_message('Botus!', ephemeral=True)

@bot.tree.command(name='stats', description='Affiche vos statistiques')
async def stats(ctx):
    if await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        if await get_wins(ctx.user.id) is None:
            await ctx.response.send_message('Vous n\'avez pas encore de victoires!')
        else:
            wins = await get_wins(ctx.user.id) or 0
            loses = await get_loses(ctx.user.id) or 0
            await ctx.response.send_message(f'Vous avez **{wins}** victoire{"s" if wins > 1 else ""} et **{loses}** défaite{"s" if loses > 1 else ""}.')
    else:
        await ctx.response.send_message("Channel incorrect!", ephemeral=True)

@bot.tree.command(name='classement', description='Affiche le classement du serveur')
async def classement(ctx):
    if await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        server_wins = await get_server_wins(ctx.guild.id)
        header = f'**CLASSEMENT DU SERVEUR** — {server_wins} victoire{"s" if server_wins > 1 else ""} au total\n\n'
        await ctx.response.send_message(header + await get_server_leaderboard(ctx.guild.id, bot))
    else:
        await ctx.response.send_message("Channel incorrect!", ephemeral=True)

@bot.tree.command(name='global', description='Affiche le classement global tous serveurs confondus')
async def global_classement(ctx):
    if await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        c.execute("SELECT server_id, server_wins FROM servers WHERE server_wins > 0 ORDER BY server_wins DESC")
        server_rows = c.fetchall()
        servers_section = ""
        for row in server_rows:
            try:
                guild = await bot.fetch_guild(row[0])
                wins = row[1]
                servers_section += f"**{guild.name}** — {wins} victoire{'s' if wins > 1 else ''}\n"
            except Exception:
                pass
        players_section = await get_global_leaderboard(bot)
        msg = "**CLASSEMENT GLOBAL**\n\n"
        if servers_section:
            msg += f"**Serveurs :**\n{servers_section}\n"
        msg += f"**Top joueurs :**\n{players_section}"
        await ctx.response.send_message(msg)
    else:
        await ctx.response.send_message("Channel incorrect!", ephemeral=True)

@bot.tree.command(name='support', description='Envoie le lien du serveur support')
async def support(ctx):
    await ctx.response.send_message('Voici le lien du serveur Botus! : https://discord.gg/4M6596sjZa', ephemeral=True)
    
@bot.tree.command(name='help', description='Affiche la liste des commandes')
async def help(ctx):

    is_admin = ctx.user.guild_permissions.administrator

    embed = discord.Embed(title="Liste des commandes !", color=discord.Color.blue())

    if is_admin:
        embed.add_field(name="Commandes Admins", value="`set` : définir le channel de jeu\n`create` : créer le channel de jeu\n`quoifeur (on/off)` : activer/désactiver le quoifeur\n`longueur <n>` : forcer une longueur de mot (0 = aléatoire)\n`setmot <mot>` : imposer un mot (hors classement)", inline=False)

    embed.add_field(name="Commandes de jeu", value="`invite` : envoie le lien d'invitation du bot\n`ping` : renvoie la latence du bot\n`start` : commence une partie\n`fin` : finit une partie\n`mot` : affiche le mot en cours\n`bobo` : botus!\n`stats` : affiche vos statistiques\n`classement` : classement du serveur\n`global` : classement tous serveurs\n`support` : affiche le lien du serveur Botus\n`bug` : signaler un bug\n`suggest` : proposer un mot\n`help` : affiche cette liste", inline=False)

    await ctx.response.send_message(embed=embed, ephemeral=True)

class MessageConverter(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            message = await commands.MessageConverter().convert(ctx, argument)
        except commands.BadArgument:
            raise commands.BadArgument('Message introuvable.') from None
        else:
            return message

# Envoi un message dans 1093581382581751888 quand le bot rejoint un serveur
@bot.event
async def on_guild_join(guild):
    channel = bot.get_channel(1093581382581751888)
    await channel.send(f"Botus a rejoint le serveur {guild.name} ({guild.id}), contenant {guild.member_count} membres. Lien : https://discord.gg/{guild.invite.code}")

@bot.event
async def on_command_error(ctx, error):
    # send message to 1092509916238979182
    if not isinstance(error, commands.CommandNotFound):
        await bot.get_channel(1092509916238979182).send(f"Une erreur est survenue : {error} dans le serveur {ctx.guild.name} (id : {ctx.guild.id}) dans le channel #{ctx.channel.name} (id : {ctx.channel.id})")
        raise error

# Regarde si la commande existe

@bot.event
async def on_message(message):
    global tries
    global guessed_letters

    #ignore lui meme
    if message.author == bot.user:
        return

    if message.author.id in blacklisted_users:
        return

    if bot.user in message.mentions:
        latency = round(bot.latency * 1000)
        await message.channel.send(f"Pong! Latence: {latency}ms")

    # Faites pas attention
    if await get_quoifeur(message.guild.id) == 1:
        if 'quoi' in message.content.lower() or 'cwa' in message.content.lower() or 'kwa' in message.content.lower() or 'qwa' in message.content.lower() or 'koi' in message.content.lower() or 'koa' in message.content.lower() or 'quouwa' in message.content.lower() or 'quoua' in message.content.lower():
            roll = random.randint(0, 1000)
            if roll <= 69:
                await message.channel.send('COUBAKA :star2:')
            elif 69 < roll <= 300:
                await message.channel.send('COUBEH :star:')
            elif roll > 300:
                await message.channel.send('FEUR')

        if 'ui' in message.content.lower():
            roll = random.randint(0, 10)
            if roll <= 1:
                await message.channel.send('STITI :star2:')
            else:
                await message.channel.send('FI')
        
        if 'ok' in message.content.lower() or 'okay' in message.content.lower():
            roll = random.randint(0, 10)
            await message.channel.send('BOOMER')

        if 'ratio' in message.content.lower():
            await message.add_reaction('👍')

    await bot.process_commands(message)
    if message.author.id in DEV_ID: #admin commands :)

        if message.content == '$adcountusers': #compte le nombre d'utilisateurs
            nb_users = str(c.execute('SELECT COUNT(*) FROM users').fetchone()).replace("(", "").replace(")", "").replace(",", "")
            await message.channel.send(f"Nombre d'utilisateurs : {nb_users}")

        if message.content == '$adcountservers': #compte le nombre de serveurs
            await message.channel.send(f"Nombre de serveurs : {len(bot.guilds)}")

        if message.content == '$adcountgames': #compte le nombre de parties
            await message.channel.send(f"Nombre de parties : {c.execute('SELECT COUNT(*) FROM parties').fetchone()}")

        if message.content == '$advotes': # recupere les votes en appelant https://discordbotlist.com/api/v1/bots/1086344574689095741/upvotes
            await message.channel.send(f"Nombre de votes sur dbl : {len(requests.get('https://discordbotlist.com/api/v1/bots/1086344574689095741/upvotes').json())}")
        
        if message.content == '$adstats': # affiche le nombre de serveurs et d'utilisateurs
            await message.channel.send(f"Nombre de serveurs : {len(bot.guilds)}\nNombre d'utilisateurs : {len(bot.users)}\nNombres de parties totales : {c.execute('SELECT COUNT(*) FROM games').fetchone()[0]}")

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

        if message.content[:6] == '$adsay':
            await message.channel.send(message.content[7:])
            await message.delete()

        if message.content[:9] == '$adstatus':
            await bot.change_presence(activity=discord.Game(name=message.content[10:]))
            await message.channel.send('Status changé!')

        if message.content[:10] == '$adaddwins': #ajoute des victoires
            user_id = message.mentions[0].id
            await add_win(user_id)
            await message.channel.send('1 victoire ajoutée a ' + message.mentions[0].name + '!')
        
        if message.content[:6] == '$admot': #montre le mot
            guild_id = message.content[7:]
            word = await get_mot(guild_id)
            await message.author.send('Le mot est : ' + word.upper() + ' !')
            await message.channel.send('Le mot a été envoyé en DM!')

        if message.content[6:] == '$adwin': #gagne la partie
            guild_id=message.content[7:]
            word= await get_mot(guild_id)
            await message.channel.send('Bravo, vous avez trouvé! Le mot etait bien "' + word.upper() + '" !')
            await new_word(guild_id)
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + await game_status(guild_id))

        if message.content[:7] == '$adlose': #perd la partie
            guild_id=message.content[8:]
            word = await get_mot(guild_id)
            await message.channel.send('Vous avez perdu! Le mot etait "' + word.upper() + '".')
            await new_word(guild_id)
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
        
        if message.content[:8] == '$adreset': #remet le nombre d'essais a 6
            guild_id=message.content[9:]
            await resetTries(guild_id)
            await message.channel.send('Nombre d\'essais remis a 6!')

        if message.content[:11] == '$adviewtries': #montre le nombre d'essais
            guild_id=message.content[12:]
            tries = await get_tries(guild_id)
            await message.channel.send('Nombre d\'essais restants: ' + str(6-await get_tries(guild_id)))

        if message.content[:14]=='$adviewguessed': #montre les lettres essayees
            guild_id=message.content[15:]
            guessed_letters = await get_guessed_letters(guild_id)
            await message.channel.send('Lettres essayees : ' + str(guessed_letters))
        
        if message.content[:14] == '$adresetguessed': #retire les lettres essayees
            guild_id=message.content[15:]
            await reset_guessed_letters(guild_id)
            await message.channel.send('Lettres essayees remises a 0!')
            
        if message.content[:10] == '$adletters': #montre les lettres correctes
            guild_id=message.content[11:]
            message.channel.send (await get_correct_letters(guild_id))

        if message.content[:13] == '$adresetletters':
            guild_id=message.content[14:]
            await reset_correct_letters(guild_id)
            message.channel.send (await get_correct_letters(guild_id))

        if message.content == '$adgetusers':
            await message.channel.send(await get_users(bot))

        if message.content == '$adgetservers':
            await message.channel.send(await get_servers(bot))

        if message.content[:12] == '$adblacklist': #ajoute un user a la blacklist
            user_id = int(message.content[13:])
            blacklisted_users.add(user_id)
            c.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (user_id,))
            conn.commit()
            await message.channel.send(f"Utilisateur {user_id} ajouté à la blacklist.")

        if message.content[:14] == '$adunblacklist': #retire un user de la blacklist
            user_id = int(message.content[15:])
            blacklisted_users.discard(user_id)
            c.execute("DELETE FROM blacklist WHERE user_id=?", (user_id,))
            conn.commit()
            await message.channel.send(f"Utilisateur {user_id} retiré de la blacklist.")

        if message.content[:11] == '$advolaille': #active/desactive le mode volaille sur un serveur
            guild_id = int(message.content[12:])
            current = c.execute("SELECT volaille FROM servers WHERE server_id=?", (guild_id,)).fetchone()
            new_val = 0 if (current and current[0]) else 1
            c.execute("UPDATE servers SET volaille=? WHERE server_id=?", (new_val, guild_id))
            conn.commit()
            await message.channel.send(f"Mode volaille {'activé' if new_val else 'désactivé'} sur le serveur {guild_id}!")

        if message.content == '$adhelp': #envoie en DM les commandes admins
            await message.author.send(':spy: Commandes secretes :spy:: \n\n$adcountusers : compte le nombre d\'users\n$adcountservers : compte le nombre de serveurs\n$adstats : affiche le nombre de serveurs et d\'utilisateurs\n $adaddwins : Ajoute une victoire a un utilisateur \n $admot : Montre le mot \n $adwin : Gagne la partie \n $adlose : Perd la partie \n $adreset : Remet le nombre d\'essais a 6 \n $adviewtries : Montre le nombre d\'essais \n $adviewguessed : Montre les lettres essayees \n $adresetguessed : Retire les lettres essayees \n $adletters : Montre les lettres correctes \n $adresetletters : Retire les lettres correctes \n $adgetusers : Montre la liste des utilisateurs \n $adgetservers : Montre la liste des serveurs \n $adhelp : Envoie en DM les commandes admins')
            await message.channel.send('Commandes admins secrètes envoyé en mp :ok_hand: :spy:')
        
        if message.content == '$adjoinserver': #renvoie le lien du serveur avec l'id specifié
            guild_id = message.content[15:]
            guild = bot.get_guild(int(guild_id))
            invite = await guild.text_channels[0].create_invite(max_age = 300)
            await message.channel.send(f"Lien d'invitation pour le serveur {guild.name} : {invite.url}")

    #verifie que le channel est bien botus
    if message.channel.id == await get_channel_id(message.guild.id):
        norm_content = normalize(message.content)
        if norm_content in dico_fr or norm_content in mots_fr or norm_content in mots_volaille:

            if message.content[0] == '.':
                return

            current_word = str(await get_mot(message.guild.id))
            if len(norm_content) == len(current_word) and norm_content[0] == current_word[0]: #verifie que le mot respecte les conditions
                status=""
                correct=0

                await add_tries(message.guild.id) #ajoute un essai
                mot_emote=""
                for letter in norm_content: #ajoute les lettres dans mot_emote
                    mot_emote+=":regional_indicator_"+letter+": "
                guess = norm_content
                target = normalize(str(await get_correct_letters(message.guild.id)))
                result: list[str | None] = [None] * len(guess)
                target_available = list(target)

                # passe 1 : positions exactes (rouge)
                for i in range(len(guess)):
                    if guess[i] == target_available[i]:
                        result[i] = ':red_square: '
                        target_available[i] = None
                        correct += 1

                if correct == len(target):
                    await message.channel.send('Bravo <@'+ str(message.author.id) +'>, vous avez gagné! Le mot etait bien "' + target.upper() + '" ! :tada:')
                    if not await get_secret(message.guild.id):
                        await add_win(message.author.id)
                        await add_server_win(message.guild.id)
                        await add_user_server_win(message.author.id, message.guild.id)
                    await new_word(message.guild.id)
                    await resetTries(message.guild.id)
                    next_word = await get_mot(message.guild.id)
                    await message.channel.send('Nouveau mot (' + str(len(next_word)) + ' lettres) : \n' + await game_status(message.guild.id))
                    return

                # passe 2 : lettres présentes mais mal placées (jaune), limitées aux occurrences restantes
                for i in range(len(guess)):
                    if result[i] is not None:
                        continue
                    if guess[i] in target_available:
                        result[i] = ':yellow_square: '
                        target_available[target_available.index(guess[i])] = None
                    else:
                        result[i] = ':black_large_square: '

                status = ''.join(r for r in result if r is not None)
                if await get_tries(message.guild.id)>5:
                    await message.channel.send('Vous avez perdu! Le mot etait "' + target.upper() + '".')
                    if not await get_secret(message.guild.id):
                        await add_lose(message.author.id)
                    await new_word(message.guild.id)
                    await resetTries(message.guild.id)
                    next_word = await get_mot(message.guild.id)
                    await message.channel.send('Nouveau mot (' + str(len(next_word)) + ' lettres) : \n' + await game_status(message.guild.id))
                    return
                else:
                    await message.channel.send(mot_emote + "\n" + status + "\n" + str(6-await get_tries(message.guild.id))+'/6 essais restants')

bot.run(TOKEN) #run bot