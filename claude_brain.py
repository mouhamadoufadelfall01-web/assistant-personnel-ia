# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from groq import Groq
from database import (get_taches, get_notes, get_historique,
                      sauvegarder_historique, ajouter_tache,
                      ajouter_note, ajouter_rappel)
from datetime import datetime

load_dotenv(dotenv_path=r'C:\Users\fallm\PycharmProjects\telegram\.env')

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODELES = {
    "groq": "llama-3.3-70b-versatile",
    "groq_fast": "llama-3.1-8b-instant",
    "groq_smart": "llama-3.1-70b-versatile"
}

SYSTEM_PROMPT = """Tu es l'assistant personnel intelligent de Fallou.
Tu es disponible 24/7 via Telegram.
Tu peux :
- Repondre a toutes les questions en francais
- Gerer les taches, notes et rappels
- Planifier et organiser le planning
- Faire des resumes et syntheses
- Donner des conseils et recommandations
- Aider avec la redaction de documents

Tu reponds toujours en francais, de maniere concise et utile.
Tu utilises des emojis pour rendre les reponses plus lisibles.
Tu es proactif et suggeres des actions utiles.

Contexte actuel : {contexte}
Date/Heure : {datetime}
"""

def get_contexte():
    taches = get_taches(statut="en attente")
    notes = get_notes()
    return f"""
Taches en attente : {len(taches)}
{chr(10).join([f"- {t['titre']} ({t['priorite']})" for t in taches[:3]])}
Notes recentes : {len(notes)}
"""

def chat_groq(message, historique=[], modele="groq"):
    contexte = get_contexte()
    system = SYSTEM_PROMPT.format(
        contexte=contexte,
        datetime=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    messages = [{"role": "system", "content": system}]
    for h in historique[-8:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    response = groq_client.chat.completions.create(
        model=MODELES[modele],
        messages=messages,
        max_tokens=1024
    )
    return response.choices[0].message.content

def chat(message, historique=[], modele="groq"):
    sauvegarder_historique("user", message)
    try:
        reponse = chat_groq(message, historique, modele)
    except Exception as e:
        print(f"[IA] Erreur Groq : {e}")
        reponse = f"Erreur IA : {e}"
    sauvegarder_historique("assistant", reponse)
    return reponse

def analyser_intention(message):
    prompt = f"""Analyse ce message et reponds UNIQUEMENT avec un JSON :
Message : "{message}"
Format JSON :
{{
  "intention": "chat|tache|note|rappel|planning|resume",
  "action": "creer|lister|terminer|supprimer|aucune",
  "donnees": {{}}
}}"""
    response = groq_client.chat.completions.create(
        model=MODELES["groq_fast"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    import json
    try:
        text = response.choices[0].message.content
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except:
        return {"intention": "chat", "action": "aucune", "donnees": {}}

def generer_resume(texte, modele="groq"):
    prompt = f"Fais un resume concis en francais de ce texte :\n{texte}"
    return chat(prompt, modele=modele)

def generer_plan_journee(taches, evenements="", modele="groq"):
    taches_text = "\n".join([f"- {t['titre']} ({t['priorite']})" for t in taches])
    prompt = f"""Cree un plan de journee optimise en francais :
Taches : {taches_text}
Evenements : {evenements}
Date : {datetime.now().strftime('%d/%m/%Y')}
Propose un planning heure par heure."""
    return chat(prompt, modele=modele)

def comparer_ia(message):
    resultats = {}
    for modele in ["groq", "groq_fast", "groq_smart"]:
        try:
            resultats[modele] = chat_groq(message, modele=modele)
        except Exception as e:
            resultats[modele] = f"Erreur : {e}"
    return resultats
