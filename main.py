#!/usr/bin/env python3
"""
Secret‑Revealer v3.0 – Full‑Profile OSINT
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

# ------------------ CONFIG (set via environment variables, not hardcoded) ------------------
# export NUMVERIFY_KEY=...    (https://numverify.com)
# export GOOGLE_API_KEY=...   (https://console.cloud.google.com, format: AIza...)
# export GOOGLE_CX=...        (Google Programmable Search Engine ID)
# export HIBP_API_KEY=...     (https://haveibeenpwned.com/API/Key - paid, required by HIBP v3)
CONFIG = {
    "numverify_key": os.environ.get("NUMVERIFY_KEY", ""),
    "google_api_key": os.environ.get("GOOGLE_API_KEY", ""),
    "google_cx": os.environ.get("GOOGLE_CX", ""),
    "hibp_api_key": os.environ.get("HIBP_API_KEY", ""),
    "tor_proxy": os.environ.get("TOR_PROXY", "socks5h://127.0.0.1:9050")
}

# ------------------ PLATFORM LIST FOR USERNAME SEARCH ------------------
PLATFORMS = [
    ("Twitter", "https://twitter.com/{}"),
    ("Instagram", "https://www.instagram.com/{}"),
    ("GitHub", "https://github.com/{}"),
    ("Reddit", "https://www.reddit.com/user/{}"),
    ("YouTube", "https://www.youtube.com/{}"),
    ("Facebook", "https://www.facebook.com/{}"),
    ("LinkedIn", "https://www.linkedin.com/in/{}"),
    ("TikTok", "https://www.tiktok.com/@{}"),
    ("Pinterest", "https://www.pinterest.com/{}"),
    ("Tumblr", "https://{}.tumblr.com"),
    ("Flickr", "https://www.flickr.com/people/{}"),
    ("Snapchat", "https://www.snapchat.com/add/{}"),
    ("Telegram", "https://t.me/{}"),
    ("Discord", "https://discord.com/users/{}"),
    ("Medium", "https://medium.com/@{}"),
    ("DeviantArt", "https://www.deviantart.com/{}"),
    ("VK", "https://vk.com/{}"),
    ("Patreon", "https://www.patreon.com/{}"),
    ("Quora", "https://www.quora.com/profile/{}"),
    ("StackOverflow", "https://stackoverflow.com/users/{}"),
    # Add more as needed
]

# ------------------ OSINT ENGINE ------------------
class OSINTEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        self.results = {}

    # ---------- PHONE ----------
    def lookup_phone(self, phone):
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
                        "international": data.get("international_format"),
                        "local": data.get("local_format")
                    }
            return None
        except:
            return None

    # ---------- EMAIL (Breaches + Gravatar) ----------
    def check_hibp(self, email):
        if not email or not CONFIG["hibp_api_key"]:
            return []
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {"hibp-api-key": CONFIG["hibp_api_key"]}
        try:
            resp = self.session.get(url, headers=headers, params={"truncateResponse": "false"}, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            # 404 = no breaches found (not an error); 401/429/etc = key or rate-limit issue
            return []
        except Exception:
            return []

    def get_gravatar(self, email):
        import hashlib
        hash_md5 = hashlib.md5(email.strip().lower().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{hash_md5}?d=404&size=200"

    # ---------- USERNAME SEARCH (check platforms) ----------
    def check_username(self, username):
        found = []
        if not username:
            return found
        for name, url_template in PLATFORMS:
            url = url_template.format(username)
            try:
                resp = self.session.get(url, timeout=5, allow_redirects=False)
                if resp.status_code == 200:
                    found.append({"platform": name, "url": url, "exists": True})
                elif resp.status_code == 404:
                    pass
                else:
                    # maybe exists but blocked
                    found.append({"platform": name, "url": url, "exists": None})
            except:
                pass
        return found

    # ---------- GOOGLE SEARCH ----------
    def google_search(self, query):
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

    # ---------- WHOIS ----------
    def whois_lookup(self, domain):
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
            return {"error": "WHOIS failed"}

    # ---------- DARK WEB (Ahmia index search) ----------
    def search_dark_web(self, query):
        """Search the Ahmia dark-web index. Ahmia (ahmia.fi) is a clearnet-searchable
        index of .onion sites that excludes abuse content; no Tor connection is
        required to query its search page, only to visit the .onion results."""
        if not query:
            return []
        results = []
        url = "https://ahmia.fi/search/"
        try:
            resp = self.session.get(url, params={"q": query}, timeout=10)
            if resp.status_code == 200:
                for m in re.finditer(
                    r'<li[^>]*class="result"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
                    r'<p[^>]*class="description"[^>]*>(.*?)</p>',
                    resp.text, re.S
                ):
                    link, title, desc = m.groups()
                    results.append({
                        "title": re.sub(r"<[^>]+>", "", title).strip(),
                        "link": link,
                        "snippet": re.sub(r"<[^>]+>", "", desc).strip()[:200]
                    })
        except Exception:
            pass
        return results[:5]

    # ---------- MAIN RUN ----------
    def run(self, data):
        result = {
            "identity": {
                "full_name": data.get("name") or "Unknown",
                "phones": [],
                "emails": [],
                "usernames": [],
                "search_results": [],
                "breaches": [],
                "whois": {},
                "dark_web": []
            },
            "score": 0.0
        }

        # 1. Phone
        phone = data.get("phone")
        if phone:
            phone_info = self.lookup_phone(phone)
            if phone_info:
                result["identity"]["phones"].append({
                    "number": phone,
                    "international": phone_info.get("international"),
                    "local": phone_info.get("local"),
                    "carrier": phone_info.get("carrier"),
                    "country": phone_info.get("country"),
                    "country_code": phone_info.get("country_code"),
                    "location": phone_info.get("location"),
                    "line_type": phone_info.get("line_type")
                })
                result["score"] += 0.2

        # 2. Email
        email = data.get("email")
        if email:
            # Breaches
            breaches = self.check_hibp(email)
            for b in breaches:
                result["identity"]["breaches"].append({
                    "source": b.get("Name"),
                    "date": b.get("BreachDate"),
                    "description": b.get("Description", "")[:150]
                })
            if breaches:
                result["score"] += 0.3
            # Gravatar
            gravatar = self.get_gravatar(email)
            result["identity"]["emails"].append({
                "address": email,
                "gravatar": gravatar,
                "source": "input"
            })

        # 3. Username (if provided, else try from email/name)
        username = data.get("username") or data.get("name")
        if username:
            found = self.check_username(username)
            result["identity"]["usernames"] = found
            result["score"] += 0.1 * min(len(found), 5)

        # 4. Google search (if name or username)
        query = data.get("name") or data.get("username")
        if query:
            items = self.google_search(query)
            if items:
                result["identity"]["search_results"] = [
                    {"title": i.get("title"), "link": i.get("link"), "snippet": i.get("snippet")}
                    for i in items[:5]
                ]
                result["score"] += 0.1

        # 5. WHOIS for domain
        domain = data.get("domain")
        if domain:
            whois_data = self.whois_lookup(domain)
            if whois_data and "error" not in whois_data:
                result["identity"]["whois"] = whois_data
                result["score"] += 0.1

        # 6. Dark web (Ahmia index search)
        dark_query = data.get("username") or data.get("email") or data.get("name")
        if dark_query:
            dark_hits = self.search_dark_web(dark_query)
            if dark_hits:
                for hit in dark_hits:
                    result["identity"]["dark_web"].append({
                        "source": "Ahmia",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "snippet": f"{hit['title']}: {hit['snippet']} ({hit['link']})"
                    })
                result["score"] += 0.1
            else:
                result["identity"]["dark_web"].append({
                    "source": "Ahmia",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "snippet": "No dark web mentions found."
                })

        result["score"] = min(result["score"] + 0.3, 1.0)
        return result

# ------------------ GUI (same layout, but with improved output) ------------------
class SecretRevealerGUI:
    # ------------------ Cyber theme palette ------------------
    BG = "#0a0e14"
    PANEL_BG = "#0d1117"
    FIELD_BG = "#161b22"
    ACCENT = "#39ff14"
    ACCENT_DIM = "#1f8f0c"
    FG = "#c9d1d9"
    FONT = ("Consolas", 10)
    FONT_BOLD = ("Consolas", 10, "bold")
    FONT_MONO = ("Consolas", 10)

    def __init__(self, root):
        self.root = root
        self.root.title("SECRET-REVEALER // OSINT TERMINAL v3.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.engine = OSINTEngine()
        self.output_data = {}
        self._apply_cyber_theme()
        self._build_menu()
        self._build_main_layout()
        self.status_var.set("READY")

    def _apply_cyber_theme(self):
        self.root.configure(bg=self.BG)
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background=self.BG, foreground=self.FG, font=self.FONT)
        style.configure('TFrame', background=self.BG)
        style.configure('TLabel', background=self.BG, foreground=self.FG, font=self.FONT)

        style.configure('TLabelframe', background=self.BG, bordercolor=self.ACCENT_DIM)
        style.configure('TLabelframe.Label', background=self.BG, foreground=self.ACCENT, font=self.FONT_BOLD)

        style.configure('TEntry', fieldbackground=self.FIELD_BG, foreground=self.ACCENT,
                         insertcolor=self.ACCENT, bordercolor=self.ACCENT_DIM)

        style.configure('TButton', background=self.FIELD_BG, foreground=self.ACCENT,
                         font=self.FONT_BOLD, bordercolor=self.ACCENT_DIM, focusthickness=0)
        style.map('TButton',
                  background=[('active', self.ACCENT)],
                  foreground=[('active', self.BG)])

        style.configure('TCheckbutton', background=self.BG, foreground=self.FG, font=self.FONT)
        style.map('TCheckbutton', background=[('active', self.BG)])

        style.configure('TNotebook', background=self.BG, bordercolor=self.ACCENT_DIM)
        style.configure('TNotebook.Tab', background=self.FIELD_BG, foreground=self.FG,
                         font=self.FONT_BOLD, padding=[12, 5])
        style.map('TNotebook.Tab',
                  background=[('selected', self.ACCENT)],
                  foreground=[('selected', self.BG)])

        style.configure('Horizontal.TProgressbar', background=self.ACCENT,
                         troughcolor=self.FIELD_BG, bordercolor=self.BG)

        style.configure('Status.TLabel', background=self.FIELD_BG, foreground=self.ACCENT, font=self.FONT)

    PLACEHOLDER_COLOR = '#4d5566'

    def _add_placeholder(self, entry, text):
        entry._placeholder = text
        entry.insert(0, text)
        entry.configure(foreground=self.PLACEHOLDER_COLOR)
        entry.bind('<FocusIn>', lambda e, ent=entry: self._clear_placeholder(ent))
        entry.bind('<FocusOut>', lambda e, ent=entry: self._restore_placeholder(ent))

    def _clear_placeholder(self, entry):
        if entry.get() == entry._placeholder:
            entry.delete(0, tk.END)
            entry.configure(foreground=self.ACCENT)

    def _restore_placeholder(self, entry):
        if not entry.get():
            entry.insert(0, entry._placeholder)
            entry.configure(foreground=self.PLACEHOLDER_COLOR)

    def _entry_value(self, entry):
        val = entry.get().strip()
        return '' if val == getattr(entry, '_placeholder', None) else val

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export JSON", command=self.export_json)
        file_menu.add_command(label="Export HTML", command=self.export_html)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)

    def _build_main_layout(self):
        header = tk.Label(self.root, text="[ SECRET-REVEALER // OSINT TERMINAL ]",
                           bg=self.BG, fg=self.ACCENT, font=("Consolas", 16, "bold"),
                           anchor=tk.W, padx=15, pady=8)
        header.pack(side=tk.TOP, fill=tk.X)

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # Left panel
        left = ttk.LabelFrame(main, text="Search Target", padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))

        ttk.Label(left, text="Full Name:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.name_entry = ttk.Entry(left, width=30)
        self.name_entry.grid(row=0, column=1, pady=3)
        self._add_placeholder(self.name_entry, "e.g. Jane Doe")

        ttk.Label(left, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.email_entry = ttk.Entry(left, width=30)
        self.email_entry.grid(row=1, column=1, pady=3)
        self._add_placeholder(self.email_entry, "e.g. jane@example.com")

        ttk.Label(left, text="Phone:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.phone_entry = ttk.Entry(left, width=30)
        self.phone_entry.grid(row=2, column=1, pady=3)
        self._add_placeholder(self.phone_entry, "e.g. +1 555 0100")

        ttk.Label(left, text="Username:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.username_entry = ttk.Entry(left, width=30)
        self.username_entry.grid(row=3, column=1, pady=3)
        self._add_placeholder(self.username_entry, "e.g. janedoe")

        ttk.Label(left, text="Domain:").grid(row=4, column=0, sticky=tk.W, pady=3)
        self.domain_entry = ttk.Entry(left, width=30)
        self.domain_entry.grid(row=4, column=1, pady=3)
        self._add_placeholder(self.domain_entry, "e.g. example.com")

        btn_frame = ttk.Frame(left)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="▶ RUN SCAN", command=self.run_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✕ CLEAR", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        # Right panel
        right = ttk.LabelFrame(main, text="Results", padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        notebook = ttk.Notebook(right)
        notebook.pack(fill=tk.BOTH, expand=True)

        text_opts = dict(wrap=tk.WORD, height=20, bg="#010409", fg=self.ACCENT,
                          insertbackground=self.ACCENT, selectbackground=self.ACCENT_DIM,
                          selectforeground=self.BG, font=self.FONT_MONO,
                          borderwidth=0, highlightthickness=1,
                          highlightbackground=self.ACCENT_DIM, highlightcolor=self.ACCENT)

        self.summary_text = scrolledtext.ScrolledText(notebook, **text_opts)
        self.summary_text.tag_configure('title', foreground=self.ACCENT, font=self.FONT_BOLD)
        self.summary_text.tag_configure('score_high', foreground='#39ff14', font=self.FONT_BOLD)
        self.summary_text.tag_configure('score_mid', foreground='#f5d90a', font=self.FONT_BOLD)
        self.summary_text.tag_configure('score_low', foreground='#ff4136', font=self.FONT_BOLD)
        self.summary_text.tag_configure('section', foreground='#58a6ff', font=self.FONT_BOLD)
        notebook.add(self.summary_text, text="📊 Summary")

        self.json_text = scrolledtext.ScrolledText(notebook, **text_opts)
        notebook.add(self.json_text, text="📄 Full JSON")

        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W,
                                style='Status.TLabel', padding=(8, 3))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)

    def run_scan(self):
        data = {
            'name': self._entry_value(self.name_entry),
            'email': self._entry_value(self.email_entry),
            'phone': self._entry_value(self.phone_entry),
            'username': self._entry_value(self.username_entry),
            'domain': self._entry_value(self.domain_entry)
        }
        if not any(data.values()):
            messagebox.showwarning("Input", "Enter at least one identifier.")
            return
        self.progress.start()
        self.status_var.set(">> SCANNING...")
        thread = threading.Thread(target=self._scan_thread, args=(data,))
        thread.daemon = True
        thread.start()

    def _scan_thread(self, data):
        try:
            result = self.engine.run(data)
            self.output_data = result
            self.root.after(0, self._update_results, result)
        except Exception as e:
            self.root.after(0, self._show_error, str(e))
        finally:
            self.root.after(0, self._scan_done)

    def _update_results(self, result):
        identity = result.get('identity', {})
        st = self.summary_text
        st.delete(1.0, tk.END)

        st.insert(tk.END, "=== SECRET-REVEALER v3.0 REPORT ===\n\n", 'title')

        score_pct = result.get('score', 0) * 100
        score_tag = 'score_high' if score_pct >= 70 else 'score_mid' if score_pct >= 40 else 'score_low'
        st.insert(tk.END, "Score: ")
        st.insert(tk.END, f"{score_pct:.1f}%\n", score_tag)
        st.insert(tk.END, f"Name: {identity.get('full_name', 'N/A')}\n")

        phones = identity.get('phones', [])
        if phones:
            st.insert(tk.END, "\n📞 Phones\n", 'section')
            for p in phones:
                st.insert(tk.END, f"   {p.get('number')} – Carrier: {p.get('carrier')}, Country: {p.get('country')}\n")

        emails = identity.get('emails', [])
        if emails:
            st.insert(tk.END, "\n📧 Emails\n", 'section')
            for e in emails:
                st.insert(tk.END, f"   {e.get('address')} (Gravatar: {e.get('gravatar')})\n")

        usernames = identity.get('usernames', [])
        if usernames:
            st.insert(tk.END, "\n👤 Usernames found\n", 'section')
            for u in usernames:
                status = "✅" if u.get('exists') else "❌"
                st.insert(tk.END, f"   {status} {u.get('platform')}: {u.get('url')}\n")

        breaches = identity.get('breaches', [])
        if breaches:
            st.insert(tk.END, "\n🔓 Breaches\n", 'section')
            for b in breaches:
                st.insert(tk.END, f"   {b.get('source')} ({b.get('date')})\n")

        search = identity.get('search_results', [])
        if search:
            st.insert(tk.END, "\n🔍 Web Search\n", 'section')
            for s in search:
                st.insert(tk.END, f"   {s.get('title')}: {s.get('link')}\n")

        whois = identity.get('whois', {})
        if whois and 'error' not in whois:
            st.insert(tk.END, "\n🌐 WHOIS\n", 'section')
            st.insert(tk.END, f"   Registrar: {whois.get('registrar')}\n")

        dark = identity.get('dark_web', [])
        if dark:
            st.insert(tk.END, "\n🌑 Dark Web\n", 'section')
            for d in dark:
                st.insert(tk.END, f"   [{d.get('source')}] {d.get('snippet')}\n")

        self.json_text.delete(1.0, tk.END)
        self.json_text.insert(tk.END, json.dumps(result, indent=2))

    def _show_error(self, msg):
        messagebox.showerror("Error", msg)
        self.status_var.set("!! ERROR")
    def _scan_done(self):
        self.progress.stop()
        self.status_var.set("READY")
    def clear_fields(self):
        for e in [self.name_entry, self.email_entry, self.phone_entry, self.username_entry, self.domain_entry]:
            e.delete(0, tk.END)
            self._restore_placeholder(e)
        self.summary_text.delete(1.0, tk.END)
        self.json_text.delete(1.0, tk.END)
        self.output_data = {}
        self.status_var.set("CLEARED")
    def export_json(self):
        if not self.output_data:
            messagebox.showwarning("Export", "No data.")
            return
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if f:
            with open(f, 'w') as fp:
                json.dump(self.output_data, fp, indent=2)
    def export_html(self):
        if not self.output_data:
            messagebox.showwarning("Export", "No data.")
            return
        f = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
        if f:
            html = f"<html><head><title>Secret‑Revealer Report</title></head><body><pre>{json.dumps(self.output_data, indent=2)}</pre></body></html>"
            with open(f, 'w') as fp:
                fp.write(html)
    def show_about(self):
        messagebox.showinfo("About", "Secret‑Revealer v3.0\nFull OSINT Engine\nAuthor: CAT\n\nSearches: Phone, Email, Username, Name, Domain.\nUses numverify, HaveIBeenPwned, Google CSE, WHOIS, and platform checks.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SecretRevealerGUI(root)
    root.mainloop()
