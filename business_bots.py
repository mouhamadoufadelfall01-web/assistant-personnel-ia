# -*- coding: utf-8 -*-
import os
import requests
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(dotenv_path=r'C:\Users\fallm\PycharmProjects\telegram\.env')

# ─── GENERATEUR DE FACTURES PDF ───
def generer_facture(client_nom, client_email, services, numero=None):
    os.makedirs("factures", exist_ok=True)
    if not numero:
        numero = datetime.now().strftime("%Y%m%d%H%M%S")
    fichier = f"factures/facture_{numero}.pdf"

    doc = SimpleDocTemplate(fichier, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Titre
    elements.append(Paragraph(f"<b>FACTURE N° {numero}</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    # Infos
    elements.append(Paragraph(f"<b>Date :</b> {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Client :</b> {client_nom}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Email :</b> {client_email}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Tableau services
    data = [["Service", "Quantite", "Prix unitaire", "Total"]]
    total_general = 0
    for s in services:
        total = s["quantite"] * s["prix"]
        total_general += total
        data.append([s["nom"], str(s["quantite"]),
                     f"{s['prix']} EUR", f"{total} EUR"])
    data.append(["", "", "TOTAL", f"{total_general} EUR"])

    table = Table(data, colWidths=[200, 80, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#4A90D9")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Merci pour votre confiance !", styles["Normal"]))

    doc.build(elements)
    return fichier, total_general

# ─── SCRAPER LEADS ───
def scraper_leads_simple(query, location="Dakar"):
    try:
        url = f"https://www.google.com/search?q={query}+{location}+contact+email"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        resultats = []
        for g in soup.find_all("div", class_="g")[:5]:
            titre = g.find("h3")
            lien = g.find("a")
            if titre and lien:
                resultats.append({
                    "nom": titre.text,
                    "url": lien.get("href", "")
                })
        return resultats
    except Exception as e:
        return [{"nom": f"Erreur: {e}", "url": ""}]

# ─── VEILLE CONCURRENTIELLE ───
def surveiller_prix(url, selecteur_css=None):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        if selecteur_css:
            element = soup.select_one(selecteur_css)
            if element:
                return {"prix": element.text.strip(), "url": url, "date": datetime.now().strftime("%d/%m/%Y %H:%M")}
        titre = soup.find("title")
        return {"prix": "Non trouve", "titre": titre.text if titre else "Inconnu", "url": url}
    except Exception as e:
        return {"erreur": str(e), "url": url}

# ─── GENERATEUR RAPPORT PDF ───
def generer_rapport(titre, sections, nom_fichier=None):
    os.makedirs("rapports", exist_ok=True)
    if not nom_fichier:
        nom_fichier = f"rapports/rapport_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"

    doc = SimpleDocTemplate(nom_fichier, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>{titre}</b>", styles["Title"]))
    elements.append(Paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    for section in sections:
        elements.append(Paragraph(f"<b>{section['titre']}</b>", styles["Heading2"]))
        elements.append(Paragraph(section["contenu"], styles["Normal"]))
        elements.append(Spacer(1, 15))

    doc.build(elements)
    return nom_fichier

# ─── METEO ───
def get_meteo(ville="Dakar"):
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY", "")
        if not api_key:
            return f"Meteo pour {ville} : API key manquante"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={ville}&appid={api_key}&units=metric&lang=fr"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("cod") == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            return f"Meteo {ville} : {temp}C, {desc}, Humidite: {humidity}%"
        return f"Ville non trouvee : {ville}"
    except Exception as e:
        return f"Erreur meteo : {e}"

# ─── TAUX DE CHANGE ───
def get_taux_change(base="EUR"):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        r = requests.get(url, timeout=10)
        data = r.json()
        xof = data["rates"].get("XOF", "N/A")
        usd = data["rates"].get("USD", "N/A")
        eur = data["rates"].get("EUR", "N/A")
        return f"Taux ({base}) :\n1 {base} = {xof} XOF\n1 {base} = {usd} USD\n1 {base} = {eur} EUR"
    except Exception as e:
        return f"Erreur taux : {e}"

# ─── ACTUALITES ───
def get_actualites(sujet="Senegal"):
    try:
        api_key = os.getenv("NEWS_API_KEY", "")
        if not api_key:
            url = f"https://newsapi.org/v2/everything?q={sujet}&language=fr&pageSize=3&apiKey=demo"
        else:
            url = f"https://newsapi.org/v2/everything?q={sujet}&language=fr&pageSize=3&apiKey={api_key}"
        r = requests.get(url, timeout=10)
        data = r.json()
        articles = data.get("articles", [])
        if not articles:
            return f"Aucune actualite trouvee pour : {sujet}"
        msg = f"Actualites {sujet} :\n\n"
        for a in articles[:3]:
            msg += f"• {a['title']}\n{a['url']}\n\n"
        return msg
    except Exception as e:
        return f"Erreur actualites : {e}"

# ─── BLAGUES ───
def get_blague():
    try:
        r = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=10)
        data = r.json()
        return f"😄 {data['setup']}\n\n{data['punchline']}"
    except:
        try:
            r = requests.get("https://v2.jokeapi.dev/joke/Any?lang=fr", timeout=10)
            data = r.json()
            if data["type"] == "single":
                return f"😄 {data['joke']}"
            return f"😄 {data['setup']}\n\n{data['delivery']}"
        except Exception as e:
            return f"Erreur blague : {e}"
