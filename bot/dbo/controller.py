import sqlite3
from main import get_bot
conn = sqlite3.connect("botus.db")
c = conn.cursor()
bot=get_bot()

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
    wins = await get_wins(user_id)
    c.execute("UPDATE users SET wins=wins+1 WHERE user_id=?", (user_id,))
    conn.commit()

async def add_lose(user_id):
    loses = await get_loses(user_id)
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
    word_status += ' :regional_indicator_' + word[0].lower() + ': '  # affiche la première lettre du mot
    for pos in range(1,len(word)):
        if word[pos] in await get_guessed_letters(guild_id):
            word_status += ' :regional_indicator_' + word[pos].lower() + ': '
        else:
            word_status += ' :black_large_square: '
    return word_status

async def get_users():
    # récupère l'ID et le pseudonyme des utilisateurs
    c.execute("SELECT user_id FROM users")
    rows = c.fetchall()
    users = []
    for row in rows:
        user_id = row[0]
        user = await bot.fetch_user(user_id)
        users.append((user_id, user.name))
    return users


async def get_servers():
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