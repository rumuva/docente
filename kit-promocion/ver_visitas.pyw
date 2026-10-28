# -*- coding: utf-8 -*-
import os
import json
import re
import threading
import urllib.request
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import ttk

NAVY = "#17222d"
RED = "#ad4437"
CREAM = "#f5f2ee"
CARD_BG = "#ffffff"
INK = "#232930"
MUTED = "#5d646b"
GREEN = "#285849"
TOPIC = "rm_docente_visitas_84a9c2e1"
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historial_visitas.json")


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


def load_saved_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def fetch_and_merge_visitors():
    history = load_saved_history()
    known_ids = {item.get("id") for item in history if item.get("id")}
    url = f"https://ntfy.sh/{TOPIC}/json?poll=1&since=all"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            lines = r.read().decode("utf-8", errors="ignore").splitlines()
            for line in lines:
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                    if ev.get("event") != "message":
                        continue
                    msg_id = ev.get("id")
                    if msg_id in known_ids:
                        continue
                    raw_msg = ev.get("message", "{}")
                    payload = json.loads(raw_msg)
                    ts_epoch = ev.get("time", 0)
                    dt_str = datetime.fromtimestamp(ts_epoch).strftime("%d/%m/%Y %H:%M:%S") if ts_epoch else payload.get("ts", "")
                    entry = {
                        "id": msg_id,
                        "time_epoch": ts_epoch,
                        "fecha": dt_str,
                        "accion": payload.get("accion", "🌐 Visita"),
                        "pagina": payload.get("pagina", "/"),
                        "origen": payload.get("origen", "Directo / WhatsApp"),
                        "ciudad": payload.get("ciudad", "Desconocida"),
                        "isp": payload.get("isp", "No disponible"),
                        "ip": payload.get("ip", "No disponible"),
                        "dispositivo": payload.get("dispositivo", "Desconocido"),
                        "pantalla": payload.get("pantalla", ""),
                        "idioma": payload.get("idioma", "es-ES"),
                    }
                    history.append(entry)
                    known_ids.add(msg_id)
                except Exception:
                    continue
    except Exception:
        pass

    history.sort(key=lambda x: x.get("time_epoch", 0), reverse=True)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[:500], f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return history


class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Audiencia e Identificación de Visitantes · Rubén Muñoz Docente")
        self.root.geometry("1020x740")
        self.root.configure(bg=CREAM)
        self.visitors = []

        try:
            ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icono-visitas.ico")
            if os.path.exists(ico):
                self.root.iconbitmap(ico)
        except Exception:
            pass

        # Header
        hdr = tk.Frame(root, bg=NAVY, pady=14, padx=24)
        hdr.pack(fill="x")
        tk.Label(hdr, text="PANEL DE AUDIENCIA E IDENTIFICACIÓN DE VISITANTES EN TIEMPO REAL", fg="#e8b19b", bg=NAVY,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(hdr, text="Rubén Muñoz Valadés · Web y YouTube", fg="#ffffff", bg=NAVY,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(2, 0))
        tk.Frame(root, bg=RED, height=4).pack(fill="x")

        # Top bar with status + total
        top_bar = tk.Frame(root, bg=CREAM, padx=24, pady=8)
        top_bar.pack(fill="x")
        self.status_var = tk.StringVar(value="⏳ Conectando a internet para consultar tus visitas y el registro de accesos...")
        tk.Label(top_bar, textvariable=self.status_var, bg=CREAM, fg=MUTED, font=("Segoe UI", 9, "italic")).pack(side="left")
        self.total_var = tk.StringVar(value="Calculando impacto total...")
        tk.Label(top_bar, textvariable=self.total_var, bg=CREAM, fg=NAVY, font=("Segoe UI", 10, "bold")).pack(side="right")

        # 4 KPI Cards in a single row
        kpi_frame = tk.Frame(root, bg=CREAM, padx=20)
        kpi_frame.pack(fill="x")
        for i in range(4):
            kpi_frame.columnconfigure(i, weight=1)

        self.cards = {}
        specs = [
            ("web", "🌐 Visitas a tu Web", RED, 0),
            ("cv", "📄 Descargas de CV", GREEN, 1),
            ("yt_main", "▶️ YouTube Horizontal", "#c4302b", 2),
            ("yt_short", "📱 YouTube Short", "#0a66c2", 3),
        ]
        for key, title, color, col in specs:
            card = tk.Frame(kpi_frame, bg=CARD_BG, highlightbackground="#dfd9d0", highlightthickness=1, padx=14, pady=10)
            card.grid(row=0, column=col, sticky="nsew", padx=5, pady=4)
            tk.Label(card, text=title, bg=CARD_BG, fg=NAVY, font=("Segoe UI", 10, "bold")).pack(anchor="w")
            val_lbl = tk.Label(card, text="...", bg=CARD_BG, fg=color, font=("Segoe UI", 20, "bold"))
            val_lbl.pack(anchor="w", pady=(2, 0))
            detail_lbl = tk.Label(card, text="Consultando...", bg=CARD_BG, fg=MUTED, font=("Segoe UI", 8))
            detail_lbl.pack(anchor="w")
            self.cards[key] = (val_lbl, detail_lbl)

        # Visitor Log Table section
        log_section = tk.Frame(root, bg=CREAM, padx=24, pady=8)
        log_section.pack(fill="both", expand=True)

        lbl_row = tk.Frame(log_section, bg=CREAM)
        lbl_row.pack(fill="x", pady=(0, 6))
        tk.Label(lbl_row, text="🕵️ Registro detallado de quién ha accedido a tu web (Haz clic en una fila para ver todos sus datos técnicos):",
                 bg=CREAM, fg=NAVY, font=("Segoe UI", 10, "bold")).pack(side="left")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#ffffff", foreground=INK, rowheight=28, fieldbackground="#ffffff", font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=NAVY, foreground="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#f4e3d7")], foreground=[("selected", NAVY)])

        table_frame = tk.Frame(log_section, bg=CARD_BG, highlightbackground="#dfd9d0", highlightthickness=1)
        table_frame.pack(fill="both", expand=True)

        cols = ("fecha", "accion", "ciudad", "isp", "origen", "dispositivo")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=9)
        self.tree.heading("fecha", text="Fecha y Hora")
        self.tree.heading("accion", text="Acción / Página vista")
        self.tree.heading("ciudad", text="Ciudad / Provincia")
        self.tree.heading("isp", text="Red / Operador / Organización")
        self.tree.heading("origen", text="Viene desde (Origen)")
        self.tree.heading("dispositivo", text="Dispositivo y Navegador")

        self.tree.column("fecha", width=135, anchor="w")
        self.tree.column("accion", width=165, anchor="w")
        self.tree.column("ciudad", width=175, anchor="w")
        self.tree.column("isp", width=195, anchor="w")
        self.tree.column("origen", width=140, anchor="w")
        self.tree.column("dispositivo", width=160, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select_visitor)

        # Selected visitor full detail box
        detail_box = tk.Frame(root, bg="#ffffff", highlightbackground=RED, highlightthickness=1, padx=16, pady=10)
        detail_box.pack(fill="x", padx=24, pady=(2, 8))
        tk.Label(detail_box, text="📌 Ficha técnica completa del visitante seleccionado:", bg="#ffffff", fg=RED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.detail_text = tk.StringVar(value="Selecciona cualquier visita de la tabla superior para ver su IP, proveedor/empresa de red, resolución de pantalla, idioma y página exacta.")
        tk.Label(detail_box, textvariable=self.detail_text, bg="#ffffff", fg=INK,
                 font=("Segoe UI", 9), justify="left", wraplength=940).pack(anchor="w", pady=(3, 0))

        # Action Buttons
        btn_bar = tk.Frame(root, bg=CREAM, pady=8, padx=24)
        btn_bar.pack(fill="x")

        tk.Button(btn_bar, text="🔄 Actualizar datos ahora", command=self.refresh,
                  bg=RED, fg="white", activebackground="#853327", activeforeground="white",
                  font=("Segoe UI", 9, "bold"), relief="flat", padx=14, pady=7, cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_bar, text="🌐 Abrir mi Web",
                  command=lambda: webbrowser.open("https://docente.rubenmunozdocente.digital/"),
                  bg="#ffffff", fg=NAVY, font=("Segoe UI", 9, "bold"), relief="solid", bd=1, padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_bar, text="📈 Gráfica diaria (hits.sh)",
                  command=lambda: webbrowser.open("https://hits.sh/docente.rubenmunozdocente.digital/visitas-web/"),
                  bg="#ffffff", fg=NAVY, font=("Segoe UI", 9, "bold"), relief="solid", bd=1, padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_bar, text="▶️ YouTube Studio",
                  command=lambda: webbrowser.open("https://studio.youtube.com/channel/UCDhqkg0kxcJmZ-z6jGLRcvQ/analytics"),
                  bg="#ffffff", fg=NAVY, font=("Segoe UI", 9, "bold"), relief="solid", bd=1, padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)

        tk.Button(btn_bar, text="🔍 Google Search Console",
                  command=lambda: webbrowser.open("https://search.google.com/search-console/performance/search-analytics?resource_id=https%3A%2F%2Fdocente.rubenmunozdocente.digital%2F"),
                  bg="#ffffff", fg=NAVY, font=("Segoe UI", 9, "bold"), relief="solid", bd=1, padx=12, pady=6, cursor="hand2").pack(side="left", padx=4)

        self.refresh()

    def on_select_visitor(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.visitors):
            v = self.visitors[idx]
            info = (
                f"• Fecha y hora: {v.get('fecha')}   |   • Acción: {v.get('accion')} (Página: {v.get('pagina')})   |   • Origen: {v.get('origen')}\n"
                f"• Ubicación aproximada: {v.get('ciudad')}   |   • Red / Operador / Entidad (ISP): {v.get('isp')}   |   • Dirección IP: {v.get('ip')}\n"
                f"• Equipo y Navegador: {v.get('dispositivo')}   |   • Pantalla: {v.get('pantalla', 'N/D')} px   |   • Idioma: {v.get('idioma', 'es-ES')}"
            )
            self.detail_text.set(info)

    def refresh(self):
        self.status_var.set("⏳ Consultando contadores y descargando registro detallado de visitantes...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        web = fetch_hits("docente.rubenmunozdocente.digital/visitas-web")
        cv = fetch_hits("docente.rubenmunozdocente.digital/descargas-cv")
        yt_main = fetch_yt_views("hmVcdfkkZPk")
        yt_short = fetch_yt_views("Rw0hQTTwMq8")
        visitors = fetch_and_merge_visitors()
        self.root.after(0, lambda: self._update_ui(web, cv, yt_main, yt_short, visitors))

    def _update_ui(self, web, cv, yt_main, yt_short, visitors):
        now = datetime.now().strftime("%d/%m/%Y a las %H:%M:%S")
        self.status_var.set(f"✅ Conectado · Última actualización: {now}")

        self.cards["web"][0].config(text=f"{web['total']} visitas")
        self.cards["web"][1].config(text=f"Hoy: {web['today']} · 7 días: {web['weekly']}")

        self.cards["cv"][0].config(text=f"{cv['total']} descargas")
        self.cards["cv"][1].config(text=f"Hoy: {cv['today']} · 7 días: {cv['weekly']}")

        self.cards["yt_main"][0].config(text=f"{yt_main} vistas")
        self.cards["yt_main"][1].config(text="Vídeo horizontal (1:17)")

        self.cards["yt_short"][0].config(text=f"{yt_short} vistas")
        self.cards["yt_short"][1].config(text="Feed de YouTube Shorts")

        total_impact = web["total"] + yt_main + yt_short
        self.total_var.set(f"🏆 Impacto Total: {total_impact} ({web['total']} Web + {yt_main + yt_short} YouTube)")

        self.visitors = visitors
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not visitors:
            self.detail_text.set("El registro detallado ya está activo en tu web. En cuanto entre el próximo visitante aparecerán aquí su ciudad, operador/empresa, IP, origen y dispositivo.")
        else:
            for i, v in enumerate(visitors):
                self.tree.insert("", "end", iid=str(i), values=(
                    v.get("fecha", ""),
                    v.get("accion", ""),
                    v.get("ciudad", ""),
                    v.get("isp", ""),
                    v.get("origen", ""),
                    v.get("dispositivo", "")
                ))
            self.tree.selection_set("0")
            self.on_select_visitor()


if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()
