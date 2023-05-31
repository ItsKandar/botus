import random
import discord
from discord import app_commands
from discord.ext import commands
import requests
from mots.mots import mots_fr
from mots.dico import dico_fr
from controller import *
from create_db import *
from config import *

# Créer ou ouvrir la base de données SQLite
create_db()

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

if DEVMODE:
    TOKEN=DEV_TOKEN
else:
    TOKEN=RE_TOKEN

async def new_word(guild_id):
    word = random.choice(mots_fr)
    await reset_correct_letters(guild_id)
    await reset_guessed_letters(guild_id)
    await resetTries(guild_id)
    await add_mot(guild_id, word)
    await add_partie(guild_id)
    return word

bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

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

@bot.tree.command(name='start', description='Démarre une partie')
async def start(ctx):
    if await is_blacklisted(ctx.user.id) is True:
        await ctx.response.send_message("Vous avez été blacklisté du bot!", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        await new_word(ctx.guild.id)
        await ctx.response.send_message('Nouveau mot (' + str(len(await get_mot(ctx.guild.id))) + ' lettres) : \n' + await game_status(ctx.guild.id))
    else:
        await ctx.response.send_message("Channel incorrect!, le channel defini est <#"+get_channel_id(ctx.guild.id)+">", ephemeral=True)

@bot.tree.command(name='fin', description='Termine une partie')
async def fin(ctx):
    if await is_blacklisted(ctx.user.id) is True:
        await ctx.response.send_message("Vous avez été blacklisté du bot!", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`")
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        mot = str(await get_mot(ctx.guild.id)).upper()
        await new_word(ctx.guild.id)
        await ctx.response.send_message('Le mot etait "' + mot + '".\nNouveau mot (' + str(len(await get_mot(ctx.guild.id))) + ' lettres) : \n' + await game_status(ctx.guild.id))
    else:
        await ctx.response.send_message("Channel incorrect!, le channel defini est <#"+get_channel_id(ctx.guild.id)+">", ephemeral=True)

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

@bot.tree.command(name='bug', description='Signale un bug')
async def bug(ctx, message: str):
    await bot.get_channel(1090643512220983346).send("**<@&1090635527058898944>\nBUG REPORT DE " + str(ctx.user.display_name) + "**\n\n**LIEN DU REPORT**\n" + "a debug" + "\n\n**MESSAGE**\n" + message)
    await ctx.response.send_message('Le bug a été signalé, merci!', ephemeral=True)

@bot.tree.command(name='suggest', description='Suggère un mot ou une nouvelle fonctionnalité')
async def suggest(ctx, message: str):
    if message.lower() in mots_fr:
        await ctx.response.send_message('Le mot "' + message.upper() + '" est déjà dans la liste!', ephemeral=True)
    else:
        await bot.get_channel(1090643533922304041).send("**<@&1090635527058898944>\nSUGGESTION DE " + str(ctx.user.display_name) + "**\n\n**LIEN DE LA SUGGESTION**\n" + "a debug" + "\n\n**MESSAGE**\n" + message)
        await ctx.response.send_message('La suggestion a été envoyée, merci!', ephemeral=True)

@bot.tree.command(name='mot', description='Affiche le mot en cours')
async def mot(ctx):
    if await is_blacklisted(ctx.user.id) is True:
        await ctx.response.send_message("Vous avez été blacklisté du bot!", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) is None:
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
    if await is_blacklisted(ctx.user.id) is True:
        await ctx.response.send_message("Vous avez été blacklisté du bot!", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        if await get_wins(ctx.user.id) is None:
            await ctx.response.send_message('Vous n\'avez pas encore de victoires!')
        else:
            await ctx.response.send_message('Vous avez **' + str(await get_wins(ctx.user.id)) + '** victoires.')
    else:
        await ctx.response.send_message("Channel incorrect!", ephemeral=True)

@bot.tree.command(name='classement', description='Affiche le classement global')
async def classement(ctx):
    if await is_blacklisted(ctx.user.id) is True:
        await ctx.response.send_message("Vous avez été blacklisté du bot!", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) is None:
        await ctx.response.send_message("Veuillez définir un channel avec la commande `set`", ephemeral=True)
    elif await get_channel_id(ctx.guild.id) == ctx.channel.id:
        await ctx.response.send_message('**CLASSEMENT GLOBAL**\n\n' + str(await get_leaderboard(bot)))
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
        embed.add_field(name="Commandes Admins", value="`set` : définir le channel de jeu\n`create` : créer le channel de jeu\n`quoifeur (on/off)` : activer/désactiver le quoifeur", inline=False)

    embed.add_field(name="Commandes de jeu", value="`invite` : envoie le lien d'invitation du bot\n`ping` : renvoie la latence du bot\n`start` : commence une partie\n`fin` : finit une partie\n`mot` : affiche le mot en cours\n`bobo` : botus!\n`stats` : affiche vos statistiques\n`classement` : affiche le classement global\n`support` : affiche le lien du serveur Botus\n`bug` : signaler un bug\n`suggest` : proposer un mot\n`help` : affiche cette liste", inline=False)

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
    # send message to 1092509916238979182
    if error != commands.CommandNotFound:
        await bot.get_channel(1092509916238979182).send(f"Une erreur est survenue : {error} dans le serveur {ctx.guild.name} (id : {ctx.guild.id}) dans le channel #{ctx.channel.name} (id : {ctx.channel.id})")
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
        ping()

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

        if message.content[:12] == '$adblacklist': #blacklist quelqu'un
            user_id = message.mentions[0].id
            if await is_blacklisted(user_id) == False:
                await blacklist(user_id)
                await message.channel.send('Utilisateur blacklisté!')
            elif await is_blacklisted(user_id) is True:
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
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status(guild_id))

        if message.content[:7] == '$adlose': #perd la partie
            guild_id=message.content[8:]
            word = await get_mot(guild_id)
            await message.channel.send('Vous avez perdu! Le mot etait "' + word.upper() + '".')
            await new_word(guild_id)
            await message.channel.send('Nouveau mot (' + str(len(word)) + ' lettres) : \n' + game_status())
        
        if message.content[:8] == '$adreset': #remet le nombre d'essais a 0
            guild_id=message.content[9:]
            await resetTries(guild_id)
            await message.channel.send('Nombre d\'essais remis a 0!')

        if message.content[:11] == '$adviewtries': #montre le nombre d'essais
            guild_id=message.content[12:]
            tries = await get_tries(guild_id)
            await message.channel.send('Nombre d\'essais : ' + str(tries))

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

        if message.content == '$adhelp': #envoie en DM les commandes admins
            await message.author.send(':spy: Commandes secretes :spy:: \n\n$adcountusers : compte le nombre d\'users\n$adcountservers : compte le nombre de serveurs\n$adstats : affiche le nombre de serveurs et d\'utilisateurs\n $adblacklist : Blackliste un utilisateur \n $adunblacklist : Unblackliste un utilisateur \n $adaddwins : Ajoute une victoire a un utilisateur \n $admot : Montre le mot \n $adwin : Gagne la partie \n $adlose : Perd la partie \n $adreset : Remet le nombre d\'essais a 0 \n $adviewtries : Montre le nombre d\'essais \n $adviewguessed : Montre les lettres essayees \n $adresetguessed : Retire les lettres essayees \n $adletters : Montre les lettres correctes \n $adresetletters : Retire les lettres correctes \n $adgetusers : Montre la liste des utilisateurs \n $adgetservers : Montre la liste des serveurs \n $adhelp : Envoie en DM les commandes admins')
            await message.channel.send('Commandes admins secrètes envoyé en mp :ok_hand: :spy:')

    #verifie que le channel est bien botus
    if message.channel.id == await get_channel_id(message.guild.id):
        if message.content.lower() in dico_fr or message.content.lower() in mots_fr:
            
            if message.content[0] == '.':
                return
            
            elif message.content[0].lower() != str(await get_mot(message.guild.id))[0].lower(): #verifie que le mot commence par la bonne lettre
                await message.channel.send('Le mot doit commencer par la lettre "' + str(await get_mot(message.guild.id))[0].upper() + '" !')
            
            elif len(message.content)<len(await get_mot(message.guild.id)):
                await message.channel.send('Le mot est plus long que ça!')
            elif len(message.content)>len(await get_mot(message.guild.id)):
                await message.channel.send('Le mot est plus court que ça!')

            elif len(message.content) == len(await get_mot(message.guild.id)) and message.content.isalpha() and message.content.lower()[0] == str(await get_mot(message.guild.id))[0].lower(): #verifie que le mot respecte les conditions
                status=""
                correct=0

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
                                await message.channel.send('Bravo <@'+ str(message.author.id) +'>, vous avez gagné! Le mot etait bien "' + str(await get_mot(message.guild.id)).upper() + '" ! :tada:')
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
                if await get_tries(message.guild.id)>6:
                    await message.channel.send('Vous avez perdu! Le mot etait "' + str(await get_mot(message.guild.id)).upper() + '".')
                    await add_lose(message.author.id)
                    await new_word(message.guild.id)
                    await resetTries(message.guild.id)
                    await message.channel.send('Nouveau mot (' + str(len(await get_mot(message.guild.id))) + ' lettres) : \n' + await game_status(message.guild.id))
                    return
                else:
                    await message.channel.send(mot_emote + "\n" + status + "\n" + str(await get_tries(message.guild.id))+'/6 essais')
            
        elif message.content.lower()[0] != ".":
            await message.channel.send('Le mot doit etre dans le dictionnaire !')

bot.run(TOKEN) #run bot