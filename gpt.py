import discord
from discord.ext import commands
import random
import string
from mots import mots_fr

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = 'MTA4NjM0NDU3NDY4OTA5NTc0MQ.GOx7nq.7a7JHR_U0oZqUhV1821JzhyspdMBOTjFIN4d1E'


def generate_hidden_word(word_length):
    words = []
    with open("liste_mots.txt", "r", encoding="utf-8") as f:
        for line in f.readlines():
            if len(line.strip()) == word_length:
                words.append(line.strip().upper())
                return random.choice(words)


def motus_check(player_word, hidden_word):
    result = ""
    for i, letter in enumerate(player_word):
        if letter == hidden_word[i]:
            result += f"[{letter}]"
        elif letter in hidden_word:
            result += f"({letter})"
        else:
            result += f"{letter}"
            return result


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.command(name='motus', help='Démarre une partie de Motus avec un mot de la longueur choisie (entre 4 et 10).')
async def motus(ctx, word_length: int = 6):
    if word_length < 4 or word_length > 10:
        await ctx.send("Veuillez choisir un nombre entre 4 et 10.")
        return
    hidden_word = generate_hidden_word(word_length)
    attempts = 0
    await ctx.send(f"Motus commencé! Le mot est de longueur {word_length}. Utilisez la commande `!guess [mot]` pour proposer un mot.")


@bot.command(name='guess', help='Propose un mot pour la partie de Motus en cours.')
async def guess(ctx, player_word: str):
    nonlocal hidden_word, attempts

    player_word = player_word.upper()

    if len(player_word) != word_length:
        await ctx.send(f"Le mot doit avoir {word_length} lettres. Réessayez.")
        return
    if not player_word.isalpha():
        await ctx.send("Votre proposition doit contenir uniquement des lettres. Réessayez.")
        return
    attempts += 1
    result = motus_check(player_word, hidden_word)

    if player_word == hidden_word:
        await ctx.send(f"Bravo! Vous avez trouvé le mot `{hidden_word}` en {attempts} essais!")
        del bot.remove_command("guess")
        return
    else:
        await ctx.send(f"Résultat : {result} - Essayez encore.")

bot.run(TOKEN)
