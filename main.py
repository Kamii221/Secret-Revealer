#!/usr/bin/env python3
"""
Secret‑Revealer v2.1 – Real OSINT Engine
Integrates:
- HaveIBeenPwned (free, 1 req/sec)
- numverify (free phone lookup, sign up for API key)
- Google Custom Search (free tier, 100 queries/day)
- WHOIS, DNS, and mock dark web
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import time
import requests
import re
from datetime import datetime

# ------------------ CONFIG (add your keys) ------------------
CONFIG = {
    "hibp_api_key": "",  # optional, but recommended
    "numverify_key": "2b14cc0a151004df6507b96fcb275535", # get from numverify.com (free)
    "google_api_key": "",
    "google_cx": "",
    "tor_proxy": "socks5h://127.0.0.1:9050"
}

# ------------------ REAL OSINT MODULES ------------------
class RealOSINTEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Secret-Revealer/2.1"})

    def check_hibp(self, email):
        """Check if email appears in breaches (HaveIBeenPwned)"""
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
        """Get carrier and location via numverify (free tier)"""
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
        """Search using Google Custom Search API"""
        if not CONFIG["google_api_key"] or not CONFIG["google_cx"]:
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
        """Simple WHOIS via python-whois (fallback to mock)"""
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
            return {"error": "WHOIS lookup failed"}

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

        # 1. Email breach check
        email = data.get("email")
        if email and "enrichment" in str(modules):
            breaches = self.check_hibp(email)
            for b in breaches:
                result["identity"]["breaches"].append({
                    "source": b.get("Name"),
                    "date": b.get("BreachDate"),
                    "description": b.get("Description", "")[:100]
                })
            if breaches:
                result["score"] += 0.2

        # 2. Phone lookup
        phone = data.get("phone")
        if phone and "clearnet" in str(modules):
            phone_info = self.lookup_phone(phone)
            if phone_info:
                result["identity"]["phones"].append({
                    "number": phone,
                    "carrier": phone_info.get("carrier"),
                    "country": phone_info.get("country"),
                    "location": phone_info.get("location"),
                    "confidence": 0.9
                })
                result["score"] += 0.1

        # 3. Google search for username/name
        query = data.get("username") or data.get("name")
        if query and "clearnet" in str(modules):
            items = self.google_search(query)
            if items:
                result["identity"]["search_results"] = [
                    {"title": i.get("title"), "link": i.get("link")}
                    for i in items[:5]
                ]
                result["score"] += 0.1

        # 4. WHOIS for domain
        domain = data.get("domain")
        if domain and "enrichment" in str(modules):
            whois_data = self.whois_lookup(domain)
            if whois_data and "error" not in whois_data:
                result["identity"]["addresses"].append(f"Domain: {domain} – Registrar: {whois_data.get('registrar')}")
                result["score"] += 0.1

        # 5. Dark web (mock) – place for Tor integration
        if "darkweb" in str(modules):
            result["identity"]["dark_web_mentions"].append({
                "source": "Mock Dark Web (replace with Tor/Ahmia)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "snippet": "To enable real dark web, integrate Tor and Ahmia search."
            })

        # Normalize score
        result["score"] = min(result["score"] + 0.5, 1.0)
        return result

# ------------------ GUI (same as before, but use RealOSINTEngine) ------------------
class SecretRevealerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secret‑Revealer v2.1 – Real OSINT")
        self.root.geometry("1200x800")
        self.engine = RealOSINTEngine()
        self.output_data = {}
        # ... (rest of GUI code is identical to previous version, just replace engine instantiation)
        # For brevity, I'll skip repeating all the UI code – it's the same as before.
        # I'll provide a full file in the next block.

# ... full code continues
