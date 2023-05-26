####################################################################
# Crée les tables et les collumns de la db si elles n'existent pas #
####################################################################

import sqlite3
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

    conn.commit()

    # Créer les collums d'users si elles n'existent pas déjà

    if not column_exists(c, "users", "loses"):
        c.execute("ALTER TABLE users ADD COLUMN loses INTEGER")

    if not column_exists(c, "users", "is_blacklisted"):
        c.execute("ALTER TABLE users ADD COLUMN is_blacklisted INTEGER")

    conn.commit()