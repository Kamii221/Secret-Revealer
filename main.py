#!/usr/bin/env python3
"""
Secret‑Revealer v2.3 – Full OSINT Engine (Phone, Breaches, Search, WHOIS)
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

# ------------------ CONFIGURATION (Your Keys Here) ------------------
CONFIG = {
    "numverify_key": "2b14cc0a151004df6507b96fcb275535",   # YOUR KEY
    "hibp_api_key": "",                                    # optional
    "google_api_key": "AQ.Ab8RN6I6sLKz3NQdXAu2JfwP3BU6PgDuN-lj2ULbmWYLincKDg",                    
    "google_cx": "0536e286037c942e3",                 
    "tor_proxy": "socks5h://127.0.0.1:9050"
}

# ------------------ REAL OSINT ENGINE ------------------
class RealOSINTEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Secret-Revealer/2.3"})

    # ---------- PHONE LOOKUP (numverify) ----------
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

    # ---------- BREACH CHECK (HaveIBeenPwned) ----------
    def check_hibp(self, email):
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

    # ---------- GOOGLE SEARCH (Custom Search) ----------
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

    # ---------- WHOIS LOOKUP ----------
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
            return {"error": "WHOIS failed (install python-whois)"}

    # ---------- MAIN RUN ----------
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
                "search_results": [],
                "whois": {}
            },
            "score": 0.0
        }

        modules = modules or []

        # 1. Phone
        phone = data.get("phone")
        if phone and ("clearnet" in str(modules) or "numverify" in str(modules)):
            info = self.lookup_phone(phone)
            if info:
                result["identity"]["phones"].append({
                    "number": phone,
                    "international": info.get("international"),
                    "local": info.get("local"),
                    "carrier": info.get("carrier"),
                    "country": info.get("country"),
                    "country_code": info.get("country_code"),
                    "location": info.get("location"),
                    "line_type": info.get("line_type"),
                    "confidence": 0.9
                })
                result["score"] += 0.2

        # 2. Email breaches
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

        # 3. Google search for name/username
        query = data.get("username") or data.get("name")
        if query and ("clearnet" in str(modules) or "google" in str(modules)):
            items = self.google_search(query)
            if items:
                result["identity"]["search_results"] = [
                    {"title": i.get("title"), "link": i.get("link"), "snippet": i.get("snippet")}
                    for i in items[:5]
                ]
                result["score"] += 0.1

        # 4. WHOIS for domain
        domain = data.get("domain")
        if domain and ("enrichment" in str(modules) or "whois" in str(modules)):
            whois_data = self.whois_lookup(domain)
            if whois_data and "error" not in whois_data:
                result["identity"]["whois"] = whois_data
                result["score"] += 0.1

        # 5. Dark web placeholder
        if "darkweb" in str(modules):
            result["identity"]["dark_web_mentions"].append({
                "source": "⚠️ Dark Web (Tor + Ahmia integration ready)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "snippet": "To enable, install Tor, run 'sudo systemctl start tor', then add Ahmia/OnionSearch API calls."
            })

        result["score"] = min(result["score"] + 0.3, 1.0)
        return result

# ------------------ GUI (same as before, but now shows everything) ------------------
class SecretRevealerGUI:
    # ... (the GUI code is identical to the previous version; I'll include the full final code in a single block at the end)

