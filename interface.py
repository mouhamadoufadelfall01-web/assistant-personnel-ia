# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import os
import sys

class BotInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Assistant Personnel IA")
        self.root.geometry("500x600")
        self.root.configure(bg="#0f0f1a")
        self.root.resizable(False, False)
        self.process = None

        # ─── TITRE ───
        tk.Label(root, text="🤖", font=("Arial", 48),
                 bg="#0f0f1a").pack(pady=10)
        tk.Label(root, text="Assistant Personnel IA",
                 font=("Arial", 18, "bold"),
                 bg="#0f0f1a", fg="white").pack()
        tk.Label(root, text="Propulsé par Groq + Llama3",
                 font=("Arial", 11),
                 bg="#0f0f1a", fg="#4A90D9").pack(pady=5)

        # ─── STATUS ───
        self.status_frame = tk.Frame(root, bg="#1a1a2e",
                                      relief="flat", bd=0)
        self.status_frame.pack(pady=10, padx=20, fill="x")
        self.status_dot = tk.Label(self.status_frame, text="⚫",
                                    font=("Arial", 14),
                                    bg="#1a1a2e")
        self.status_dot.pack(side="left", padx=10, pady=8)
        self.status_label = tk.Label(self.status_frame,
                                      text="Bot arrete",
                                      font=("Arial", 12),
                                      bg="#1a1a2e", fg="#94a3b8")
        self.status_label.pack(side="left", pady=8)

        # ─── BOUTONS ───
        btn_frame = tk.Frame(root, bg="#0f0f1a")
        btn_frame.pack(pady=15)

        self.btn_start = tk.Button(btn_frame,
            text="▶ Allumer le Bot",
            font=("Arial", 13, "bold"),
            bg="#10b981", fg="white",
            padx=25, pady=12,
            cursor="hand2",
            relief="flat",
            command=self.allumer_bot)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_stop = tk.Button(btn_frame,
            text="⏹ Eteindre le Bot",
            font=("Arial", 13, "bold"),
            bg="#ef4444", fg="white",
            padx=25, pady=12,
            cursor="hand2",
            relief="flat",
            state="disabled",
            command=self.eteindre_bot)
        self.btn_stop.grid(row=0, column=1, padx=10)

        # ─── LOGS ───
        tk.Label(root, text="📋 Logs :",
                 font=("Arial", 11, "bold"),
                 bg="#0f0f1a", fg="#94a3b8").pack(anchor="w", padx=20)

        self.log_box = scrolledtext.ScrolledText(root,
            width=55, height=15,
            font=("Courier", 9),
            bg="#1a1a2e", fg="#e2e8f0",
            insertbackground="white",
            relief="flat")
        self.log_box.pack(padx=20, pady=5)

        # ─── QUITTER ───
        tk.Button(root,
            text="❌ Quitter",
            font=("Arial", 10),
            bg="#374151", fg="white",
            padx=15, pady=6,
            cursor="hand2",
            relief="flat",
            command=self.quitter).pack(pady=10)

        self.log("🤖 Interface demarree !")
        self.log("📱 Appuie sur 'Allumer' pour demarrer le bot Telegram")

    def log(self, message):
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)

    def allumer_bot(self):
        self.log("🟢 Demarrage du bot...")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.status_dot.config(text="🟢")
        self.status_label.config(text="Bot actif", fg="#10b981")

        def run():
            self.process = subprocess.Popen(
                [sys.executable, "bot.py"],
                cwd=r"C:\Users\fallm\PycharmProjects\telegram",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            for line in self.process.stdout:
                self.log(line.strip())
            self.log("🔴 Bot arrete !")
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            self.status_dot.config(text="⚫")
            self.status_label.config(text="Bot arrete", fg="#94a3b8")

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def eteindre_bot(self):
        if self.process:
            self.process.terminate()
            self.log("🔴 Bot arrete !")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_dot.config(text="⚫")
        self.status_label.config(text="Bot arrete", fg="#94a3b8")

    def quitter(self):
        if self.process:
            self.process.terminate()
        self.root.quit()

root = tk.Tk()
app = BotInterface(root)
root.mainloop()
