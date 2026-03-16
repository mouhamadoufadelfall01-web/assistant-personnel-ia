import anthropic
import openai
from google import genai
import os
from dotenv import load_dotenv
from database import (get_taches, get_notes, get_historique,
                      sauvegarder_historique, ajouter_tache,
                      ajouter_note, ajouter_rappel)
from datetime import datetime

load_dotenv(dotenv_path=r'C:\Users\fallm\PycharmProjects\telegram\.env')

# --- CLIENTS ---
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELES = {
    "claude": "claude-sonnet-4-20250514",
    "chatgpt": "gpt-3.5-turbo",
    "gemini": "gemini-1.5-flash"
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
- Analyser des situations et proposer des solutions

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

# --- CLAUDE ---
def chat_claude(message, historique=[]):
    contexte = get_contexte()
    system = SYSTEM_PROMPT.format(
        contexte=contexte,
        datetime=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    messages = []
    for h in historique[-8:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})
    response = claude_client.messages.create(
        model=MODELES["claude"],
        max_tokens=1024,
        system=system,
        messages=messages
    )
    return response.content[0].text

# --- CHATGPT ---
def chat_gpt(message, historique=[]):
    contexte = get_contexte()
    system = SYSTEM_PROMPT.format(
        contexte=contexte,
        datetime=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    messages = [{"role": "system", "content": system}]
    for h in historique[-8:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})
    response = openai.chat.completions.create(
        model=MODELES["chatgpt"],
        messages=messages,
        max_tokens=1024
    )
    return response.choices[0].message.content

# --- GEMINI ---
def chat_gemini(message, historique=[]):
    contexte = get_contexte()
    system = SYSTEM_PROMPT.format(
        contexte=contexte,
        datetime=datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    prompt = f"{system}\n\nMessage : {message}"
    response = gemini_client.models.generate_content(
        model=MODELES["gemini"],
        contents=prompt
    )
    return response.text

# --- CHAT PRINCIPAL ---
def chat(message, historique=[], modele="claude"):
    sauvegarder_historique("user", message)
    try:
        if modele == "claude":
            reponse = chat_claude(message, historique)
        elif modele == "chatgpt":
            reponse = chat_gpt(message, historique)
        elif modele == "gemini":
            reponse = chat_gemini(message, historique)
        else:
            reponse = chat_claude(message, historique)
    except Exception as e:
        print(f"[IA] Erreur {modele} : {e}")
        try:
            print(f"[IA] Fallback vers Claude...")
            reponse = chat_claude(message, historique)
        except Exception as e2:
            reponse = f"? Erreur IA : {e2}"
    sauvegarder_historique("assistant", reponse)
    return reponse

# --- ANALYSE INTENTION ---
def analyser_intention(message):
    prompt = f"""Analyse ce message et reponds UNIQUEMENT avec un JSON :
Message : "{message}"
Format JSON :
{{
  "intention": "chat|tache|note|rappel|planning|resume",
  "action": "creer|lister|terminer|supprimer|aucune",
  "donnees": {{}}
}}"""
    response = claude_client.messages.create(
        model=MODELES["claude"],
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    try:
        text = response.content[0].text
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except:
        return {"intention": "chat", "action": "aucune", "donnees": {}}

# --- RESUME ---
def generer_resume(texte, modele="claude"):
    prompt = f"Fais un resume concis en francais de ce texte :\n{texte}"
    return chat(prompt, modele=modele)

# --- PLANNING ---
def generer_plan_journee(taches, evenements="", modele="claude"):
    taches_text = "\n".join([f"- {t['titre']} ({t['priorite']})" for t in taches])
    prompt = f"""Cree un plan de journee optimise en francais :
Taches : {taches_text}
Evenements : {evenements}
Date : {datetime.now().strftime('%d/%m/%Y')}
Propose un planning heure par heure avec des conseils de productivite."""
    return chat(prompt, modele=modele)

# --- COMPARER LES 3 IA ---
def comparer_ia(message):
    resultats = {}
    for modele in ["claude", "chatgpt", "gemini"]:
        try:
            resultats[modele] = chat(message, modele=modele)
        except Exception as e:
            resultats[modele] = f"Erreur : {e}"
    return resultats
