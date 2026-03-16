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

def get_contexte():
    taches = get_taches(statut="en attente")
    notes = get_notes()
    return f"Taches en attente : {len(taches)} | Notes : {len(notes)}"

def get_system_prompt():
    return f"""Tu es ARIA, assistant personnel intelligent de Fallou, disponible 24h/24 et 7j/7 via Telegram.

RAISONNEMENT EN 5 ETAPES :
1. COMPRENDRE : Analyse l intention et le contexte du message
2. ANALYSER : Identifie l objectif (informer, aider, guider, confirmer)
3. RECHERCHER : Utilise les informations disponibles
4. CONSTRUIRE : Formule une reponse claire et structuree
5. PROPOSER : Suggere toujours une action ou etape suivante

STRUCTURE DE REPONSE :
- Reconnaissance de la demande
- Reponse principale claire et directe
- Information complementaire si utile
- Proposition d action concrete

REGLES DE REDACTION :
- Phrases courtes et directes
- Langage naturel et respectueux
- Emojis pour structurer et rendre lisible
- Jamais de reponses vagues ou inutiles
- Toujours proposer une action concrete
- Si incompris : demande une clarification polie

GESTION DES SITUATIONS :
- Question simple : reponse directe et concise
- Demande d action : guide etape par etape
- Information manquante : explique et demande des details
- Erreur : reconnais et propose une alternative

CAPACITES :
- Repond a toutes les questions en francais
- Gere les taches, notes et rappels
- Planifie et organise le planning
- Fait des resumes et syntheses
- Donne des conseils et recommandations
- Recherche des informations sur internet
- Genere des factures et rapports PDF
- Surveille les prix et actualites

Tu es proactif, utile et toujours oriente vers l action.
Contexte : {get_contexte()}
Date et heure : {datetime.now().strftime('%d/%m/%Y %H:%M')}"""

def recherche_web(query, max_results=3):
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except Exception as e:
        return []

def chat_groq(message, historique=[], modele="groq"):
    messages = [{"role": "system", "content": get_system_prompt()}]
    for h in historique[-8:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})
    response = groq_client.chat.completions.create(
        model=MODELES[modele],
        messages=messages,
        max_tokens=1024
    )
    return response.choices[0].message.content

def chat_avec_recherche(message, historique=[]):
    resultats = recherche_web(message)
    contexte_web = ""
    if resultats:
        contexte_web = "\n\nSources trouvees sur internet :\n"
        for r in resultats:
            contexte_web += f"- {r['title']} : {r['href']}\n"
            if r.get('body'):
                contexte_web += f"  Resume : {r['body'][:200]}\n"
    message_enrichi = message + contexte_web
    return chat_groq(message_enrichi, historique)

def chat(message, historique=[], modele="groq", recherche=True):
    sauvegarder_historique("user", message)
    try:
        if recherche:
            reponse = chat_avec_recherche(message, historique)
        else:
            reponse = chat_groq(message, historique, modele)
    except Exception as e:
        print(f"[IA] Erreur Groq : {e}")
        reponse = f"Erreur IA : {e}"
    sauvegarder_historique("assistant", reponse)
    return reponse

def analyser_intention(message):
    prompt = f"""Analyse ce message et reponds UNIQUEMENT avec un JSON valide :
Message : "{message}"
Format : {{"intention": "chat|tache|note|rappel|planning|resume", "action": "creer|lister|terminer|supprimer|aucune", "donnees": {{}}}}"""
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
    return chat(f"Fais un resume concis en francais : {texte}", modele=modele, recherche=False)

def generer_plan_journee(taches, evenements="", modele="groq"):
    taches_text = "\n".join([f"- {t['titre']} ({t['priorite']})" for t in taches])
    prompt = f"Cree un planning journee optimise. Taches : {taches_text}. Evenements : {evenements}. Date : {datetime.now().strftime('%d/%m/%Y')}"
    return chat(prompt, modele=modele, recherche=False)

def comparer_ia(message):
    resultats = {}
    for modele in ["groq", "groq_fast", "groq_smart"]:
        try:
            resultats[modele] = chat_groq(message, modele=modele)
        except Exception as e:
            resultats[modele] = f"Erreur : {e}"
    return resultats