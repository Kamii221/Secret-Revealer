#!/usr/bin/env python3
"""
Secret‑Revealer v2.2 – Full OSINT Engine with Phone, Breach, Search
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

# ------------------ CONFIGURATION ------------------
CONFIG = {
    "numverify_key": "2b14cc0a151004df6507b96fcb275535",   # YOUR KEY
    "hibp_api_key": "",                                    # optional
    "google_api_key": "",                                  # get from Google
    "google_cx": "",                                       # Google CSE ID
    "tor_proxy": "socks5h://127.0.0.1:9050"
}

# ------------------ REAL OSINT ENGINE ------------------
class RealOSINTEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Secret-Revealer/2.2"})

    # ---------- PHONE LOOKUP (numverify) ----------
    def lookup_phone(self, phone):
        """Get carrier, country, location via numverify."""
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
                        "country_code": data.get("country_code"),
                        "carrier": data.get("carrier"),
                        "location": data.get("location"),
                        "line_type": data.get("line_type"),
                        "international_format": data.get("international_format"),
                        "local_format": data.get("local_format")
                    }
            return None
        except Exception as e:
            return {"error": str(e)}

    # ---------- BREACH CHECK (HaveIBeenPwned) ----------
    def check_hibp(self, email):
        """Check if email appears in known breaches."""
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

    # ---------- GOOGLE SEARCH ----------
    def google_search(self, query):
        """Search public profiles using Google Custom Search."""
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

    # ---------- MAIN RUN METHOD ----------
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

        # 1. Phone lookup (Clearnet)
        phone = data.get("phone")
        if phone and ("clearnet" in str(modules) or "numverify" in str(modules)):
            phone_info = self.lookup_phone(phone)
            if phone_info and "error" not in phone_info:
                result["identity"]["phones"].append({
                    "number": phone,
                    "international": phone_info.get("international_format"),
                    "local": phone_info.get("local_format"),
                    "carrier": phone_info.get("carrier"),
                    "country": phone_info.get("country"),
                    "country_code": phone_info.get("country_code"),
                    "location": phone_info.get("location"),
                    "line_type": phone_info.get("line_type"),
                    "confidence": 0.9
                })
                result["score"] += 0.2

        # 2. Email breach check (Enrichment)
        email = data.get("email")
        if email and ("enrichment" in str(modules) or "haveibeenpwned" in str(modules)):
            breaches = self.check_hibp(email)
            for b in breaches:
                result["identity"]["breaches"].append({
                    "source": b.get("Name"),
                    "date": b.get("BreachDate"),
                    "description": b.get("Description", "")[:150]
                })
            if breaches:
                result["score"] += 0.3
                result["identity"]["emails"].append({
                    "address": email,
                    "source": "HaveIBeenPwned",
                    "confidence": 0.95
                })

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

        # 4. Dark web (placeholder – connect Tor + Ahmia here)
        if "darkweb" in str(modules):
            result["identity"]["dark_web_mentions"].append({
                "source": "⚠️ Dark Web (pending Tor + Ahmia integration)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "snippet": "To enable real dark web, install Tor, run it, and add Ahmia/OnionSearch API calls."
            })

        # Normalise score to 0-1
        result["score"] = min(result["score"] + 0.4, 1.0)
        return result

# ------------------ GUI ------------------
class SecretRevealerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secret‑Revealer v2.2 – Full OSINT Engine")
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
        settings_menu.add_command(label="API Keys / Settings", command=self.open_settings)
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
        ttk.Checkbutton(left_frame, text="Clearnet (Phone, Google)", variable=self.clearnet_var).grid(row=7, column=0, sticky=tk.W)
        ttk.Checkbutton(left_frame, text="Dark Web (mock)", variable=self.darkweb_var).grid(row=7, column=1, sticky=tk.W)
        ttk.Checkbutton(left_frame, text="Enrichment (Breaches)", variable=self.enrich_var).grid(row=8, column=0, columnspan=2, sticky=tk.W)

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

        # Tab: Graph
        self.graph_canvas = tk.Canvas(self.notebook, bg='white')
        self.notebook.add(self.graph_canvas, text="📈 Graph")

        # Status bar & progress
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)

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
            modules.extend(["numverify", "google"])
        if self.darkweb_var.get():
            modules.append("darkweb")
        if self.enrich_var.get():
            modules.append("haveibeenpwned")

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
        summary = f"=== Secret‑Revealer Report ===\n\n"
        summary += f"Identity: {identity.get('full_name', 'N/A')}\n"
        summary += f"Score: {result.get('score', 0)*100:.1f}%\n"
        summary += f"Emails: {len(identity.get('emails', []))}\n"
        summary += f"Phones: {len(identity.get('phones', []))}\n"
        summary += f"Breaches: {len(identity.get('breaches', []))}\n"
        summary += f"Search Results: {len(identity.get('search_results', []))}\n"

        # Phone details
        for p in identity.get('phones', []):
            summary += f"\n📞 Phone: {p.get('number')}\n"
            summary += f"   Carrier: {p.get('carrier')}\n"
            summary += f"   Country: {p.get('country')} ({p.get('country_code')})\n"
            summary += f"   Type: {p.get('line_type')}\n"

        # Breaches
        for b in identity.get('breaches', []):
            summary += f"\n🔓 Breach: {b.get('source')} ({b.get('date')})\n"
            summary += f"   {b.get('description', '')[:100]}\n"

        # Search results
        for s in identity.get('search_results', []):
            summary += f"\n🔍 Search: {s.get('title')}\n"
            summary += f"   {s.get('link')}\n"

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
        self.graph_canvas.create_text(10, 10, anchor=tk.NW, text="Graph: Identity connections (mock).", fill='black')

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

    def load_targets(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if filepath:
            messagebox.showinfo("Load", f"CSV loaded from {filepath} (stub)")

    def export_json(self):
        if not self.output_data:
            messagebox.showwarning("Export", "No data to export.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(self.output_data, f, indent=2)
            self.status_var.set(f"Exported to {os.path.basename(filepath)}")

    def export_html(self):
        if not self.output_data:
            messagebox.showwarning("Export", "No data to export.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML files", "*.html")])
        if filepath:
            html = f"<html><head><title>Secret‑Revealer Report</title></head><body><pre>{json.dumps(self.output_data, indent=2)}</pre></body></html>"
            with open(filepath, 'w') as f:
                f.write(html)
            self.status_var.set(f"Exported to {os.path.basename(filepath)}")

    def open_settings(self):
        messagebox.showinfo("Settings", 
            "Your numverify key is set.\n"
            "To add Google Search, get a Custom Search API key and CX ID.\n"
            "For HaveIBeenPwned, add your API key (optional).\n"
            "Dark web requires Tor + Ahmia integration.")

    def toggle_tor(self):
        self.status_var.set("Tor toggled (mock)")

    def show_about(self):
        messagebox.showinfo("About Secret‑Revealer",
            "Secret‑Revealer v2.2\n"
            "Full OSINT Intelligence Engine\n"
            "Author: CAT\n\n"
            "Features:\n"
            "✅ Phone: Carrier, Country, Location (numverify)\n"
            "✅ Email: Breach lookup (HaveIBeenPwned)\n"
            "✅ Search: Public profiles (Google CSE)\n"
            "⏳ Dark Web: Pending Tor + Ahmia\n\n"
            "For authorised use only."
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = SecretRevealerGUI(root)
    root.mainloop()
