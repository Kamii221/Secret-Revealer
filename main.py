#!/usr/bin/env python3
"""
Secret‑Revealer v2.1 – Real OSINT Intelligence Engine
Integrates:
- HaveIBeenPwned (breach lookup)
- numverify (phone carrier & location)
- Google Custom Search (public profile search)
- WHOIS (domain registrar info)
- Tor placeholder for dark web (you can connect Ahmia or OnionSearch)
Author: CAT
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import time
import requests
import re
from datetime import datetime
import os
import sys

# ------------------ CONFIGURATION (Add Your API Keys) ------------------
CONFIG = {
    "hibp_api_key": "",           # optional, but helps with rate limits
    "numverify_key": "2b14cc0a151004df6507b96fcb275535",          # get from numverify.com (free tier: 250/month)
    "google_api_key": "",         # Google Custom Search API key
    "google_cx": "",              # Google Custom Search engine ID
    "tor_proxy": "socks5h://127.0.0.1:9050"
}

# ------------------ REAL OSINT ENGINE ------------------
class RealOSINTEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Secret-Revealer/2.1"})

    def check_hibp(self, email):
        """Check if email appears in known breaches via HaveIBeenPwned"""
        if not email:
            return []
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {"hibp-api-key": CONFIG["hibp_api_key"]} if CONFIG["hibp_api_key"] else {}
        try:
            resp = self.session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return []
            else:
                return []
        except:
            return []

    def lookup_phone(self, phone):
        """Get carrier, country, location via numverify (free tier)"""
        if not phone or not CONFIG["numverify_key"]:
            return None
        url = f"http://apilayer.net/api/validate?access_key={CONFIG['numverify_key']}&number={phone}"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid"):
                    return {
                        "country": data.get("country_name"),
                        "carrier": data.get("carrier"),
                        "location": data.get("location"),
                        "line_type": data.get("line_type")
                    }
            return None
        except:
            return None

    def google_search(self, query):
        """Search for public profiles using Google Custom Search"""
        if not CONFIG["google_api_key"] or not CONFIG["google_cx"] or not query:
            return []
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": CONFIG["google_api_key"],
            "cx": CONFIG["google_cx"],
            "q": query,
            "num": 5
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("items", [])
            return []
        except:
            return []

    def whois_lookup(self, domain):
        """Simple WHOIS using python-whois if installed, else mock"""
        try:
            import whois
            w = whois.whois(domain)
            return {
                "registrar": w.registrar,
                "creation_date": str(w.creation_date),
                "expiration_date": str(w.expiration_date),
                "name_servers": w.name_servers
            }
        except:
            return {"error": "WHOIS lookup failed (install python-whois or check domain)"}

    def run(self, data, modules=None):
        result = {
            "identity": {
                "full_name": data.get("name") or "Unknown",
                "aliases": [],
                "emails": [],
                "phones": [],
                "addresses": [],
                "social": {},
                "breaches": [],
                "dark_web_mentions": [],
                "search_results": []
            },
            "score": 0.0
        }

        modules = modules or []

        # 1. Email breach check (Enrichment)
        email = data.get("email")
        if email and ("enrichment" in str(modules) or "haveibeenpwned" in str(modules)):
            breaches = self.check_hibp(email)
            for b in breaches:
                result["identity"]["breaches"].append({
                    "source": b.get("Name"),
                    "date": b.get("BreachDate"),
                    "description": b.get("Description", "")[:100]
                })
            if breaches:
                result["score"] += 0.2
                result["identity"]["emails"].append({
                    "address": email,
                    "source": "HaveIBeenPwned",
                    "confidence": 0.95
                })

        # 2. Phone lookup (Clearnet)
        phone = data.get("phone")
        if phone and ("clearnet" in str(modules) or "numverify" in str(modules)):
            phone_info = self.lookup_phone(phone)
            if phone_info:
                result["identity"]["phones"].append({
                    "number": phone,
                    "carrier": phone_info.get("carrier"),
                    "country": phone_info.get("country"),
                    "location": phone_info.get("location"),
                    "line_type": phone_info.get("line_type"),
                    "confidence": 0.9
                })
                result["score"] += 0.1

        # 3. Google search for username/name (Clearnet)
        query = data.get("username") or data.get("name")
        if query and ("clearnet" in str(modules) or "google" in str(modules)):
            items = self.google_search(query)
            if items:
                result["identity"]["search_results"] = [
                    {"title": i.get("title"), "link": i.get("link"), "snippet": i.get("snippet")}
                    for i in items[:5]
                ]
                result["score"] += 0.1

        # 4. WHOIS for domain (Enrichment)
        domain = data.get("domain")
        if domain and ("enrichment" in str(modules) or "whois" in str(modules)):
            whois_data = self.whois_lookup(domain)
            if whois_data and "error" not in whois_data:
                result["identity"]["addresses"].append(f"Domain: {domain} – Registrar: {whois_data.get('registrar')}")
                result["score"] += 0.1

        # 5. Dark web (placeholder – integrate Tor/Ahmia here)
        if "darkweb" in str(modules):
            result["identity"]["dark_web_mentions"].append({
                "source": "⚠️ Dark Web (not yet integrated – connect Tor + Ahmia)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "snippet": "To enable real dark web, install Tor, run it, and add Ahmia/OnionSearch API calls."
            })

        # Normalize score to 0-1
        result["score"] = min(result["score"] + 0.5, 1.0)
        return result

# ------------------ GUI APPLICATION ------------------
class SecretRevealerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secret‑Revealer v2.1 – Real OSINT Intelligence")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        self.engine = RealOSINTEngine()
        self.output_data = {}

        self._build_menu()
        self._build_main_layout()
        self.status_var.set("Ready")

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Targets (CSV)", command=self.load_targets)
        file_menu.add_command(label="Export Report (JSON)", command=self.export_json)
        file_menu.add_command(label="Export Report (HTML)", command=self.export_html)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Configure API Keys", command=self.open_settings)
        settings_menu.add_command(label="Toggle Tor (mock)", command=self.toggle_tor)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_main_layout(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel: Input
        left_frame = ttk.LabelFrame(main_frame, text="Search Target", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(left_frame, text="Full Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(left_frame, width=30)
        self.name_entry.grid(row=0, column=1, pady=5)

        ttk.Label(left_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_entry = ttk.Entry(left_frame, width=30)
        self.email_entry.grid(row=1, column=1, pady=5)

        ttk.Label(left_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.phone_entry = ttk.Entry(left_frame, width=30)
        self.phone_entry.grid(row=2, column=1, pady=5)

        ttk.Label(left_frame, text="Username:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(left_frame, width=30)
        self.username_entry.grid(row=3, column=1, pady=5)

        ttk.Label(left_frame, text="Company:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.company_entry = ttk.Entry(left_frame, width=30)
        self.company_entry.grid(row=4, column=1, pady=5)

        ttk.Label(left_frame, text="Domain:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.domain_entry = ttk.Entry(left_frame, width=30)
        self.domain_entry.grid(row=5, column=1, pady=5)

        # Module toggles
        ttk.Label(left_frame, text="Modules:", font=("Arial", 10, "bold")).grid(row=6, column=0, columnspan=2, pady=(10,5), sticky=tk.W)
        self.clearnet_var = tk.IntVar(value=1)
        self.darkweb_var = tk.IntVar(value=1)
        self.enrich_var = tk.IntVar(value=1)
        ttk.Checkbutton(left_frame, text="Clearnet (Google, Phone)", variable=self.clearnet_var).grid(row=7, column=0, sticky=tk.W)
        ttk.Checkbutton(left_frame, text="Dark Web (mock)", variable=self.darkweb_var).grid(row=7, column=1, sticky=tk.W)
        ttk.Checkbutton(left_frame, text="Enrichment (Breach, WHOIS)", variable=self.enrich_var).grid(row=8, column=0, columnspan=2, sticky=tk.W)

        # Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="🔍 Run Scan", command=self.run_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        # Right panel: Results Notebook
        right_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab: Summary
        self.summary_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=20)
        self.notebook.add(self.summary_text, text="📊 Summary")

        # Tab: JSON
        self.json_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=20)
        self.notebook.add(self.json_text, text="📄 Detailed JSON")

        # Tab: Dark Web
        self.dark_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=20)
        self.notebook.add(self.dark_text, text="🌑 Dark Web")

        # Tab: Graph (placeholder)
        self.graph_canvas = tk.Canvas(self.notebook, bg='white')
        self.notebook.add(self.graph_canvas, text="📈 Graph")

        # Status bar & progress
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)

    # ---------- Event Handlers ----------
    def run_scan(self):
        data = {
            'name': self.name_entry.get().strip(),
            'email': self.email_entry.get().strip(),
            'phone': self.phone_entry.get().strip(),
            'username': self.username_entry.get().strip(),
            'company': self.company_entry.get().strip(),
            'domain': self.domain_entry.get().strip()
        }
        if not any(data.values()):
            messagebox.showwarning("Input", "Please provide at least one identifier.")
            return

        modules = []
        if self.clearnet_var.get():
            modules.extend(["google", "numverify"])
        if self.darkweb_var.get():
            modules.append("darkweb")
        if self.enrich_var.get():
            modules.extend(["haveibeenpwned", "whois"])

        self.progress.start()
        self.status_var.set("Scanning...")
        thread = threading.Thread(target=self._scan_thread, args=(data, modules))
        thread.daemon = True
        thread.start()

    def _scan_thread(self, data, modules):
        try:
            result = self.engine.run(data, modules=modules)
            self.output_data = result
            self.root.after(0, self._update_results, result)
        except Exception as e:
            self.root.after(0, self._show_error, str(e))
        finally:
            self.root.after(0, self._scan_done)

    def _update_results(self, result):
        identity = result.get('identity', {})
        summary = f"=== Secret‑Revealer Report ===\n"
        summary += f"Identity: {identity.get('full_name', 'N/A')}\n"
        summary += f"Emails: {len(identity.get('emails', []))}\n"
        summary += f"Phones: {len(identity.get('phones', []))}\n"
        summary += f"Breaches: {len(identity.get('breaches', []))}\n"
        summary += f"Dark Web Mentions: {len(identity.get('dark_web_mentions', []))}\n"
        summary += f"Search Results: {len(identity.get('search_results', []))}\n"
        summary += f"Confidence Score: {result.get('score', 0)*100:.1f}%\n\n"
        # Add phone details
        for p in identity.get('phones', []):
            summary += f"Phone: {p.get('number')} – Carrier: {p.get('carrier')}, Country: {p.get('country')}\n"
        # Add breaches
        for b in identity.get('breaches', []):
            summary += f"Breach: {b.get('source')} ({b.get('date')})\n"
        # Add search results
        for s in identity.get('search_results', []):
            summary += f"Search: {s.get('title')} – {s.get('link')}\n"

        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)

        self.json_text.delete(1.0, tk.END)
        self.json_text.insert(tk.END, json.dumps(result, indent=2))

        dark = identity.get('dark_web_mentions', [])
        if dark:
            dark_str = "🌑 Dark Web Mentions:\n"
            for item in dark:
                dark_str += f"- Source: {item.get('source')}, Date: {item.get('date')}\n  Snippet: {item.get('snippet', '')[:200]}...\n"
        else:
            dark_str = "No dark web mentions found."
        self.dark_text.delete(1.0, tk.END)
        self.dark_text.insert(tk.END, dark_str)

        self.graph_canvas.delete("all")
        self.graph_canvas.create_text(10, 10, anchor=tk.NW, text="Graph visualization (mock) – shows connections between entities.", fill='black')

    def _show_error(self, msg):
        messagebox.showerror("Error", f"Scan failed: {msg}")
        self.status_var.set("Error")

    def _scan_done(self):
        self.progress.stop()
        self.status_var.set("Ready")

    def clear_fields(self):
        for entry in [self.name_entry, self.email_entry, self.phone_entry, self.username_entry, self.company_entry, self.domain_entry]:
            entry.delete(0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        self.json_text.delete(1.0, tk.END)
        self.dark_text.delete(1.0, tk.END)
        self.graph_canvas.delete("all")
        self.output_data = {}
        self.status_var.set("Cleared")

    # ---------- Menu Actions ----------
    def load_targets(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filepath:
            messagebox.showinfo("Load", f"CSV loaded from {filepath}\n(Feature stub)")

    def export_json(self):
        if not self.output_data:
            messagebox.showwarning("Export", "No data to export. Run a scan first.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(self.output_data, f, indent=2)
            self.status_var.set(f"Exported to {os.path.basename(filepath)}")

    def export_html(self):
        if not self.output_data:
            messagebox.showwarning("Export", "No data to export. Run a scan first.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html")])
        if filepath:
            html = f"<html><head><title>Secret‑Revealer Report</title></head><body><pre>{json.dumps(self.output_data, indent=2)}</pre></body></html>"
            with open(filepath, 'w') as f:
                f.write(html)
            self.status_var.set(f"Exported to {os.path.basename(filepath)}")

    def open_settings(self):
        messagebox.showinfo("Settings", 
            "Add your API keys in the CONFIG dictionary inside the script:\n"
            "numverify_key = get from numverify.com (free)\n"
            "google_api_key and google_cx from Google Custom Search\n"
            "hibp_api_key optional\n\n"
            "For WHOIS, install python-whois: pip install python-whois")

    def toggle_tor(self):
        current = self.status_var.get()
        self.status_var.set("Tor toggled (mock)" if "Tor" not in current else "Tor disabled (mock)")

    def show_about(self):
        messagebox.showinfo("About Secret‑Revealer",
            "Secret‑Revealer v2.1\n"
            "Real OSINT Intelligence Engine\n"
            "Author: CAT\n"
            "License: For authorised use only.\n\n"
            "Integrates:\n"
            "- HaveIBeenPwned (breaches)\n"
            "- numverify (phone lookup)\n"
            "- Google Custom Search (public profiles)\n"
            "- WHOIS (domain info)\n"
            "- Dark web (placeholder for Tor)\n\n"
            "You need API keys for full functionality."
        )

# ------------------ MAIN ENTRY ------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SecretRevealerGUI(root)
    root.mainloop()
