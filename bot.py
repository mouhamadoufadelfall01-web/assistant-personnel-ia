# -*- coding: utf-8 -*-
import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from database import (get_taches, get_notes, ajouter_tache, ajouter_note,
                      terminer_tache, supprimer_tache, supprimer_note,
                      ajouter_rappel, get_rappels_actifs, get_historique,
                      marquer_rappel_envoye)
from claude_brain import (chat, analyser_intention, generer_resume,
                           generer_plan_journee, comparer_ia)
from business_bots import (generer_facture, scraper_leads_simple,
                            surveiller_prix, generer_rapport,
                            get_meteo, get_taux_change,
                            get_actualites, get_blague)
from datetime import datetime

load_dotenv(dotenv_path=r'C:\Users\fallm\PycharmProjects\telegram\.env')

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ia_active = {"modele": "groq"}

MENU_PRINCIPAL = ReplyKeyboardMarkup([
    [KeyboardButton("💬 Chat"), KeyboardButton("✅ Taches")],
    [KeyboardButton("📝 Notes"), KeyboardButton("⏰ Rappels")],
    [KeyboardButton("📅 Planning"), KeyboardButton("📊 Stats")],
    [KeyboardButton("🛠️ Business"), KeyboardButton("🌍 Info")],
    [KeyboardButton("🏠 Menu")]
], resize_keyboard=True)

MENU_BUSINESS = ReplyKeyboardMarkup([
    [KeyboardButton("📄 Generer Facture"),
     KeyboardButton("📊 Generer Rapport")],
    [KeyboardButton("🔍 Scraper Leads"),
     KeyboardButton("👁️ Surveiller Prix")],
    [KeyboardButton("🏠 Menu")]
], resize_keyboard=True)

MENU_INFO = ReplyKeyboardMarkup([
    [KeyboardButton("🌤️ Meteo"),
     KeyboardButton("💱 Taux de change")],
    [KeyboardButton("📰 Actualites"),
     KeyboardButton("😄 Blague")],
    [KeyboardButton("🏠 Menu")]
], resize_keyboard=True)

sessions = {}

def get_ia_emoji():
    return "🟢 Groq (Llama3)"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nom = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Bonjour *{nom}* !\n\n"
        f"Je suis ton assistant personnel IA 🤖\n\n"
        f"*Mes capacites :*\n"
        f"💬 Chat intelligent\n"
        f"✅ Gestion des taches\n"
        f"📝 Notes et rappels\n"
        f"📅 Planning intelligent\n"
        f"📄 Factures et rapports PDF\n"
        f"🔍 Scraper de leads\n"
        f"🌤️ Meteo et actualites\n"
        f"💱 Taux de change\n\n"
        f"Disponible *24/7* pour t'aider !",
        parse_mode="Markdown",
        reply_markup=MENU_PRINCIPAL
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_user.id)
    texte = update.message.text
    session = sessions.get(chat_id, {"etape": "menu"})

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing")

    # ─── MENU ───
    if texte == "🏠 Menu":
        sessions[chat_id] = {"etape": "menu"}
        await update.message.reply_text(
            "🏠 Menu principal",
            reply_markup=MENU_PRINCIPAL)
        return

    # ─── BUSINESS ───
    if texte == "🛠️ Business":
        sessions[chat_id] = {"etape": "business"}
        await update.message.reply_text(
            "🛠️ *Outils Business*\n\nChoisis une action :",
            parse_mode="Markdown",
            reply_markup=MENU_BUSINESS)
        return

    # ─── INFO ───
    if texte == "🌍 Info":
        sessions[chat_id] = {"etape": "info"}
        await update.message.reply_text(
            "🌍 *Informations en temps reel*",
            parse_mode="Markdown",
            reply_markup=MENU_INFO)
        return

    # ─── METEO ───
    if texte == "🌤️ Meteo":
        sessions[chat_id] = {"etape": "meteo"}
        await update.message.reply_text(
            "🌤️ Pour quelle ville veux-tu la meteo ?",
            reply_markup=MENU_INFO)
        return

    if session.get("etape") == "meteo":
        meteo = get_meteo(texte)
        await update.message.reply_text(
            f"🌤️ {meteo}", reply_markup=MENU_PRINCIPAL)
        sessions[chat_id] = {"etape": "menu"}
        return

    # ─── TAUX DE CHANGE ───
    if texte == "💱 Taux de change":
        await update.message.reply_text("⏳ Recuperation des taux...")
        taux = get_taux_change("EUR")
        await update.message.reply_text(
            f"💱 *{taux}*",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    # ─── ACTUALITES ───
    if texte == "📰 Actualites":
        sessions[chat_id] = {"etape": "actualites"}
        await update.message.reply_text(
            "📰 Sur quel sujet veux-tu les actualites ?",
            reply_markup=MENU_INFO)
        return

    if session.get("etape") == "actualites":
        await update.message.reply_text("⏳ Recherche des actualites...")
        actu = get_actualites(texte)
        await update.message.reply_text(actu, reply_markup=MENU_PRINCIPAL)
        sessions[chat_id] = {"etape": "menu"}
        return

    # ─── BLAGUE ───
    if texte == "😄 Blague":
        blague = get_blague()
        await update.message.reply_text(
            blague, reply_markup=MENU_PRINCIPAL)
        return

    # ─── FACTURE ───
    if texte == "📄 Generer Facture":
        sessions[chat_id] = {"etape": "facture_client"}
        await update.message.reply_text(
            "📄 *Generateur de facture*\n\nNom du client :",
            parse_mode="Markdown",
            reply_markup=MENU_BUSINESS)
        return

    if session.get("etape") == "facture_client":
        sessions[chat_id] = {**session, "etape": "facture_email",
                              "client_nom": texte}
        await update.message.reply_text("Email du client :")
        return

    if session.get("etape") == "facture_email":
        sessions[chat_id] = {**session, "etape": "facture_services",
                              "client_email": texte}
        await update.message.reply_text(
            "Services (format: Nom,Quantite,Prix - un par ligne) :\nEx: Developpement web,1,500")
        return

    if session.get("etape") == "facture_services":
        services = []
        for ligne in texte.split("\n"):
            parts = ligne.split(",")
            if len(parts) == 3:
                try:
                    services.append({
                        "nom": parts[0].strip(),
                        "quantite": int(parts[1].strip()),
                        "prix": float(parts[2].strip())
                    })
                except:
                    pass
        if not services:
            await update.message.reply_text(
                "Format incorrect. Ex: Developpement web,1,500")
            return
        await update.message.reply_text("⏳ Generation de la facture...")
        try:
            fichier, total = generer_facture(
                session["client_nom"],
                session["client_email"],
                services)
            await update.message.reply_document(
                document=open(fichier, "rb"),
                filename=os.path.basename(fichier),
                caption=f"📄 Facture generee !\nTotal : {total} EUR"
            )
        except Exception as e:
            await update.message.reply_text(f"Erreur : {e}")
        sessions[chat_id] = {"etape": "menu"}
        await update.message.reply_text(
            "Facture envoyee !", reply_markup=MENU_PRINCIPAL)
        return

    # ─── RAPPORT ───
    if texte == "📊 Generer Rapport":
        sessions[chat_id] = {"etape": "rapport_titre"}
        await update.message.reply_text(
            "📊 Titre du rapport :",
            reply_markup=MENU_BUSINESS)
        return

    if session.get("etape") == "rapport_titre":
        sessions[chat_id] = {**session, "etape": "rapport_contenu",
                              "rapport_titre": texte}
        await update.message.reply_text(
            "Contenu du rapport (sections separees par ---) :")
        return

    if session.get("etape") == "rapport_contenu":
        sections_text = texte.split("---")
        sections = []
        for i, s in enumerate(sections_text):
            sections.append({
                "titre": f"Section {i+1}",
                "contenu": s.strip()
            })
        await update.message.reply_text("⏳ Generation du rapport...")
        try:
            fichier = generer_rapport(session["rapport_titre"], sections)
            await update.message.reply_document(
                document=open(fichier, "rb"),
                filename=os.path.basename(fichier),
                caption=f"📊 Rapport genere : {session['rapport_titre']}"
            )
        except Exception as e:
            await update.message.reply_text(f"Erreur : {e}")
        sessions[chat_id] = {"etape": "menu"}
        await update.message.reply_text(
            "Rapport envoye !", reply_markup=MENU_PRINCIPAL)
        return

    # ─── SCRAPER LEADS ───
    if texte == "🔍 Scraper Leads":
        sessions[chat_id] = {"etape": "scraper"}
        await update.message.reply_text(
            "🔍 Quel type de business cherches-tu ?\nEx: restaurants, salons de coiffure",
            reply_markup=MENU_BUSINESS)
        return

    if session.get("etape") == "scraper":
        await update.message.reply_text("⏳ Scraping en cours...")
        resultats = scraper_leads_simple(texte)
        msg = f"🔍 *Leads trouves pour '{texte}' :*\n\n"
        for r in resultats:
            msg += f"• {r['nom']}\n{r['url'][:50]}...\n\n"
        await update.message.reply_text(
            msg, parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        sessions[chat_id] = {"etape": "menu"}
        return

    # ─── SURVEILLER PRIX ───
    if texte == "👁️ Surveiller Prix":
        sessions[chat_id] = {"etape": "veille_url"}
        await update.message.reply_text(
            "👁️ Entre l'URL du site a surveiller :",
            reply_markup=MENU_BUSINESS)
        return

    if session.get("etape") == "veille_url":
        await update.message.reply_text("⏳ Analyse du site...")
        resultat = surveiller_prix(texte)
        msg = f"👁️ *Analyse :*\n\n"
        for k, v in resultat.items():
            msg += f"• {k}: {v}\n"
        await update.message.reply_text(
            msg, parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        sessions[chat_id] = {"etape": "menu"}
        return

    # ─── STATS ───
    if texte == "📊 Stats":
        taches = get_taches()
        notes = get_notes()
        rappels = get_rappels_actifs()
        en_attente = [t for t in taches if t["statut"] == "en attente"]
        terminees = [t for t in taches if t["statut"] == "termine"]
        await update.message.reply_text(
            f"📊 *Statistiques*\n\n"
            f"✅ Taches en attente : {len(en_attente)}\n"
            f"✔️ Taches terminees : {len(terminees)}\n"
            f"📝 Notes : {len(notes)}\n"
            f"⏰ Rappels actifs : {len(rappels)}\n"
            f"🤖 IA : {get_ia_emoji()}\n"
            f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    # ─── TACHES ───
    if texte == "✅ Taches":
        sessions[chat_id] = {"etape": "taches"}
        taches = get_taches(statut="en attente")
        if not taches:
            msg = "✅ Aucune tache !\n\nTape une tache a ajouter :"
        else:
            msg = "✅ *Taches en attente :*\n\n"
            for t in taches:
                emoji = "🔴" if t["priorite"] == "haute" else "🟡"
                msg += f"{emoji} [{t['id']}] {t['titre']}\n"
            msg += "\n• 'terminer X' → terminer\n• 'supprimer X' → supprimer"
        await update.message.reply_text(
            msg, parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    if session.get("etape") == "taches":
        if texte.lower().startswith("terminer "):
            try:
                tid = int(texte.split()[1])
                terminer_tache(tid)
                await update.message.reply_text(
                    f"✔️ Tache {tid} terminee !",
                    reply_markup=MENU_PRINCIPAL)
            except:
                await update.message.reply_text("❌ Format : terminer X")
            return
        if texte.lower().startswith("supprimer "):
            try:
                tid = int(texte.split()[1])
                supprimer_tache(tid)
                await update.message.reply_text(
                    f"🗑️ Tache supprimee !",
                    reply_markup=MENU_PRINCIPAL)
            except:
                await update.message.reply_text("❌ Format : supprimer X")
            return
        ajouter_tache(texte)
        await update.message.reply_text(
            f"✅ Tache ajoutee : *{texte}*",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    # ─── NOTES ───
    if texte == "📝 Notes":
        sessions[chat_id] = {"etape": "notes"}
        notes = get_notes()
        if not notes:
            msg = "📝 Aucune note.\n\nTape pour creer une note :"
        else:
            msg = "📝 *Notes recentes :*\n\n"
            for n in notes[:5]:
                msg += f"[{n['id']}] {n['contenu'][:40]}...\n"
            msg += "\n'supprimer X' pour supprimer :"
        await update.message.reply_text(
            msg, parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    if session.get("etape") == "notes":
        if texte.lower().startswith("supprimer "):
            try:
                nid = int(texte.split()[1])
                supprimer_note(nid)
                await update.message.reply_text(
                    "🗑️ Note supprimee !",
                    reply_markup=MENU_PRINCIPAL)
            except:
                await update.message.reply_text("❌ Format : supprimer X")
            return
        ajouter_note(texte)
        await update.message.reply_text(
            "📝 Note sauvegardee !",
            reply_markup=MENU_PRINCIPAL)
        return

    # ─── RAPPELS ───
    if texte == "⏰ Rappels":
        sessions[chat_id] = {"etape": "rappels"}
        rappels = get_rappels_actifs()
        if not rappels:
            msg = "⏰ Aucun rappel.\n\nFormat : 2026-03-20 10:00 | Message"
        else:
            msg = "⏰ *Rappels actifs :*\n\n"
            for r in rappels:
                msg += f"• [{r['id']}] {r['date_heure']} - {r['message']}\n"
            msg += "\nAjoute : 2026-03-20 10:00 | Message"
        await update.message.reply_text(
            msg, parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    if session.get("etape") == "rappels":
        try:
            parts = texte.split("|")
            date_heure = parts[0].strip()
            message_rappel = parts[1].strip()
            ajouter_rappel(message_rappel, date_heure)
            await update.message.reply_text(
                f"⏰ Rappel cree !\n📅 {date_heure}\n💬 {message_rappel}",
                reply_markup=MENU_PRINCIPAL)
        except:
            await update.message.reply_text(
                "❌ Format : 2026-03-20 10:00 | Message")
        return

    # ─── PLANNING ───
    if texte == "📅 Planning":
        await update.message.reply_text("⏳ Generation du planning...")
        taches = get_taches(statut="en attente")
        planning = generer_plan_journee(taches)
        await update.message.reply_text(
            f"📅 *Ton planning :*\n\n{planning}",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    # ─── CHAT INTELLIGENT ───
    historique = get_historique(8)
    intention = analyser_intention(texte)

    if intention["intention"] == "tache" and intention["action"] == "creer":
        titre = texte.replace("cree une tache", "").replace("ajoute", "").strip()
        ajouter_tache(titre)
        await update.message.reply_text(
            f"✅ Tache creee : *{titre}*",
            parse_mode="Markdown",
            reply_markup=MENU_PRINCIPAL)
        return

    if intention["intention"] == "note" and intention["action"] == "creer":
        contenu = texte.replace("note:", "").replace("note :", "").strip()
        ajouter_note(contenu)
        await update.message.reply_text(
            "📝 Note sauvegardee !",
            reply_markup=MENU_PRINCIPAL)
        return

    reponse = chat(texte, historique, modele="groq")
    await update.message.reply_text(
        f"🤖 {reponse}",
        reply_markup=MENU_PRINCIPAL)

async def verifier_rappels(context: ContextTypes.DEFAULT_TYPE):
    rappels = get_rappels_actifs()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for r in rappels:
        if r["date_heure"] <= now:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"⏰ *Rappel !*\n\n{r['message']}",
                parse_mode="Markdown")
            marquer_rappel_envoye(r["id"])

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(verifier_rappels, interval=60, first=10)
    print("[BOT] Assistant business demarre !")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
