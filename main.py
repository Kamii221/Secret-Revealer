#!/usr/bin/env python3
"""
Secret‑Revealer v2.0 – Red Team Intelligence Engine
Author: CAT (Interdimensional Coding Champion)
Description: Single‑file OSINT GUI with mock dark‑web and breach modules.
             Replace mock engine with real APIs for production.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import time
import random
import os
from datetime import datetime

# ------------------ ASCII BANNER ------------------
BANNER = r"""
   _____                       _    _____                     _           
  / ____|                     | |  |  __ \                   | |          
 | (___   ___  ___  ___ _ __  | |  | |__) |___  ___  ___  __| | ___ _ __ 
  \___ \ / _ \/ _ \/ _ \ '_ \ | |  |  _  // _ \/ _ \/ _ \/ _` |/ _ \ '__|
  ____) |  __/  __/  __/ | | || |  | | \ \  __/  __/  __/ (_| |  __/ |   
 |_____/ \___|\___|\___|_| |_||_|  |_|  \_\___|\___|\___|\__,_|\___|_|   
                                                                          
  Secret‑Revealer – Uncover the truth.
"""

# ------------------ CONFIGURATION ------------------
CONFIG = {
    "tor_proxy": "socks5h://127.0.0.1:9050",
    "modules": {
        "clearnet": ["google", "linkedin", "twitter", "github", "shodan"],
        "darkweb": ["ahmia", "dark_paste", "breach_forums"],
        "enrichment": ["haveibeenpwned", "dehashed", "geoip"]
    }
}

# ------------------ MOCK OSINT ENGINE ------------------
class SecretRevealerEngine:
    """Mock OSINT engine – replace with real modules."""
    def run(self, data, modules=None):
        # Simulate scanning delay
        time.sleep(random.uniform(1.5, 3.0))

        # Build synthetic result
        result = {
            "identity": {
                "full_name": data.get("name") or "Unknown",
                "aliases": [data.get("name", "") + " (alias)"] if data.get("name") else [],
                "emails": [
                    {"address": data.get("email") or "unknown@example.com", "source": "input", "confidence": 1.0}
                ],
                "phones": [
                    {"number": data.get("phone") or "+1-555-0000", "carrier": "Mock Carrier", "confidence": 0.8}
                ],
                "addresses": ["123 Mock Street, City, Country"],
                "social": {
                    "twitter": data.get("username", "") or "mockuser",
                    "linkedin": data.get("username", "") + "-linked" if data.get("username") else "",
                    "github": data.get("username", "") + "-git" if data.get("username") else ""
                },
                "breaches": [
                    {"source": "Example Breach 1", "date": "2020-01-01", "password_hash": "mockhash1"},
                    {"source": "Example Breach 2", "date": "2021-06-15", "password_hash": "mockhash2"}
                ],
                "dark_web_mentions": []
            },
            "score": random.uniform(0.7, 0.95)
        }

        # Dark web module
        if modules and ("darkweb" in str(modules) or "ahmia" in str(modules)):
            result["identity"]["dark_web_mentions"].append({
                "source": "Ahmia (mock)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "snippet": f"Found reference to {data.get('username', 'user')} on a dark forum."
            })

        # Enrichment
        if modules and "dehashed" in str(modules):
            result["identity"]["breaches"].append({
                "source": "Dehashed (mock)",
                "date": "2022-08-10",
                "password_hash": "mocked_hash"
            })

        return result

# ------------------ GUI APPLICATION ------------------
class SecretRevealerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secret‑Revealer v2.0 – Red Team Intelligence")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Show banner in console
        print(BANNER)

        self.engine = SecretRevealerEngine()
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
        settings_menu.add_command(label="Configure Proxy", command=self.open_settings)
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
        ttk.Checkbutton(left_frame, text="Clearnet", variable=self.clearnet_var).grid(row=7, column=0, sticky=tk.W)
        ttk.Checkbutton(left_frame, text="Dark Web", variable=self.darkweb_var).grid(row=7, column=1, sticky=tk.W)
        ttk.Checkbutton(left_frame, text="Enrichment", variable=self.enrich_var).grid(row=8, column=0, columnspan=2, sticky=tk.W)

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
            modules.extend(CONFIG["modules"]["clearnet"])
        if self.darkweb_var.get():
            modules.extend(CONFIG["modules"]["darkweb"])
        if self.enrich_var.get():
            modules.extend(CONFIG["modules"]["enrichment"])

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
        summary += f"Confidence Score: {result.get('score', 0)*100:.1f}%\n"
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
        messagebox.showinfo("Settings", "Settings dialog (mock) – configure proxy, API keys, etc.")

    def toggle_tor(self):
        current = self.status_var.get()
        self.status_var.set("Tor toggled (mock)" if "Tor" not in current else "Tor disabled (mock)")

    def show_about(self):
        messagebox.showinfo("About Secret‑Revealer",
            "Secret‑Revealer v2.0\n"
            "Red Team Intelligence Engine\n"
            "Author: CAT (Interdimensional Coding Champion)\n"
            "License: For authorized use only.\n\n"
            "This tool aggregates publicly available information.\n"
            "Use responsibly and ethically."
        )

# ------------------ MAIN ENTRY ------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SecretRevealerGUI(root)
    root.mainloop()
