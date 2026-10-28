# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import urllib.request
import json
import re
import threading
import webbrowser
from datetime import datetime

NAVY = "#17222d"
RED = "#ad4437"
CREAM = "#f5f2ee"
CARD_BG = "#ffffff"
INK = "#232930"
MUTED = "#5d646b"
GREEN = "#285849"

def fetch_hits(urn):
    url = f"https://hits.sh/api/urns/{urn}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode("utf-8"))
            total = int(data.get("total", 0))
            weekly = int(data.get("weekly", 0))
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            today = 0
            for item in data.get("items", []):
                for d in item.get("data", []):
                    if d.get("day") == today_str:
                        today = int(d.get("value", 0))
            return {"total": total, "today": today, "weekly": weekly}
    except Exception:
        return {"total": 0, "today": 0, "weekly": 0}

def fetch_yt_views(vid):
    url = f"https://www.youtube.com/watch?v={vid}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9"})
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8", errors="ignore")
            m = re.search(r'"viewCount":"(\d+)"', html)
            return int(m.group(1)) if m else 0
    except Exception:
        return 0

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Estadísticas en Vivo · Rubén Muñoz Docente")
        self.root.geometry("680x520")
        self.root.configure(bg=CREAM)
        self.root.resizable(False, False)

        try:
            import os
            ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono-visitas.ico")
            if os.path.exists(ico):
                self.root.iconbitmap(ico)
        except Exception:
            pass

        # Header
        hdr = tk.Frame(root, bg=NAVY, pady=18, padx=24)
        hdr.pack(fill="x")
        tk.Label(hdr, text="PANEL DE AUDIENCIA EN TIEMPO REAL", fg="#e8b19b", bg=NAVY,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(hdr, text="Rubén Muñoz Valadés · Web y YouTube", fg="#ffffff", bg=NAVY,
                 font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(2, 0))
        tk.Frame(root, bg=RED, height=4).pack(fill="x")

        # Status bar
        self.status_var = tk.StringVar(value="⏳ Conectando a internet para consultar tus visitas en vivo...")
        self.status_lbl = tk.Label(root, textvariable=self.status_var, bg=CREAM, fg=MUTED,
                                   font=("Segoe UI", 10, "italic"), pady=10)
        self.status_lbl.pack()

        # Grid container
        grid = tk.Frame(root, bg=CREAM, padx=24)
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self.cards = {}
        specs = [
            ("web", "🌐 Visitas a tu Página Web", "docente.rubenmunozdocente.digital", RED, 0, 0),
            ("cv", "📄 Descargas de tu CV (PDF)", "Clics en Descargar CV", GREEN, 0, 1),
            ("yt_main", "▶️ Vídeo Presentación YouTube", "youtu.be/hmVcdfkkZPk (Horizontal)", "#c4302b", 1, 0),
            ("yt_short", "📱 YouTube Short Vertical", "youtube.com/shorts/Rw0hQTTwMq8", "#0a66c2", 1, 1),
        ]

        for key, title, sub, color, r, c in specs:
            card = tk.Frame(grid, bg=CARD_BG, highlightbackground="#dfd9d0", highlightthickness=1, padx=18, pady=14)
            card.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)
            tk.Label(card, text=title, bg=CARD_BG, fg=NAVY, font=("Segoe UI", 11, "bold")).pack(anchor="w")
            tk.Label(card, text=sub, bg=CARD_BG, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 8))
            val_lbl = tk.Label(card, text="...", bg=CARD_BG, fg=color, font=("Segoe UI", 26, "bold"))
            val_lbl.pack(anchor="w")
            detail_lbl = tk.Label(card, text="Consultando...", bg=CARD_BG, fg=INK, font=("Segoe UI", 9))
            detail_lbl.pack(anchor="w", pady=(4, 0))
            self.cards[key] = (val_lbl, detail_lbl)

        # Total banner
        total_box = tk.Frame(root, bg="#ece6de", padx=20, pady=10)
        total_box.pack(fill="x", padx=32, pady=(4, 12))
        self.total_var = tk.StringVar(value="Impacto total acumulado (Web + YouTube): calculando...")
        tk.Label(total_box, textvariable=self.total_var, bg="#ece6de", fg=NAVY,
                 font=("Segoe UI", 11, "bold")).pack()

        # Buttons
        btn_bar = tk.Frame(root, bg=CREAM, pady=10, padx=24)
        btn_bar.pack(fill="x")

        tk.Button(btn_bar, text="🔄 Actualizar ahora", command=self.refresh,
                  bg=RED, fg="white", activebackground="#853327", activeforeground="white",
                  font=("Segoe UI", 9, "bold"), relief="flat", padx=14, pady=7, cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_bar, text="🌐 Abrir mi Web",
                  command=lambda: webbrowser.open("https://docente.rubenmunozdocente.digital/"),
                  bg="#ffffff", fg=NAVY, font=("Segoe UI", 9, "bold"), relief="solid", bd=1, padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_bar, text="▶️ YouTube Studio",
                  command=lambda: webbrowser.open("https://studio.youtube.com/channel/UCDhqkg0kxcJmZ-z6jGLRcvQ/analytics"),
                  bg="#ffffff", fg=NAVY, font=("Segoe UI", 9, "bold"), relief="solid", bd=1, padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_bar, text="🔍 Google Search Console",
                  command=lambda: webbrowser.open("https://search.google.com/search-console/performance/search-analytics?resource_id=https%3A%2F%2Fdocente.rubenmunozdocente.digital%2F"),
                  bg="#ffffff", fg=NAVY, font=("Segoe UI", 9, "bold"), relief="solid", bd=1, padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)

        self.refresh()

    def refresh(self):
        self.status_var.set("⏳ Actualizando datos en tiempo real desde internet...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        web = fetch_hits("docente.rubenmunozdocente.digital/visitas-web")
        cv = fetch_hits("docente.rubenmunozdocente.digital/descargas-cv")
        yt_main = fetch_yt_views("hmVcdfkkZPk")
        yt_short = fetch_yt_views("Rw0hQTTwMq8")
        self.root.after(0, lambda: self._update_ui(web, cv, yt_main, yt_short))

    def _update_ui(self, web, cv, yt_main, yt_short):
        now = datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")
        self.status_var.set(f"✅ Conectado · Última actualización: {now}")

        self.cards["web"][0].config(text=f"{web['total']} visitas")
        self.cards["web"][1].config(text=f"Hoy: {web['today']}  ·  Últimos 7 días: {web['weekly']}")

        self.cards["cv"][0].config(text=f"{cv['total']} descargas")
        self.cards["cv"][1].config(text=f"Hoy: {cv['today']}  ·  Últimos 7 días: {cv['weekly']}")

        self.cards["yt_main"][0].config(text=f"{yt_main} vistas")
        self.cards["yt_main"][1].config(text="Vídeo horizontal (1:17 min)")

        self.cards["yt_short"][0].config(text=f"{yt_short} vistas")
        self.cards["yt_short"][1].config(text="Vídeo vertical en el feed de Shorts")

        total_impact = web["total"] + yt_main + yt_short
        self.total_var.set(f"🏆 Impacto total acumulado: {total_impact} visualizaciones ({web['total']} en Web + {yt_main + yt_short} en YouTube)")

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()
