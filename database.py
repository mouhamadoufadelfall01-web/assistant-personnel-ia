import sqlite3
import os
from datetime import datetime

DB_PATH = "data/assistant.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def creer_base():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS taches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        description TEXT,
        statut TEXT DEFAULT 'en attente',
        priorite TEXT DEFAULT 'normale',
        date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
        date_echeance TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT,
        contenu TEXT NOT NULL,
        categorie TEXT DEFAULT 'general',
        date_creation TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS rappels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        date_heure TEXT NOT NULL,
        statut TEXT DEFAULT 'actif'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS historique (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        contenu TEXT NOT NULL,
        date_creation TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()
    print("[DB] Base creee !")

# ─── TACHES ───
def ajouter_tache(titre, description="", priorite="normale", date_echeance=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO taches (titre, description, priorite, date_echeance) VALUES (?,?,?,?)",
              (titre, description, priorite, date_echeance))
    conn.commit()
    conn.close()

def get_taches(statut=None):
    conn = get_conn()
    c = conn.cursor()
    if statut:
        c.execute("SELECT id, titre, description, statut, priorite, date_echeance FROM taches WHERE statut=?", (statut,))
    else:
        c.execute("SELECT id, titre, description, statut, priorite, date_echeance FROM taches")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "titre": r[1], "description": r[2],
             "statut": r[3], "priorite": r[4], "date_echeance": r[5]} for r in rows]

def terminer_tache(tache_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE taches SET statut='termine' WHERE id=?", (tache_id,))
    conn.commit()
    conn.close()

def supprimer_tache(tache_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM taches WHERE id=?", (tache_id,))
    conn.commit()
    conn.close()

# ─── NOTES ───
def ajouter_note(contenu, titre="", categorie="general"):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO notes (titre, contenu, categorie) VALUES (?,?,?)",
              (titre, contenu, categorie))
    conn.commit()
    conn.close()

def get_notes(categorie=None):
    conn = get_conn()
    c = conn.cursor()
    if categorie:
        c.execute("SELECT id, titre, contenu, categorie, date_creation FROM notes WHERE categorie=?", (categorie,))
    else:
        c.execute("SELECT id, titre, contenu, categorie, date_creation FROM notes ORDER BY date_creation DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "titre": r[1], "contenu": r[2],
             "categorie": r[3], "date": r[4]} for r in rows]

def supprimer_note(note_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()

# ─── RAPPELS ───
def ajouter_rappel(message, date_heure):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO rappels (message, date_heure) VALUES (?,?)",
              (message, date_heure))
    conn.commit()
    conn.close()

def get_rappels_actifs():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, message, date_heure FROM rappels WHERE statut='actif'")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "message": r[1], "date_heure": r[2]} for r in rows]

def marquer_rappel_envoye(rappel_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE rappels SET statut='envoye' WHERE id=?", (rappel_id,))
    conn.commit()
    conn.close()

# ─── HISTORIQUE ───
def sauvegarder_historique(role, contenu):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO historique (role, contenu) VALUES (?,?)", (role, contenu))
    conn.commit()
    conn.close()

def get_historique(limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT role, contenu FROM historique ORDER BY date_creation DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

creer_base()
