import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from core.engine import OSINTEngine
from utils.logger import setup_logger
import json
import yaml

class OSINTGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Omni‑OSINT v2.0 – Red Team Intelligence")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        self.logger = setup_logger()
        self.engine = OSINTEngine()
        self.output_data = {}

        self._build_menu()
        self._build_main_layout()

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Targets", command=self.load_targets)
        file_menu.add_command(label="Export Report", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Configure Proxy", command=self.open_settings)
        settings_menu.add_command(label="Toggle Tor", command=self.toggle_tor)
        menubar.add_cascade(label="Settings", menu=settings_menu)
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

        # Options
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

        # Right panel: Results
        right_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab1: Summary
        self.summary_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=20)
        self.notebook.add(self.summary_text, text="📊 Summary")

        # Tab2: JSON
        self.json_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=20)
        self.notebook.add(self.json_text, text="📄 Detailed JSON")

        # Tab3: Dark Web Results
        self.dark_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, height=20)
        self.notebook.add(self.dark_text, text="🌑 Dark Web")

        # Tab4: Graph (placeholder)
        self.graph_canvas = tk.Canvas(self.notebook, bg='white')
        self.notebook.add(self.graph_canvas, text="📈 Graph")

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X)

    def run_scan(self):
        # Gather inputs
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

        # Disable UI
        self.progress.start()
        self.status_var.set("Scanning...")
        # Run in thread
        thread = threading.Thread(target=self._scan_thread, args=(data,))
        thread.daemon = True
        thread.start()

    def _scan_thread(self, data):
        try:
            # Which modules to use
            modules = []
            if self.clearnet_var.get():
                modules.extend(['google', 'linkedin', 'twitter', 'github', 'shodan', 'whois'])
            if self.darkweb_var.get():
                modules.extend(['ahmia', 'dark_paste', 'breach_forums'])
            if self.enrich_var.get():
                modules.extend(['haveibeenpwned', 'dehashed', 'geoip'])

            # Run engine (mock for demonstration)
            result = self.engine.run(data, modules=modules)

            self.output_data = result
            # Update UI
            self.root.after(0, self._update_results, result)
        except Exception as e:
            self.root.after(0, self._show_error, str(e))
        finally:
            self.root.after(0, self._scan_done)

    def _update_results(self, result):
        # Summary
        summary = f"=== OSINT Report ===\n"
        summary += f"Identity: {result.get('identity', {}).get('full_name', 'N/A')}\n"
        summary += f"Emails: {len(result.get('identity', {}).get('emails', []))}\n"
        summary += f"Phones: {len(result.get('identity', {}).get('phones', []))}\n"
        summary += f"Breaches: {len(result.get('identity', {}).get('breaches', []))}\n"
        summary += f"Dark Web Mentions: {len(result.get('identity', {}).get('dark_web_mentions', []))}\n"
        summary += f"Confidence Score: {result.get('score', 0)}%\n"
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, summary)

        # JSON
        self.json_text.delete(1.0, tk.END)
        self.json_text.insert(tk.END, json.dumps(result, indent=2))

        # Dark web
        dark = result.get('identity', {}).get('dark_web_mentions', [])
        if dark:
            dark_str = "🌑 Dark Web Mentions:\n"
            for item in dark:
                dark_str += f"- Source: {item.get('source')}, Date: {item.get('date')}\n  Snippet: {item.get('snippet', '')[:200]}...\n"
        else:
            dark_str = "No dark web mentions found."
        self.dark_text.delete(1.0, tk.END)
        self.dark_text.insert(tk.END, dark_str)

        # Graph placeholder - could use networkx + matplotlib, but for now just text
        self.graph_canvas.delete("all")
        self.graph_canvas.create_text(10, 10, anchor=tk.NW, text="Graph visualization will show connections between entities.", fill='black')

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

    def load_targets(self):
        # Implement CSV load
        pass

    def export_report(self):
        # Save JSON/HTML
        pass

    def open_settings(self):
        # Settings window
        pass

    def toggle_tor(self):
        # Toggle Tor proxy
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = OSINTGUI(root)
    root.mainloop()
