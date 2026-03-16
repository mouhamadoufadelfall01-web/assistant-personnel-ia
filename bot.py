# -*- coding: utf-8 -*-
import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from database import (get_taches, get_notes, ajouter_tache, ajouter_note,
                      terminer_tache, supprimer_tache, supprimer_note,
                      ajouter_rappel, get_rappels_actifs, get_historique,
                      marquer_rappel_envoye)
from claude_brain import (chat, analyser_intention, generer_resume,
                           generer_plan_journee, comparer_ia)
from datetime import datetime

load_dotenv(dotenv_path=r'C:\Users\fallm\PycharmProjects\telegram\.env')

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# IA active par defaut
ia_active = {"modele": "claude"}

MENU_PRINCIPAL = ReplyKeyboardMarkup([
    [KeyboardButton("?? Chat"), KeyboardButton("? Taches")],
    [KeyboardButton("?? Notes"), KeyboardButton("? Rappels")],
    [KeyboardButton("?? Planning"), KeyboardButton("?? Stats")],
    [KeyboardButton("?? Changer IA"), KeyboardButton("?? Menu")]
], resize_keyboard=True)

MENU_IA = ReplyKeyboardMarkup([
    [KeyboardButton("?? Claude (Anthropic)"),
     KeyboardButton("?? ChatGPT (OpenAI)")],
    [KeyboardButton("?? Gemini (Google)"),
     KeyboardButton("? Comparer les 3 IA")],
    [KeyboardButton("?? Menu")]
], resize_keyboard=True)

sessions = {}

def get_ia_emoji():
    modele = ia_active["modele"]
    if modele == "claude": return "?? Claude"
    if modele == "chatgpt": return "?? ChatGPT"
    if modele == "gemini": return "?? Gemini"
    return "?? IA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nom = update.effective_user.first_name
    await update.message.reply_text(
        f"?? Bonjour *{nom}* !\n\n"
        f"Je suis ton assistant personnel IA ??\n\n"
        f"*3 cerveaux IA disponibles :*\n"
        f"?? Claude (Anthropic) - Principal\n"
        f"?? ChatGPT (OpenAI) - Secondaire\n"
        f"?? Gemini (Google) - Tertiaire\n\n"
        f"IA active : *{get_ia_emoji()}*\n\n"
        f"Disponible *24/7* pour t'aider !",
        parse_mode="Markdown",
        reply_markup=MENU_PRINCIPAL
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_user.id)
    texte = update.message.text
    session = sessions.get(chat_id, {"etape": "menu"})

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # --- MENU ---
    if texte == "?? Menu":
        sessions[chat_id] = {"etape": "menu"}
        await update.message.reply_text(
            f"?? Menu principal\nIA active : *{get_ia_emoji()}*",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    # --- CHANGER IA ---
    if texte == "?? Changer IA":
        sessions[chat_id] = {"etape": "changer_ia"}
        await update.message.reply_text(
            f"?? *Choisis ton IA*\n\nIA active : *{get_ia_emoji()}*\n\n"
            f"Chaque IA a ses forces :\n"
            f"?? Claude ? Analyse, redaction, planification\n"
            f"?? ChatGPT ? Creativite, conversation\n"
            f"?? Gemini ? Recherche, synthese\n"
            f"? Comparer ? Voir les 3 reponses",
            parse_mode="Markdown",
            reply_markup=MENU_IA)
        return

    if texte == "?? Claude (Anthropic)":
        ia_active["modele"] = "claude"
        await update.message.reply_text(
            "?? *Claude activé !*\nPropulsé par Anthropic",
            parse_mode="Markdown", reply_markup=MENU_PRINCIPAL)
        return

    if texte == "?? ChatGPT (OpenAI)":
        ia_active["modele"] = "chatgpt"
        await update.message.reply_text(
            "?? *ChatGPT activé !*\nPropulsé par OpenAI",
            parse_mode="Markdown", reply_markup=MENU_PRINCIPAL)
        return

    if texte == "?? Gemini (Google)":
        ia_active["modele"] = "gemini"
        await update.message.reply_text(
            "?? *Gemini activé !*\nPropulsé par Google",
            parse_mode="Markdown", reply_markup=MENU_PRINCIPAL)
        return

    if texte == "? Comparer les 3 IA":
        sessions[chat_id] = {"etape": "comparer"}
        await update.message.reply_text(
            "? *Comparaison des 3 IA*\n\nEnvoie ta question et je te montre les 3 reponses !",
            parse_mode="Markdown", reply_markup=MENU_PRINCIPAL)
        return

    if session.get("etape") == "comparer":
        await update.message.reply_text("? Interrogation des 3 IA en cours...")
        resultats = comparer_ia(texte)
        msg = f"? *Comparaison pour :* _{texte}_\n\n"
        msg += f"?? *Claude :*\n{resultats.get('claude', 'Erreur')[:400]}\n\n"
        msg += f"?? *ChatGPT :*\n{resultats.get('chatgpt', 'Erreur')[:400]}\n\n"
        msg += f"?? *Gemini :*\n{resultats.get('gemini', 'Erreur')[:400]}"
        await update.message.reply_text(msg, parse_mode="Markdown",
                                         reply_markup=MENU_PRINCIPAL)
        sessions[chat_id] = {"etape": "menu"}
        return

    # --- STATS ---
    if texte == "?? Stats":
        taches = get_taches()
        notes = get_notes()
        rappels = get_rappels_actifs()
        en_attente = [t for t in taches if t["statut"] == "en attente"]
        terminees = [t for t in taches if t["statut"] == "termine"]
        await update.message.reply_text(
            f"?? *Statistiques*\n\n"
            f"? Taches en attente : {len(en_attente)}\n"
            f"?? Taches terminees : {len(terminees)}\n"
            f"?? Notes : {len(notes)}\n"
            f"? Rappels actifs : {len(rappels)}\n"
            f"?? IA active : {get_ia_emoji()}\n"
            f"?? {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    # --- TACHES ---
    if texte == "? Taches":
        sessions[chat_id] = {"etape": "taches"}
        taches = get_taches(statut="en attente")
        if not taches:
            msg = "? Aucune tache en attente !\n\nTape une tache a ajouter :"
        else:
            msg = "? *Taches en attente :*\n\n"
            for t in taches:
                emoji = "??" if t["priorite"] == "haute" else "??"
                msg += f"{emoji} [{t['id']}] {t['titre']}\n"
            msg += "\n• Tape 'terminer X' pour terminer\n• Tape 'supprimer X' pour supprimer\n• Ou ajoute une nouvelle tache"
        await update.message.reply_text(msg, parse_mode="Markdown",
                                         reply_markup=MENU_PRINCIPAL)
        return

    if session.get("etape") == "taches":
        if texte.lower().startswith("terminer "):
            try:
                tid = int(texte.split()[1])
                terminer_tache(tid)
                await update.message.reply_text(f"?? Tache {tid} terminee !",
                                                 reply_markup=MENU_PRINCIPAL)
            except:
                await update.message.reply_text("? Format : terminer X",
                                                 reply_markup=MENU_PRINCIPAL)
            return
        if texte.lower().startswith("supprimer "):
            try:
                tid = int(texte.split()[1])
                supprimer_tache(tid)
                await update.message.reply_text(f"??? Tache supprimee !",
                                                 reply_markup=MENU_PRINCIPAL)
            except:
                await update.message.reply_text("? Format : supprimer X",
                                                 reply_markup=MENU_PRINCIPAL)
            return
        ajouter_tache(texte)
        await update.message.reply_text(f"? Tache ajoutee : *{texte}*",
                                         parse_mode="Markdown",
                                         reply_markup=MENU_PRINCIPAL)
        return

    # --- NOTES ---
    if texte == "?? Notes":
        sessions[chat_id] = {"etape": "notes"}
        notes = get_notes()
        if not notes:
            msg = "?? Aucune note.\n\nTape ton message pour creer une note :"
        else:
            msg = "?? *Tes notes recentes :*\n\n"
            for n in notes[:5]:
                msg += f"[{n['id']}] {n['titre'] or n['contenu'][:30]}...\n"
            msg += "\nTape 'supprimer X' ou ecris une nouvelle note :"
        await update.message.reply_text(msg, parse_mode="Markdown",
                                         reply_markup=MENU_PRINCIPAL)
        return

    if session.get("etape") == "notes":
        if texte.lower().startswith("supprimer "):
            try:
                nid = int(texte.split()[1])
                supprimer_note(nid)
                await update.message.reply_text(f"??? Note supprimee !",
                                                 reply_markup=MENU_PRINCIPAL)
            except:
                await update.message.reply_text("? Format : supprimer X",
                                                 reply_markup=MENU_PRINCIPAL)
            return
        ajouter_note(texte)
        await update.message.reply_text("?? Note sauvegardee !",
                                         reply_markup=MENU_PRINCIPAL)
        return

    # --- RAPPELS ---
    if texte == "? Rappels":
        sessions[chat_id] = {"etape": "rappels"}
        rappels = get_rappels_actifs()
        if not rappels:
            msg = "? Aucun rappel.\n\nFormat : 2026-03-20 10:00 | Message"
        else:
            msg = "? *Rappels actifs :*\n\n"
            for r in rappels:
                msg += f"• [{r['id']}] {r['date_heure']} - {r['message']}\n"
            msg += "\nAjoute un rappel (format: 2026-03-20 10:00 | Message) :"
        await update.message.reply_text(msg, parse_mode="Markdown",
                                         reply_markup=MENU_PRINCIPAL)
        return

    if session.get("etape") == "rappels":
        try:
            parts = texte.split("|")
            date_heure = parts[0].strip()
            message_rappel = parts[1].strip()
            ajouter_rappel(message_rappel, date_heure)
            await update.message.reply_text(
                f"? Rappel cree !\n?? {date_heure}\n?? {message_rappel}",
                reply_markup=MENU_PRINCIPAL)
        except:
            await update.message.reply_text(
                "? Format : 2026-03-20 10:00 | Message",
                reply_markup=MENU_PRINCIPAL)
        return

    # --- PLANNING ---
    if texte == "?? Planning":
        await update.message.reply_text(
            f"? Generation du planning avec {get_ia_emoji()}...")
        taches = get_taches(statut="en attente")
        planning = generer_plan_journee(taches, modele=ia_active["modele"])
        await update.message.reply_text(
            f"?? *Ton planning :*\n\n{planning}",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    # --- RESUME ---
    if texte.lower().startswith("resume:") or texte.lower().startswith("résume:"):
        contenu = texte.split(":", 1)[1].strip()
        await update.message.reply_text(
            f"? Resume avec {get_ia_emoji()}...")
        resume = generer_resume(contenu, modele=ia_active["modele"])
        await update.message.reply_text(
            f"?? *Resume :*\n\n{resume}",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    # --- CHAT INTELLIGENT ---
    historique = get_historique(8)
    intention = analyser_intention(texte)

    if intention["intention"] == "tache" and intention["action"] == "creer":
        titre = texte.replace("cree une tache", "").replace("ajoute", "").strip()
        ajouter_tache(titre)
        await update.message.reply_text(
            f"? Tache creee : *{titre}*",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    if intention["intention"] == "note" and intention["action"] == "creer":
        contenu = texte.replace("note:", "").replace("note :", "").strip()
        ajouter_note(contenu)
        await update.message.reply_text(
            "?? Note sauvegardee !",
            reply_markup=MENU_PRINCIPAL)
        return

    reponse = chat(texte, historique, modele=ia_active["modele"])
    await update.message.reply_text(
        f"{get_ia_emoji()} : {reponse}",
        reply_markup=MENU_PRINCIPAL)

async def verifier_rappels(context: ContextTypes.DEFAULT_TYPE):
    rappels = get_rappels_actifs()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for r in rappels:
        if r["date_heure"] <= now:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"? *Rappel !*\n\n{r['message']}",
                parse_mode="Markdown")
            marquer_rappel_envoye(r["id"])

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(verifier_rappels, interval=60, first=10)
    print("[BOT] Assistant 3 IA demarre !")
    print(f"[BOT] Claude + ChatGPT + Gemini prets !")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
