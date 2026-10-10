import asyncio
import os
import re
import sqlite3
import struct
import time
import datetime
import threading
import shutil
import zipfile
import tarfile
import urllib.request
import urllib.parse
import ssl
import json
import base64
from io import BytesIO
from PIL import Image, ImageTk, ImageFile
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Ensure PIL handles full icon rendering cleanly
ImageFile.LOAD_TRUNCATED_IMAGES = True

# --- Theme Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- App Version ---
CURRENT_VERSION = "1.0.1"

# Base64 32x32 Alien Face PNG Icon (Valid PNG Byte Sequence)
ALIEN_ICON_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAA"
    "AXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAACNSURBVFhH"
    "7ZXBCsAgDMR8+P9/m4sO3mR4iOsh1oO2CilI4i2mtS7C33m3mblmB2I+2UFiI4mNJDaS2EhiI4mN"
    "JDaS2EhiI2kF2INmPq2C3vC3p1WgN8w/eN3x+9o5O0hsJLGRAA7wO59WQUvSBy0f1pI+aPmwlvRB"
    "y4e1pA9aPqy1C3qIewK94R6Q3O89fTsnN5I4L+EBJAt0e3e21z4AAAAASUVORK5CYII="
)

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = os.path.join(db_path, "xdcc_database.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS packs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE,
                bot TEXT,
                pack_num TEXT,
                resolution TEXT,
                year TEXT,
                timestamp REAL,
                size TEXT,
                speed TEXT,
                server TEXT
            )
        ''')
        try:
            self.cursor.execute("ALTER TABLE packs ADD COLUMN server TEXT")
        except sqlite3.OperationalError:
            pass
        self.conn.commit()

    def add_pack(self, title, bot, pack_num, resolution, year, timestamp, size, speed, server=""):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO packs (title, bot, pack_num, resolution, year, timestamp, size, speed, server)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, bot, pack_num, resolution, year, timestamp, size, speed, server))
            self.conn.commit()
        except Exception as e:
            print(f"DB Error: {e}")

    def fix_old_timestamps(self):
        try:
            current_now = time.time()
            self.cursor.execute("UPDATE packs SET timestamp = ? WHERE timestamp < 1000000000", (current_now,))
            self.conn.commit()
        except Exception as e:
            print(f"Timestamp Fix Error: {e}")

    def get_stats(self):
        try:
            self.cursor.execute("SELECT COUNT(*), COUNT(DISTINCT bot), MAX(timestamp) FROM packs")
            count, unique_bots, max_ts = self.cursor.fetchone()
        except Exception:
            count, unique_bots, max_ts = 0, 0, None

        file_size_bytes = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        if file_size_bytes >= 1024 * 1024:
            size_str = f"{file_size_bytes / (1024 * 1024):.2f} MB"
        else:
            size_str = f"{file_size_bytes / 1024:.2f} KB"

        last_update_str = "Never"
        if max_ts:
            last_update_str = datetime.datetime.fromtimestamp(max_ts).strftime("%d/%m/%Y %H:%M:%S")

        return {
            "total_packs": count or 0,
            "unique_bots": unique_bots or 0,
            "file_size": size_str,
            "last_updated": last_update_str
        }

    def get_servers(self):
        try:
            self.cursor.execute("SELECT DISTINCT server FROM packs WHERE server IS NOT NULL AND server != ''")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception:
            return []

    def optimize_db(self):
        try:
            self.conn.execute("VACUUM")
            self.conn.commit()
        except Exception as e:
            print(f"Optimization Error: {e}")


class InstructionsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("CipherStream XDCC - Comprehensive User Guide & Instructions")
        self.geometry("880x680")
        self.minsize(780, 580)
        self.attributes("-topmost", True)
        self.parent.set_window_icon(self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        t_xdcc = self.tabview.add("1. What is XDCC?")
        t_nick = self.tabview.add("2. NickServ & Identity")
        t_net = self.tabview.add("3. Network Config")
        t_api = self.tabview.add("4. API Keys Setup")
        t_guide = self.tabview.add("5. How to Use")

        # --- Tab 1: XDCC Explanation ---
        txt1 = ctk.CTkTextbox(t_xdcc, font=("Consolas", 12), wrap="word")
        txt1.pack(fill="both", expand=True, padx=5, pady=5)
        txt1.insert("1.0", (
            "======================================================================\n"
            "               UNDERSTANDING IRC & XDCC FILE SHARING                  \n"
            "======================================================================\n\n"
            "1. WHAT IS IRC?\n"
            "   IRC (Internet Relay Chat) is one of the oldest internet chat protocols.\n"
            "   Users connect to an IRC server (e.g. irc.server.net) and join channels\n"
            "   (e.g. #channel) to communicate in real time.\n\n"
            "2. WHAT IS XDCC?\n"
            "   XDCC stands for 'eXtended Direct Client-to-Client'. It is a file sharing\n"
            "   protocol built on top of IRC.\n\n"
            "   - Distribution Bots: Special automated chat users (bots) maintain large\n"
            "     libraries of files arranged into 'Packs'.\n"
            "   - Pack Numbers: Each file stored on a bot is assigned a unique number\n"
            "     (for example: Pack #1042).\n"
            "   - Direct Downloads: When you request a pack, the bot initiates a direct\n"
            "     DCC socket transfer to send the file directly to your PC without\n"
            "     passing through intermediate web servers.\n\n"
            "3. ADVANTAGES OF CIPHERSTREAM XDCC:\n"
            "   - Multi-Server Support: Connect to multiple IRC networks simultaneously.\n"
            "   - Automatic Indexing: Listens to announce channels and saves files into\n"
            "     a local, fast SQLite search database.\n"
            "   - Automated Queueing & Staggering: Staggers batch downloads cleanly so\n"
            "     bots don't flood or reject your request.\n"
            "   - Resume Capabilities: Automatic partial file detection and resume support.\n"
        ))
        txt1.configure(state="disabled")

        # --- Tab 2: NickServ Explanation ---
        txt2 = ctk.CTkTextbox(t_nick, font=("Consolas", 12), wrap="word")
        txt2.pack(fill="both", expand=True, padx=5, pady=5)
        txt2.insert("1.0", (
            "======================================================================\n"
            "              NICKSERV IDENTIFICATION & REGISTRATION                  \n"
            "======================================================================\n\n"
            "1. WHAT IS NICKSERV?\n"
            "   NickServ is an automated service built into most major IRC networks that\n"
            "   allows users to reserve and password-protect their nickname.\n\n"
            "2. WHY DO I NEED IT FOR XDCC?\n"
            "   Many IRC networks enforce security policies where distribution bots and\n"
            "   chat channels will REJECT file transfers or ban users who are using\n"
            "   unregistered or unauthenticated nicknames.\n\n"
            "3. HOW CIPHERSTREAM AUTOMATES NICKSERV:\n"
            "   - Registration: If a network requests NickServ registration, enter your\n"
            "     desired password and email address in the 'Network & API Settings' window.\n"
            "   - Nick Age Policies: Many IRC networks enforce a rule requiring your\n"
            "     nick to be active for a set duration before accepting registration.\n"
            "   - Auto-Identify: Once registered, whenever you connect in the future,\n"
            "     CipherStream silently logs you into NickServ in the background before\n"
            "     joining channels or requesting files.\n"
        ))
        txt2.configure(state="disabled")

        # --- Tab 3: Network Configuration ---
        txt3 = ctk.CTkTextbox(t_net, font=("Consolas", 12), wrap="word")
        txt3.pack(fill="both", expand=True, padx=5, pady=5)
        txt3.insert("1.0", (
            "======================================================================\n"
            "                   NETWORK CONFIGURATION SETUP                        \n"
            "======================================================================\n\n"
            "Open the configuration window anytime by clicking 'Network & API Settings'\n"
            "at the top of the main application window.\n\n"
            "1. ADDING A NEW IRC SERVER:\n"
            "   - Hostname: Enter the server address (e.g. irc.server.net).\n"
            "   - Port: Standard plain IRC uses port 6667.\n"
            "   - Click 'Add Server' to add it to your server roster.\n\n"
            "2. CONFIGURING SERVER DETAILS:\n"
            "   - Auto-Connect: Enable to automatically connect to this server when clicking 'Connect All'.\n"
            "   - Nickname: Choose a unique handle.\n"
            "   - NickServ Pass: Enter your NickServ password here.\n"
            "   - NickServ Email: Enter your email address if registering a new nick.\n"
            "   - Auto-Join Channels: Add channels where bots announce packs (e.g. #channel).\n"
            "   - Click 'Save Server Config' to apply changes.\n"
        ))
        txt3.configure(state="disabled")

        # --- Tab 4: API Keys ---
        txt4 = ctk.CTkTextbox(t_api, font=("Consolas", 12), wrap="word")
        txt4.pack(fill="both", expand=True, padx=5, pady=5)
        txt4.insert("1.0", (
            "======================================================================\n"
            "           OBTAINING FREE API KEYS FOR LIVE RELEASE PREVIEW           \n"
            "======================================================================\n\n"
            "CipherStream includes a Live Release Preview sidebar that automatically fetches\n"
            "high-resolution posters, plot summaries, and release dates for movies, TV series, and PC games.\n\n"
            "To enable live metadata preview, enter API keys in 'Network & API Settings' -> 'API Keys (Global)':\n\n"
            "1. TMDB (The Movie Database) API KEY (For Movies & TV Shows):\n"
            "   - Cost: 100% Free\n"
            "   - Step 1: Go to https://www.themoviedb.org/ and sign up for a free account.\n"
            "   - Step 2: Navigate to Account Settings -> API -> Request an API Key.\n"
            "   - Step 3: Choose 'Developer' and fill in standard basic details.\n"
            "   - Step 4: Copy your 'API Key (v3 auth)' and paste it into CipherStream.\n\n"
            "2. RAWG API KEY (For PC Games & Updates):\n"
            "   - Cost: 100% Free\n"
            "   - Step 1: Go to https://rawg.io/apidocs and create a free user account.\n"
            "   - Step 2: Click 'Get API Key'.\n"
            "   - Step 3: Copy your personal API key string and paste it into CipherStream.\n\n"
            "Note: TVMaze fallback metadata works automatically out of the box without an API key!"
        ))
        txt4.configure(state="disabled")

        # --- Tab 5: How to Use ---
        txt5 = ctk.CTkTextbox(t_guide, font=("Consolas", 12), wrap="word")
        txt5.pack(fill="both", expand=True, padx=5, pady=5)
        txt5.insert("1.0", (
            "======================================================================\n"
            "                       QUICK START USAGE GUIDE                        \n"
            "======================================================================\n\n"
            "STEP 1: CONNECT TO IRC\n"
            "   Click 'Connect All' or select a server and click 'Connect Selected'.\n"
            "   The client will connect, authenticate with NickServ, and join channels.\n\n"
            "STEP 2: SEARCH THE INDEXED DATABASE\n"
            "   - Type terms in the search bar (e.g. '1080p', 'Inception').\n"
            "   - Use Resolution, Codec, or Year filters to narrow down results.\n"
            "   - Single-click any item to preview poster artwork and plot summaries.\n\n"
            "STEP 3: STAGE & DOWNLOAD\n"
            "   - Double-click search results to push them to the 'Staging Queue'.\n"
            "   - Click 'Check Bot Status' to see if the bot sharing the pack is currently online.\n"
            "   - Click 'Download All (Push to Active)' to begin downloads.\n"
            "   - Transfers are automatically staggered with a 4-second buffer to prevent bot bans.\n\n"
            "STEP 4: MULTI-SERVER CHANNEL CHAT\n"
            "   Click 'Channel Chat' to open a tabbed IRC client where you can talk in\n"
            "   channels, double-click user nicknames to send PMs, or view operator counts.\n\n"
            "STEP 5: AUTO-EXTRACT ARCHIVES\n"
            "   Downloaded .zip or .tar archives automatically extract into subfolders in your download directory upon completion."
        ))
        txt5.configure(state="disabled")


class LogWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Expanded System Log View")
        self.geometry("900x600")
        self.attributes("-topmost", True)
        self.parent.set_window_icon(self)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        ctk.CTkLabel(top_frame, text="Filter by Server:").pack(side="left", padx=5)
        
        self.filter_var = tk.StringVar(value="All Logs")
        srv_list = ["All Logs"] + list(self.parent.config.get("servers", {}).keys())
        self.filter_combo = ctk.CTkComboBox(top_frame, values=srv_list, variable=self.filter_var, command=self.apply_filter)
        self.filter_combo.pack(side="left", padx=5)
        
        self.log_box = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.log_box.tag_config("system", foreground="#81d4fa")
        self.log_box.tag_config("sent", foreground="#ffb74d")
        self.log_box.tag_config("dcc", foreground="#29b6f6")
        self.log_box.tag_config("notice", foreground="#ab47bc")
        self.log_box.tag_config("error", foreground="yellow", underline=True)
        self.log_box.tag_config("success", foreground="#00e676")
        self.log_box.tag_config("default", foreground="#e0e0e0")
        
        self.apply_filter("All Logs")

    def apply_filter(self, choice):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        for msg, tag in self.parent.log_history:
            if choice == "All Logs" or choice in msg:
                self.log_box.insert("end", msg, tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")


class NetworkManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Network, Channels & API Settings")
        self.geometry("820x680")
        self.minsize(780, 600)
        self.attributes("-topmost", True)
        self.parent.set_window_icon(self)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        lb_bg = "#ffffff" if self.parent.config.get("theme", "Dark").lower() == "light" else "#2b2b2b"
        lb_fg = "#000000" if self.parent.config.get("theme", "Dark").lower() == "light" else "white"
        
        self.srv_listbox = tk.Listbox(left_frame, bg=lb_bg, fg=lb_fg, font=("Consolas", 11), selectbackground="#1f538d", highlightthickness=0, borderwidth=0)
        self.srv_listbox.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.srv_listbox.bind("<<ListboxSelect>>", self.on_server_select)
        
        add_del_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        add_del_frame.pack(side="bottom", fill="x", padx=5, pady=5)
        
        entry_frame = ctk.CTkFrame(add_del_frame, fg_color="transparent")
        entry_frame.pack(side="top", fill="x", pady=(0, 5))
        
        self.new_srv_entry = ctk.CTkEntry(entry_frame, placeholder_text="irc.server.net")
        self.new_srv_entry.pack(side="left", fill="x", expand=True, padx=(0, 2))
        
        self.new_port_entry = ctk.CTkEntry(entry_frame, width=50, placeholder_text="6667")
        self.new_port_entry.pack(side="left", padx=(2, 0))
        self.new_port_entry.insert(0, "6667")
        
        btn_frame = ctk.CTkFrame(add_del_frame, fg_color="transparent")
        btn_frame.pack(side="top", fill="x")
        
        ctk.CTkButton(btn_frame, text="Add Server", command=self.add_server).pack(side="left", expand=True, padx=(0, 2))
        ctk.CTkButton(btn_frame, text="Delete", fg_color="firebrick", command=self.del_server).pack(side="right", expand=True, padx=(2, 0))

        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        right_frame.grid_columnconfigure(1, weight=1)

        self.selected_server = None

        self.tabview = ctk.CTkTabview(right_frame)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        tab_srv = self.tabview.add("Server Config")
        tab_api = self.tabview.add("API Keys (Global)")
        
        tab_srv.grid_columnconfigure(1, weight=1)
        tab_api.grid_columnconfigure(1, weight=1)

        # --- Tab 1: Server Config ---
        ctk.CTkLabel(tab_srv, text="Auto-Connect:").grid(row=0, column=0, sticky="e", padx=10, pady=5)
        self.auto_conn_var = tk.BooleanVar()
        self.auto_conn_chk = ctk.CTkCheckBox(tab_srv, text="Enable for this server", variable=self.auto_conn_var)
        self.auto_conn_chk.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(tab_srv, text="Nickname:").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.nick_entry = ctk.CTkEntry(tab_srv, placeholder_text="Required unique nickname")
        self.nick_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(tab_srv, text="NickServ Pass:").grid(row=2, column=0, sticky="e", padx=10, pady=5)
        self.pass_entry = ctk.CTkEntry(tab_srv, show="*", placeholder_text="Password for NickServ")
        self.pass_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(tab_srv, text="NickServ Email:").grid(row=3, column=0, sticky="e", padx=10, pady=5)
        self.email_entry = ctk.CTkEntry(tab_srv, placeholder_text="Email for auto-registration")
        self.email_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(tab_srv, text="Auto-Join Channels:").grid(row=4, column=0, sticky="ne", padx=10, pady=5)
        
        chan_container = ctk.CTkFrame(tab_srv, fg_color="transparent")
        chan_container.grid(row=4, column=1, sticky="ew", padx=10, pady=5)
        
        self.chan_listbox = tk.Listbox(
            chan_container, bg=lb_bg, fg=lb_fg, font=("Consolas", 11),
            selectbackground="#1f538d", highlightthickness=0, borderwidth=0, selectmode=tk.EXTENDED, height=5
        )
        self.chan_listbox.pack(side="top", fill="both", expand=True)
        
        chan_ctrl_frame = ctk.CTkFrame(chan_container, fg_color="transparent")
        chan_ctrl_frame.pack(side="top", fill="x", pady=(5, 0))
        
        self.new_chan_entry = ctk.CTkEntry(chan_ctrl_frame, placeholder_text="#channel")
        self.new_chan_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        add_chan_btn = ctk.CTkButton(chan_ctrl_frame, text="Add", width=50, command=self.add_channel)
        add_chan_btn.pack(side="left", padx=2)
        
        rem_chan_btn = ctk.CTkButton(chan_ctrl_frame, text="Remove", width=60, fg_color="firebrick", command=self.remove_channel)
        rem_chan_btn.pack(side="left", padx=0)

        save_btn = ctk.CTkButton(tab_srv, text="Save Server Config", fg_color="green", command=self.save_server_details)
        save_btn.grid(row=5, column=0, columnspan=2, pady=15)

        # --- Tab 2: API Keys ---
        ctk.CTkLabel(tab_api, text="TMDB API Key:", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.tmdb_entry = ctk.CTkEntry(tab_api, placeholder_text="Enter TMDB v3 API Key (Optional)", show="*", width=250)
        self.tmdb_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(tab_api, text="RAWG API Key:", font=("Arial", 12, "bold")).grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.rawg_entry = ctk.CTkEntry(tab_api, placeholder_text="Enter RAWG API Key (Optional)", show="*", width=250)
        self.rawg_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(tab_api, text="Used for enhanced movie, TV show, and PC game\nposters/metadata without logging in.", font=("Arial", 10), text_color="gray").grid(row=2, column=1, sticky="w", padx=10, pady=(0, 10))

        save_api_btn = ctk.CTkButton(tab_api, text="Save Global API Keys", fg_color="green", command=self.save_api_keys)
        save_api_btn.grid(row=3, column=0, columnspan=2, pady=15)

        self.populate_servers()
        self.load_api_keys_ui()

    def add_channel(self):
        new_chan = self.new_chan_entry.get().strip()
        if new_chan:
            if not new_chan.startswith("#"):
                new_chan = "#" + new_chan
            self.chan_listbox.insert(tk.END, new_chan)
            self.new_chan_entry.delete(0, 'end')

    def remove_channel(self):
        selected = self.chan_listbox.curselection()
        for i in reversed(selected):
            self.chan_listbox.delete(i)

    def populate_servers(self):
        self.srv_listbox.delete(0, tk.END)
        for srv in self.parent.config.get("servers", {}):
            self.srv_listbox.insert(tk.END, srv)
    
    def on_server_select(self, event):
        selection = self.srv_listbox.curselection()
        if selection:
            srv = self.srv_listbox.get(selection[0])
            self.selected_server = srv
            data = self.parent.config["servers"][srv]
            
            self.auto_conn_var.set(data.get("auto_connect", True))
            self.nick_entry.delete(0, 'end')
            self.nick_entry.insert(0, data.get("nick", ""))
            self.pass_entry.delete(0, 'end')
            self.pass_entry.insert(0, data.get("nickserv_pass", ""))
            self.email_entry.delete(0, 'end')
            self.email_entry.insert(0, data.get("nickserv_email", ""))
            
            self.chan_listbox.delete(0, tk.END)
            chans = data.get("channels", [])
            for c in chans:
                self.chan_listbox.insert(tk.END, c)

    def add_server(self):
        new_srv = self.new_srv_entry.get().strip()
        port = self.new_port_entry.get().strip() or "6667"
        if new_srv:
            if ":" not in new_srv:
                new_srv = f"{new_srv}:{port}"
            if new_srv not in self.parent.config["servers"]:
                self.parent.config["servers"][new_srv] = {
                    "auto_connect": True, "nick": "", "nickserv_pass": "", "nickserv_email": "", "channels": []
                }
                self.parent.save_config()
                self.parent.update_server_combos()
                self.populate_servers()
            self.new_srv_entry.delete(0, 'end')
            self.new_port_entry.delete(0, 'end')
            self.new_port_entry.insert(0, "6667")

    def del_server(self):
        if self.selected_server and self.selected_server in self.parent.config["servers"]:
            del self.parent.config["servers"][self.selected_server]
            self.selected_server = None
            self.parent.save_config()
            self.parent.update_server_combos()
            self.populate_servers()
            
            self.nick_entry.delete(0, 'end')
            self.pass_entry.delete(0, 'end')
            self.email_entry.delete(0, 'end')
            self.chan_listbox.delete(0, tk.END)

    def save_server_details(self):
        if self.selected_server and self.selected_server in self.parent.config["servers"]:
            data = self.parent.config["servers"][self.selected_server]
            data["auto_connect"] = self.auto_conn_var.get()
            data["nick"] = self.nick_entry.get().strip()
            data["nickserv_pass"] = self.pass_entry.get().strip()
            data["nickserv_email"] = self.email_entry.get().strip()
            
            chans = list(self.chan_listbox.get(0, tk.END))
            data["channels"] = chans
            
            self.parent.save_config()
            self.parent.log(f"[System] Updated configuration for {self.selected_server}.")
            
            if self.parent.is_connected and self.selected_server in self.parent.connections:
                proto = self.parent.connections[self.selected_server]
                if proto and proto.transport:
                    joined = self.parent.joined_channels.get(self.selected_server, [])
                    for c in chans:
                        if c not in joined:
                            proto.send(f"JOIN {c}")
                            self.parent.log(f"[{self.selected_server}] Sent JOIN for new channel: {c}")

    def load_api_keys_ui(self):
        keys = self.parent.config.get("api_keys", {})
        self.tmdb_entry.delete(0, 'end')
        self.tmdb_entry.insert(0, keys.get("tmdb", ""))
        self.rawg_entry.delete(0, 'end')
        self.rawg_entry.insert(0, keys.get("rawg", ""))

    def save_api_keys(self):
        if "api_keys" not in self.parent.config:
            self.parent.config["api_keys"] = {}
        self.parent.config["api_keys"]["tmdb"] = self.tmdb_entry.get().strip()
        self.parent.config["api_keys"]["rawg"] = self.rawg_entry.get().strip()
        self.parent.save_config()
        self.parent.log("[System] Global API keys updated successfully.")
        messagebox.showinfo("Saved", "Global API keys updated successfully.", parent=self)


class ChannelChatWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("IRC Multi-Server Channel Chat")
        self.geometry("900x580")
        self.minsize(750, 480)
        self.attributes("-topmost", True)
        self.parent.set_window_icon(self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_container = ctk.CTkFrame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        main_container.grid_columnconfigure(0, weight=4)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(main_container)
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(top_bar, text="Server:").pack(side="left", padx=5)
        srv_list = list(self.parent.connections.keys()) if self.parent.connections else ["None"]
        self.srv_combo = ctk.CTkComboBox(top_bar, values=srv_list, width=180, command=self.on_server_switch)
        self.srv_combo.pack(side="left", padx=5)

        ctk.CTkLabel(top_bar, text="Channel:").pack(side="left", padx=(10, 5))
        self.chan_combo = ctk.CTkComboBox(top_bar, values=[""], width=180, command=self.on_channel_switch)
        self.chan_combo.pack(side="left", padx=5)

        self.stats_label = ctk.CTkLabel(top_bar, text="Users: 0 | Ops: 0 | Voiced: 0", font=("Consolas", 11, "bold"), text_color="#81d4fa")
        self.stats_label.pack(side="right", padx=10)

        self.chat_box = ctk.CTkTextbox(main_container, font=("Consolas", 11), wrap="word")
        self.chat_box.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=0)
        
        try:
            tb = self.chat_box._textbox if hasattr(self.chat_box, "_textbox") else self.chat_box
            tb.tag_config("timestamp", foreground="#757575")
            tb.tag_config("nick_self", foreground="#29b6f6", font=("Consolas", 11, "bold"))
            tb.tag_config("nick_other", foreground="#81c784", font=("Consolas", 11, "bold"))
            tb.tag_config("nick_bot", foreground="#ef5350", font=("Consolas", 11, "bold"))
            tb.tag_config("notice", foreground="#ab47bc")
            tb.tag_config("action", foreground="#ba68c8", font=("Consolas", 11, "italic"))
            tb.tag_config("system", foreground="#ffb74d", font=("Consolas", 11, "italic"))
        except Exception as e:
            self.parent.log(f"[Warning] Could not load chat color tags: {e}")
            
        self.chat_box.configure(state="disabled") 

        nick_frame = ctk.CTkFrame(main_container)
        nick_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=0)
        nick_frame.grid_rowconfigure(1, weight=1)
        nick_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(nick_frame, text="Users", font=("Arial", 11, "bold")).grid(row=0, column=0, pady=2)
        
        lb_bg = "#ffffff" if self.parent.config.get("theme", "Dark").lower() == "light" else "#2b2b2b"
        lb_fg = "#000000" if self.parent.config.get("theme", "Dark").lower() == "light" else "white"

        self.nick_listbox = tk.Listbox(
            nick_frame, bg=lb_bg, fg=lb_fg, selectbackground="#1f538d",
            highlightthickness=0, borderwidth=0, font=("Consolas", 10)
        )
        nick_scroll = tk.Scrollbar(nick_frame, orient="vertical", command=self.nick_listbox.yview)
        self.nick_listbox.configure(yscrollcommand=nick_scroll.set)
        self.nick_listbox.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        nick_scroll.grid(row=1, column=1, sticky="ns") 
        
        self.nick_listbox.bind("<Double-Button-1>", self.on_nick_double_click)

        input_bar = ctk.CTkFrame(main_container)
        input_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        self.msg_entry = ctk.CTkEntry(input_bar, placeholder_text="Type a message or /command...")
        self.msg_entry.pack(side="left", padx=5, fill="x", expand=True, pady=5)
        self.msg_entry.bind("<Return>", lambda event: self.send_chat_message())

        self.send_btn = ctk.CTkButton(input_bar, text="Send", width=80, command=self.send_chat_message)
        self.send_btn.pack(side="right", padx=5, pady=5)

        self.update_server_list()

    def on_nick_double_click(self, event):
        selection = self.nick_listbox.curselection()
        if selection:
            raw_nick = self.nick_listbox.get(selection[0])
            clean_nick = raw_nick.lstrip("~&@%+")
            current_text = self.msg_entry.get()
            if current_text:
                self.msg_entry.insert("end", f"{clean_nick} ")
            else:
                self.msg_entry.insert("end", f"@{clean_nick}: ")
            self.msg_entry.focus()

    def update_server_list(self):
        srvs = list(self.parent.connections.keys())
        if srvs:
            self.srv_combo.configure(values=srvs)
            curr_srv = self.srv_combo.get()
            if curr_srv not in srvs:
                self.srv_combo.set(srvs[0])
                self.on_server_switch(srvs[0])
            else:
                self.update_channel_list(curr_srv)
        else:
            self.srv_combo.configure(values=["None"])
            self.srv_combo.set("None")
            self.chan_combo.configure(values=[""])
            self.chan_combo.set("")

    def on_server_switch(self, selected_srv):
        self.update_channel_list(selected_srv)

    def update_channel_list(self, srv=None):
        if not srv:
            srv = self.srv_combo.get()
        chans = self.parent.joined_channels.get(srv, [])
        if chans:
            self.chan_combo.configure(values=chans)
            curr_chan = self.chan_combo.get()
            if curr_chan not in chans:
                self.chan_combo.set(chans[0])
                self.on_channel_switch(chans[0])
            else:
                self.on_channel_switch(curr_chan)
        else:
            self.chan_combo.configure(values=[""])
            self.chan_combo.set("")
            self.clear_display()

    def clear_display(self):
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self.nick_listbox.delete(0, tk.END)
        self.stats_label.configure(text="Users: 0 | Ops: 0 | Voiced: 0")

    def on_channel_switch(self, selected_chan):
        srv = self.srv_combo.get()
        if not srv or srv == "None" or not selected_chan:
            self.clear_display()
            return

        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        history = self.parent.chat_history.get((srv, selected_chan), [])
        for entry in history:
            self.render_message(entry)
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

        self.refresh_nicklist(srv, selected_chan)

    def render_message(self, entry):
        ts = entry["ts"]
        nick = entry["nick"]
        msg = entry["msg"]
        mtype = entry["type"]

        self.chat_box.insert("end", f"{ts} ", "timestamp")

        if mtype == "system":
            self.chat_box.insert("end", f"*** {nick} {msg}\n", "system")
        elif mtype == "action":
            self.chat_box.insert("end", f"* {nick} {msg}\n", "action")
        elif mtype == "notice":
            self.chat_box.insert("end", f"-{nick}- ", "notice")
            self.chat_box.insert("end", f"{msg}\n", "notice")
        else:
            active_srv = self.srv_combo.get()
            my_nick = "xdccuser"
            if active_srv in self.parent.connections and self.parent.connections[active_srv]:
                my_nick = self.parent.connections[active_srv].nick.lower()
                
            nick_tag = "nick_self" if nick.lower() == my_nick else "nick_other"
            if nick.startswith("[MG]") or "bot" in nick.lower(): 
                nick_tag = "nick_bot"
            self.chat_box.insert("end", f"<{nick}> ", nick_tag)
            self.chat_box.insert("end", f"{msg}\n")

    def on_new_message(self, srv, chan, entry):
        if self.srv_combo.get() == srv and self.chan_combo.get() == chan:
            self.chat_box.configure(state="normal")
            self.render_message(entry)
            self.chat_box.see("end")
            self.chat_box.configure(state="disabled")

    def refresh_nicklist(self, srv, chan):
        if self.srv_combo.get() == srv and self.chan_combo.get() == chan:
            self.nick_listbox.delete(0, tk.END)
            raw_nicks = list(self.parent.channel_nicks.get((srv, chan), set()))
            
            def nick_sort_key(n):
                clean = n.lstrip("~&@%+")
                prefix = n[0] if n else ""
                if prefix in "~&@%":
                    return (0, clean.lower())
                elif prefix == "+":
                    return (1, clean.lower())
                else:
                    return (2, clean.lower())

            sorted_nicks = sorted(raw_nicks, key=nick_sort_key)
            
            ops_count = sum(1 for n in sorted_nicks if n and n[0] in "~&@%")
            voiced_count = sum(1 for n in sorted_nicks if n and n[0] == "+")
            total_count = len(sorted_nicks)

            for nick in sorted_nicks:
                self.nick_listbox.insert(tk.END, nick)

            self.stats_label.configure(text=f"Users: {total_count} | Ops: {ops_count} | Voiced: {voiced_count}")

    def send_chat_message(self):
        srv = self.srv_combo.get().strip()
        target_chan = self.chan_combo.get().strip()
        msg = self.msg_entry.get().strip()
        
        if not msg or srv not in self.parent.connections:
            return

        proto = self.parent.connections[srv]
        if not proto or not proto.transport:
            return

        if msg.startswith("/"):
            parts = msg.split(" ", 1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if cmd == "/join":
                if args:
                    for c in args.split(","):
                        clean_c = c.strip()
                        if not clean_c.startswith("#"): clean_c = "#" + clean_c
                        proto.send(f"JOIN {clean_c}")
            elif cmd == "/part":
                part_chan = args.strip() if args else target_chan
                if part_chan:
                    if not part_chan.startswith("#"): part_chan = "#" + part_chan
                    proto.send(f"PART {part_chan}")
            elif cmd == "/nick":
                if args:
                    proto.send(f"NICK {args.strip()}")
                    proto.nick = args.strip()
            elif cmd == "/msg":
                if " " in args:
                    target, text = args.split(" ", 1)
                    proto.send(f"PRIVMSG {target} :{text}")
                    if target_chan:
                        self.parent.route_channel_message(srv, target_chan, f"-> {target}", text)
            elif cmd == "/me":
                if target_chan and args:
                    proto.send(f"PRIVMSG {target_chan} :\x01ACTION {args}\x01")
                    self.parent.route_channel_message(srv, target_chan, proto.nick, f"\x01ACTION {args}\x01")
            else:
                proto.send(f"{cmd.lstrip('/')} {args}")
                
            self.msg_entry.delete(0, "end")
            return

        if target_chan and msg:
            proto.send(f"PRIVMSG {target_chan} :{msg}")
            self.parent.route_channel_message(srv, target_chan, proto.nick, msg)
            self.msg_entry.delete(0, "end")


class IRCClient(asyncio.Protocol):
    def __init__(self, gui_app, server_str):
        self.gui_app = gui_app
        self.server_str = server_str
        
        srv_cfg = self.gui_app.config["servers"].get(self.server_str, {})
        cfg_nick = srv_cfg.get("nick", "").strip()
        
        # Enforce server-specific nick from configuration tab
        self.nick = cfg_nick if cfg_nick else "XDCCUser"
        self.nickserv_pass = srv_cfg.get("nickserv_pass", "").strip()
        self.nickserv_email = srv_cfg.get("nickserv_email", "").strip()
        
        self.transport = None
        self.buffer = ""
        self.pending_resumes = {}
        self._has_joined = False
        self.connect_time = 0
        self.registration_scheduled = False
        self.identified = False

    def connection_made(self, transport):
        self.transport = transport
        self.connect_time = time.time()
        self.gui_app.log(f"[System] Connected to IRC Server socket ({self.server_str}).")
        self.send(f"NICK {self.nick}")
        self.send(f"USER {self.nick} 8 * :{self.nick} XDCC Monitor")

    def join_configured_channels(self):
        srv_cfg = self.gui_app.config["servers"].get(self.server_str, {})
        for chan in srv_cfg.get("channels", []):
            if chan:
                self.send(f"JOIN {chan}")
                self.gui_app.log(f"[{self.server_str}] Attempting to join: {chan}")
        
    def data_received(self, data):
        self.buffer += data.decode('utf-8', errors='ignore')
        while "\r\n" in self.buffer:
            line, self.buffer = self.buffer.split("\r\n", 1)
            self.handle_line(line)

    def send(self, message):
        if self.transport:
            try:
                self.transport.write(message.encode('utf-8') + b"\r\n")
            except Exception:
                pass

    def register_nickserv(self, password, email):
        if not password or not email or not self.transport:
            return

        if self.server_str in self.gui_app.config["servers"]:
            self.gui_app.config["servers"][self.server_str]["nickserv_pass"] = password
            self.gui_app.config["servers"][self.server_str]["nickserv_email"] = email
            self.gui_app.save_config()

        self.nickserv_pass = password
        self.nickserv_email = email

        elapsed = time.time() - self.connect_time if self.connect_time > 0 else 0
        wait_time = max(0.0, 30.5 - elapsed)

        if wait_time > 0:
            self.gui_app.log(f"[{self.server_str}] Waiting {int(wait_time)}s for 30s nick age requirement before registering with NickServ...")
            self.gui_app.after(int(wait_time * 1000), lambda: self._do_register(password, email))
        else:
            self._do_register(password, email)

    def _do_register(self, password, email):
        if self.transport:
            self.send(f"PRIVMSG NickServ :REGISTER {password} {email}")
            self.gui_app.log(f"[{self.server_str}] Sent NickServ REGISTER command for {self.nick}.")

    def handle_line(self, line):
        if line.startswith("PING"):
            self.send(f"PONG {line.split()[1]}")
            return

        parts = line.split(" ")
        if len(parts) < 2:
            return

        command = parts[1]

        if command == "PRIVMSG":
            prefix = parts[0]
            nick = prefix.split("!")[0].lstrip(":")
            target = parts[2].lstrip(":")
            message = " ".join(parts[3:]).lstrip(":")

            if "\x01DCC SEND" in message:
                self.handle_dcc_request(nick, message)
            elif "\x01DCC ACCEPT" in message:
                self.handle_dcc_accept(nick, message)
            else:
                if target.startswith("#"):
                    self.gui_app.route_channel_message(self.server_str, target, nick, message)
                else:
                    if self.gui_app.chat_window and self.gui_app.chat_window.winfo_exists():
                        active_chan = self.gui_app.chat_window.chan_combo.get()
                        if active_chan:
                            self.gui_app.route_channel_message(self.server_str, active_chan, nick, message, msg_type="notice")
                    self.gui_app.log(f"[{self.server_str} PM from {nick}] {message}")
                    
                self.parse_xdcc(nick, message)

        elif command == "NOTICE":
            prefix = parts[0]
            nick = prefix.split("!")[0].lstrip(":")
            target = parts[2].lstrip(":")
            message = " ".join(parts[3:]).lstrip(":")
            self.parse_notice(nick, target, message)

        elif command.isdigit():
            numeric = command
            message = " ".join(parts[3:]).lstrip(":")
            clean_msg = re.sub(r'\x03(?:\d{1,2}(?:,\d{1,2})?)?|\x02|\x1f|\x16|\x0f', '', message)
            
            if numeric in ["376", "422"] and not self._has_joined:
                if self.nickserv_pass and not self.nickserv_email:
                    self.gui_app.log(f"[{self.server_str}] Server MOTD finished. Authenticating with NickServ...")
                    self.send(f"PRIVMSG NickServ :IDENTIFY {self.nickserv_pass}")
                    self.gui_app.after(1500, self.join_configured_channels)
                elif self.nickserv_pass and self.nickserv_email:
                    self.gui_app.log(f"[{self.server_str}] Server MOTD finished. Executing NickServ auto-registration...")
                    self.register_nickserv(self.nickserv_pass, self.nickserv_email)
                    self.gui_app.after(3500, self.join_configured_channels)
                else:
                    self.gui_app.log(f"[{self.server_str}] Server MOTD finished. Executing channel joins...")
                    self.join_configured_channels()
                self._has_joined = True

            if numeric == "353":
                chan_parts = message.split(" :")
                if len(chan_parts) > 1:
                    chan = chan_parts[0].split()[-1]
                    nicks = chan_parts[1].split()
                    self.gui_app.add_channel_nicks(self.server_str, chan, nicks)
            elif numeric == "332":
                chan = parts[3]
                self.gui_app.log(f"[{self.server_str} Topic - {chan}] {clean_msg}")
                self.gui_app.route_channel_message(self.server_str, chan, "Topic", clean_msg, msg_type="system")
            elif numeric in ["401", "402", "403", "404", "421", "433", "477", "482"]:
                self.gui_app.log(f"[{self.server_str} Error {numeric}] {clean_msg}")
            elif numeric not in ["001", "002", "003", "004", "251", "252", "253", "254", "255", "372", "375", "376", "005", "396", "265", "266"]:
                self.gui_app.log(f"[{self.server_str} Reply {numeric}] {clean_msg}")

        elif command in ["JOIN", "PART", "KICK", "QUIT", "MODE"]:
            prefix = parts[0]
            nick = prefix.split("!")[0].lstrip(":")
            target = (parts[2] if len(parts) > 2 else "").lstrip(":")

            if command == "JOIN":
                if nick.lower() == self.nick.lower():
                    if self.server_str not in self.gui_app.joined_channels:
                        self.gui_app.joined_channels[self.server_str] = []
                    if target not in self.gui_app.joined_channels[self.server_str]:
                        self.gui_app.joined_channels[self.server_str].append(target)
                        self.gui_app.after(0, self.gui_app.refresh_chat_window)
                self.gui_app.add_channel_nicks(self.server_str, target, [nick])
                self.gui_app.route_channel_message(self.server_str, target, nick, f"has joined {target}", msg_type="system")
                
            elif command == "PART":
                self.gui_app.remove_channel_nick(self.server_str, target, nick)
                self.gui_app.route_channel_message(self.server_str, target, nick, f"has left {target}", msg_type="system")
                if nick.lower() == self.nick.lower():
                    if self.server_str in self.gui_app.joined_channels and target in self.gui_app.joined_channels[self.server_str]:
                        self.gui_app.joined_channels[self.server_str].remove(target)
                    self.gui_app.after(0, self.gui_app.refresh_chat_window)
                    
            elif command == "QUIT":
                quit_msg = target
                if self.server_str in self.gui_app.joined_channels:
                    for chan in list(self.gui_app.joined_channels[self.server_str]):
                        nicks_set = self.gui_app.channel_nicks.get((self.server_str, chan), set())
                        if any(n.lstrip("~&@%+") == nick.lstrip("~&@%+") for n in nicks_set):
                            self.gui_app.route_channel_message(self.server_str, chan, nick, f"has quit ({quit_msg})", msg_type="system")
                            self.gui_app.remove_channel_nick(self.server_str, chan, nick)
                    
            elif command == "KICK":
                kicked = parts[3]
                reason = " ".join(parts[4:]).lstrip(":")
                self.gui_app.remove_channel_nick(self.server_str, target, kicked)
                self.gui_app.route_channel_message(self.server_str, target, nick, f"kicked {kicked} ({reason})", msg_type="system")
                if kicked.lower() == self.nick.lower():
                    if self.server_str in self.gui_app.joined_channels and target in self.gui_app.joined_channels[self.server_str]:
                        self.gui_app.joined_channels[self.server_str].remove(target)
                    self.gui_app.after(0, self.gui_app.refresh_chat_window)
                self.gui_app.log(f"[{self.server_str} KICK] {kicked} was kicked from {target} by {nick} ({reason})")

    def handle_dcc_request(self, nick, message):
        match = re.search(r'DCC SEND\s+"?([^"\s]+)"?\s+(\d+)\s+(\d+)\s+(\d+)', message)
        if match:
            filename, ip_int, port, size = match.groups()
            ip_addr = '.'.join(str((int(ip_int) >> i) & 0xFF) for i in [24, 16, 8, 0])
            port = int(port)
            size = int(size)

            self.gui_app.log(f"[DCC] Incoming transfer '{filename}' from {ip_addr}:{port}")
            target_key = None
            nick_lower = nick.lower()

            for k, widget_data in self.gui_app.active_transfers_widgets.items():
                if k.startswith(nick_lower + "_") and not widget_data["completed"] and not widget_data.get("task"):
                    target_key = k
                    break
            if not target_key:
                for k, widget_data in self.gui_app.active_transfers_widgets.items():
                    if not widget_data["completed"] and not widget_data.get("task"):
                        target_key = k
                        break

            target_path = os.path.join(self.gui_app.dl_path, filename)
            if os.path.exists(target_path):
                existing_size = os.path.getsize(target_path)
                if 0 < existing_size < size:
                    self.gui_app.log(f"[DCC Resume] Requesting resume for {filename} at {existing_size} bytes...")
                    self.pending_resumes[f"{nick_lower}_{port}"] = {
                        "ip": ip_addr, "port": port, "filename": filename, "size": size,
                        "existing_size": existing_size, "bot": nick, "transfer_key": target_key
                    }
                    self.send(f'PRIVMSG {nick} :\x01DCC RESUME "{filename}" {port} {existing_size}\x01')
                    return

            if target_key:
                task = asyncio.create_task(self.download_dcc_file(ip_addr, port, filename, size, 0, nick, target_key))
                self.gui_app.active_transfers_widgets[target_key]["task"] = task

    def handle_dcc_accept(self, nick, message):
        match = re.search(r'DCC ACCEPT\s+"?([^"\s]+)"?\s+(\d+)\s+(\d+)', message)
        if match:
            filename, port, position = match.groups()
            port = int(port)
            position = int(position)
            nick_lower = nick.lower()
            key = f"{nick_lower}_{port}"

            if key in self.pending_resumes:
                info = self.pending_resumes.pop(key)
                self.gui_app.log(f"[DCC Resume] Bot accepted resume for {filename} starting at byte {position}.")
                task = asyncio.create_task(self.download_dcc_file(
                    info["ip"], info["port"], info["filename"], info["size"], position, info["bot"], info["transfer_key"]
                ))
                if info["transfer_key"] in self.gui_app.active_transfers_widgets:
                    self.gui_app.active_transfers_widgets[info["transfer_key"]]["task"] = task

    async def download_dcc_file(self, ip, port, filename, filesize, start_offset, bot_nick, transfer_key):
        target_path = os.path.join(self.gui_app.dl_path, filename)
        mode_str = "ab" if start_offset > 0 else "wb"

        try:
            reader, writer = await asyncio.open_connection(ip, port)

            if transfer_key in self.gui_app.active_transfers_widgets:
                self.gui_app.active_transfers_widgets[transfer_key]["writer"] = writer
                self.gui_app.active_transfers_widgets[transfer_key]["paused"] = False

            bytes_received = start_offset
            start_time = time.time()
            last_update_time = start_time
            last_bytes = bytes_received

            self.gui_app.log(f"[DCC] Downloading {filename} ({filesize} bytes)...")

            with open(target_path, mode_str) as f:
                while bytes_received < filesize:
                    if transfer_key in self.gui_app.active_transfers_widgets:
                        w_data = self.gui_app.active_transfers_widgets[transfer_key]
                        if w_data.get("paused"):
                            self.gui_app.log(f"[DCC Pause] Paused download for {filename}")
                            writer.close()
                            await writer.wait_closed()
                            return
                        if w_data.get("stopped"):
                            self.gui_app.log(f"[DCC Stopped] Stopped download for {filename}")
                            writer.close()
                            await writer.wait_closed()
                            return

                    chunk = await reader.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_received += len(chunk)
                    writer.write(struct.pack("!I", bytes_received))
                    await writer.drain()

                    now = time.time()
                    time_diff = now - last_update_time
                    if time_diff >= 0.5:
                        speed = (bytes_received - last_bytes) / time_diff
                        last_bytes = bytes_received
                        last_update_time = now
                        if transfer_key:
                            self.gui_app.update_active_progress(transfer_key, bytes_received, filesize, "", speed)

            writer.close()
            await writer.wait_closed()
            self.gui_app.log(f"[Success] Downloaded successfully to {target_path}")
            if transfer_key:
                self.gui_app.update_active_complete(transfer_key, filesize, target_path)
        except asyncio.CancelledError:
            self.gui_app.log(f"[DCC Cancelled] Download aborted for {filename}")
        except Exception as e:
            if transfer_key in self.gui_app.active_transfers_widgets:
                w_data = self.gui_app.active_transfers_widgets[transfer_key]
                if w_data.get("paused") or w_data.get("stopped"):
                    return
            self.gui_app.log(f"[DCC Error] {e}")
            if transfer_key:
                self.gui_app.update_active_status(transfer_key, "Failed (Disconnected/Offline)")

    def parse_notice(self, nick, target, text):
        clean_text = re.sub(r'\x03(?:\d{1,2}(?:,\d{1,2})?)?|\x02|\x1f|\x16|\x0f', '', text)
        text_lower = clean_text.lower()

        # --- NickServ Handling ---
        if nick.lower() == "nickserv" or "nickserv" in nick.lower():
            self.gui_app.log(f"[{self.server_str} Notice from {nick}] {clean_text}")

            if any(k in text_lower for k in ["password accepted", "recognized", "identified", "logged in"]):
                self.identified = True
                self.gui_app.log(f"[{self.server_str}] Authentication successful. Re-joining missing channels...")
                self.join_configured_channels()
                return

            if any(k in text_lower for k in ["registered and protected", "this nickname is registered", "choose a different nick"]):
                if self.nickserv_pass and not self.identified:
                    self.send(f"PRIVMSG NickServ :IDENTIFY {self.nickserv_pass}")
                    self.gui_app.log(f"[{self.server_str}] Automatically identifying with NickServ...")
                return

            if any(k in text_lower for k in ["not registered", "isn't registered", "register password email"]):
                if self.nickserv_pass and self.nickserv_email and not self.registration_scheduled:
                    self.registration_scheduled = True
                    self.register_nickserv(self.nickserv_pass, self.nickserv_email)
                else:
                    self.gui_app.prompt_nick_registration(self.server_str)
                return

            if "30 seconds to register" in text_lower or "30s" in text_lower:
                if self.nickserv_pass and self.nickserv_email:
                    self.gui_app.log(f"[{self.server_str}] Enforcing 30s nick age limit. Rescheduling registration...")
                    self.gui_app.after(31000, lambda: self._do_register(self.nickserv_pass, self.nickserv_email))
                return

            return

        if clean_text.startswith("**") or "queue" in text_lower or "sending pack" in text_lower or "transfer" in text_lower:
            self.gui_app.log(f"[{self.server_str} Notice from {nick}] {clean_text}")
            return

        if target.startswith("#"):
            self.gui_app.route_channel_message(self.server_str, target, nick, clean_text, msg_type="notice")
        else:
            if self.gui_app.chat_window and self.gui_app.chat_window.winfo_exists():
                active_chan = self.gui_app.chat_window.chan_combo.get()
                if active_chan:
                    self.gui_app.route_channel_message(self.server_str, active_chan, nick, clean_text, msg_type="notice")
            else:
                if not re.search(r'pack\s*#', text_lower):
                    self.gui_app.log(f"[{self.server_str} Notice from {nick}] {clean_text}")

    def parse_xdcc(self, nick, text):
        clean_text = re.sub(r'\x03(?:\d{1,2}(?:,\d{1,2})?)?|\x02|\x1f|\x16|\x0f', '', text)
        bot = nick
        pack, title = None, None
        size, speed = "?", "?"

        msg_match = re.search(r'/msg\s+(\S+)\s+XDCC\s+SEND\s+(\d+)', clean_text, re.IGNORECASE)
        std_match = re.search(r'(?:^|\s)(?:#|pack\s*#?)\s*(\d+)', clean_text, re.IGNORECASE)

        if msg_match:
            bot = msg_match.group(1)
            pack = msg_match.group(2)
            sz_match = re.search(r'\|\s*([\d\.]+[KMGT]B?)\s*\|', clean_text, re.IGNORECASE)
            if sz_match: size = sz_match.group(1).replace(" ", "")
            tit_match = re.search(r'\|\s*[\d\.]+[KMGT]B?\s*\|\s*(.+?)\s*\|\s*\/msg', clean_text, re.IGNORECASE)
            if tit_match: title = tit_match.group(1).strip()
        elif std_match:
            pack = std_match.group(1)
            title = clean_text
            title = re.sub(r'^.*?#(?:[0-9]+)\s*', '', title)
            title = re.sub(r'^[0-9]+x\s+', '', title)
            title = re.sub(r'^\[\s*[\d\.]+[a-zA-Z]+\s*\]\s*', '', title)
            title = title.strip()
            sz_match = re.search(r'\b(\d+(?:\.\d+)?\s*[MGT]B?)\b', clean_text, re.IGNORECASE)
            if sz_match: size = sz_match.group(1).replace(" ", "")

        if title and len(title) > 5:
            resolution, year = "Any", "Any"
            res_match = re.search(r'(2160p|1080p|720p|480p)', title, re.IGNORECASE)
            if res_match: resolution = res_match.group(1)
            yr_match = re.search(r'(19\d\d|20\d\d)', title)
            if yr_match: year = yr_match.group(1)
            spd_match = re.search(r'avg:\s*([\d\.]+\s*[KMGT]?i?B\/s)', clean_text, re.IGNORECASE)
            if spd_match: speed = spd_match.group(1).replace(" ", "")

            timestamp = time.time()
            self.gui_app.db.add_pack(title, bot, pack, resolution, year, timestamp, size, speed, server=self.server_str)
            self.gui_app.after(0, self.gui_app.update_db_stats_ui)

    def connection_lost(self, exc):
        self.gui_app.log(f"[System] Disconnected from {self.server_str}.")
        self.gui_app.after(0, self.gui_app.handle_server_disconnect, self.server_str)


class XDCCApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CipherStream XDCC Multi Client - V1.0.1 BETA")
        self.geometry("1400x900")

        self.current_poster_ref = None

        self.alien_icon = None
        self.load_alien_icon()
        self.set_window_icon(self)

        self.config_file = "xdcc_config.json"
        self.config = {
            "theme": "Dark",
            "servers": {},
            "api_keys": {
                "tmdb": "",
                "rawg": ""
            }
        }
        self.load_config()

        # Apply persistent theme mode
        initial_theme = self.config.get("theme", "Dark")
        ctk.set_appearance_mode(initial_theme)

        self.dl_path = r"\\WIN-RUBBERDUCK\wr-uhdd\IRC XDCC Downloader\PythonVersion"
        if not os.path.exists(self.dl_path):
            try:
                os.makedirs(self.dl_path, exist_ok=True)
            except:
                self.dl_path = os.getcwd()

        self.db_path = os.getcwd()
        self.db = DatabaseManager(self.db_path)
        self.db.fix_old_timestamps()

        self.connections = {}
        self.is_connected = False
        self.active_transfers_widgets = {}
        
        self.joined_channels = {}
        self.chat_history = {}
        self.channel_nicks = {}
        
        self.chat_window = None
        self.net_mgr_win = None
        self.instructions_win = None
        
        self.log_history = [] 

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=3)
        self.grid_rowconfigure(3, weight=2)

        # Top Control Frame
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        server_keys = list(self.config["servers"].keys())
        self.server_combo = ctk.CTkComboBox(top_frame, values=server_keys if server_keys else [""], width=170)
        self.server_combo.pack(side="left", padx=2)
        if server_keys:
            self.server_combo.set(server_keys[0])
        else:
            self.server_combo.set("")

        self.conn_selected_btn = ctk.CTkButton(top_frame, text="Connect Selected", width=120, fg_color="#2e7d32", command=self.connect_selected_server)
        self.conn_selected_btn.pack(side="left", padx=2)

        self.servers_btn = ctk.CTkButton(top_frame, text="Network & API Settings", width=155, fg_color="#37474f", command=self.open_network_manager)
        self.servers_btn.pack(side="left", padx=2)

        self.conn_btn = ctk.CTkButton(top_frame, text="Connect All", width=95, command=self.toggle_connection)
        self.conn_btn.pack(side="left", padx=5)

        self.chat_win_btn = ctk.CTkButton(top_frame, text="Channel Chat", width=100, fg_color="purple", command=self.open_chat_window)
        self.chat_win_btn.pack(side="left", padx=5)

        # Instructions Button
        self.instr_btn = ctk.CTkButton(top_frame, text="Instructions", width=100, fg_color="#0288d1", command=self.open_instructions)
        self.instr_btn.pack(side="left", padx=5)

        # Theme Switcher Selector
        ctk.CTkLabel(top_frame, text="Theme:").pack(side="left", padx=(10, 2))
        self.theme_combo = ctk.CTkComboBox(top_frame, values=["Dark", "Light", "System"], width=90, command=self.change_theme_mode)
        self.theme_combo.pack(side="left", padx=2)
        self.theme_combo.set(initial_theme)

        # Path Frame
        path_frame = ctk.CTkFrame(self)
        path_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=2)

        ctk.CTkLabel(path_frame, text="Save To:").pack(side="left", padx=3)
        self.path_entry = ctk.CTkEntry(path_frame, width=380)
        self.path_entry.pack(side="left", padx=3)
        self.path_entry.insert(0, self.dl_path)

        self.browse_btn = ctk.CTkButton(path_frame, text="Browse", width=65, command=self.browse_dl_path)
        self.browse_btn.pack(side="left", padx=3)

        self.disk_lbl = ctk.CTkLabel(path_frame, text="Disk Free: Loading...", font=("Consolas", 11), text_color="#81d4fa")
        self.disk_lbl.pack(side="right", padx=10)

        # Main Layout Frame
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_rowconfigure(6, weight=1)
        main_frame.grid_rowconfigure(9, weight=1)

        db_info_frame = ctk.CTkFrame(main_frame, fg_color="#1f1f1f")
        db_info_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=3)

        self.db_stats_lbl = ctk.CTkLabel(db_info_frame, text="DB Stats: Loading...", font=("Consolas", 11), text_color="#90caf9")
        self.db_stats_lbl.pack(side="left", padx=10)

        self.vacuum_btn = ctk.CTkButton(db_info_frame, text="Optimize DB", width=90, height=20, fg_color="#37474f", command=self.optimize_database)
        self.vacuum_btn.pack(side="right", padx=5)

        search_bar = ctk.CTkFrame(main_frame)
        search_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.search_entry = ctk.CTkEntry(search_bar, placeholder_text="Search title...", width=160)
        self.search_entry.pack(side="left", padx=2)
        
        self.search_srv_combo = ctk.CTkComboBox(search_bar, values=["All Servers"], width=150)
        self.search_srv_combo.pack(side="left", padx=2)
        self.search_srv_combo.set("All Servers")

        self.res_combo = ctk.CTkComboBox(search_bar, values=["Any", "2160p", "1080p", "720p", "480p"], width=80)
        self.res_combo.pack(side="left", padx=2)
        self.res_combo.set("Any")
        self.codec_combo = ctk.CTkComboBox(search_bar, values=["Any", "x264/h264", "x265/HEVC"], width=95)
        self.codec_combo.pack(side="left", padx=2)
        self.codec_combo.set("Any")
        self.year_entry = ctk.CTkEntry(search_bar, placeholder_text="Year", width=50)
        self.year_entry.pack(side="left", padx=2)
        self.sort_combo = ctk.CTkComboBox(search_bar, values=["Name (A-Z)", "Name (Z-A)", "Newest First", "Oldest First"], width=120)
        self.sort_combo.pack(side="left", padx=2)
        self.sort_combo.set("Name (A-Z)")
        self.unique_var = ctk.IntVar(value=0)
        self.unique_chk = ctk.CTkCheckBox(search_bar, text="Unique", variable=self.unique_var, width=55)
        self.unique_chk.pack(side="left", padx=2)
        self.search_btn = ctk.CTkButton(search_bar, text="Search", width=70, command=self.run_search)
        self.search_btn.pack(side="left", padx=5)

        lb_bg = "#ffffff" if initial_theme.lower() == "light" else "#2b2b2b"
        lb_fg = "#000000" if initial_theme.lower() == "light" else "white"

        ctk.CTkLabel(main_frame, text="Search Results:").grid(row=2, column=0, sticky="w", padx=5)
        res_container = tk.Frame(main_frame, bg=lb_bg)
        res_container.grid(row=3, column=0, sticky="nsew", padx=5, pady=2)
        self.results_list = tk.Listbox(res_container, bg=lb_bg, fg=lb_fg, selectbackground="#1f538d", highlightthickness=0, borderwidth=0, font=("Consolas", 10), selectmode=tk.EXTENDED, exportselection=False)
        self.results_list.bind("<<ListboxSelect>>", self.on_search_select_event)
        self.results_list.bind("<Double-Button-1>", lambda event: self.add_to_queue())
        res_scroll = tk.Scrollbar(res_container, orient="vertical", command=self.results_list.yview)
        self.results_list.configure(yscrollcommand=res_scroll.set)
        self.results_list.pack(side="left", fill="both", expand=True)
        res_scroll.pack(side="right", fill="y")

        btn_bar1 = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_bar1.grid(row=4, column=0, sticky="ew", pady=2)
        self.add_q_btn = ctk.CTkButton(btn_bar1, text="Add Selected to Queue", command=self.add_to_queue)
        self.add_q_btn.pack(side="left", padx=2)

        ctk.CTkLabel(main_frame, text="Staging Queue (Pending):").grid(row=5, column=0, sticky="w", padx=5)
        q_container = tk.Frame(main_frame, bg=lb_bg)
        q_container.grid(row=6, column=0, sticky="nsew", padx=5, pady=2)
        self.queue_list = tk.Listbox(q_container, bg=lb_bg, fg=lb_fg, selectbackground="#1f538d", highlightthickness=0, borderwidth=0, font=("Consolas", 10), selectmode=tk.EXTENDED, exportselection=False)
        self.queue_list.bind("<Double-Button-1>", lambda event: self.remove_from_queue())
        q_scroll = tk.Scrollbar(q_container, orient="vertical", command=self.queue_list.yview)
        self.queue_list.configure(yscrollcommand=q_scroll.set)
        self.queue_list.pack(side="left", fill="both", expand=True)
        q_scroll.pack(side="right", fill="y")

        btn_bar2 = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_bar2.grid(row=7, column=0, sticky="ew", pady=2)
        self.dl_all_btn = ctk.CTkButton(btn_bar2, text="Download All (Push to Active)", command=self.push_queue_to_active)
        self.dl_all_btn.pack(side="left", padx=2)
        self.check_status_btn = ctk.CTkButton(btn_bar2, text="Check Bot Status", fg_color="#37474f", command=self.update_queue_bot_status)
        self.check_status_btn.pack(side="left", padx=2)
        self.rem_q_btn = ctk.CTkButton(btn_bar2, text="Remove Selected", fg_color="firebrick", command=self.remove_from_queue)
        self.rem_q_btn.pack(side="left", padx=5)
        self.clear_q_btn = ctk.CTkButton(btn_bar2, text="Clear All", fg_color="darkorange", command=self.clear_queue)
        self.clear_q_btn.pack(side="left", padx=2)

        ctk.CTkLabel(main_frame, text="Active Transfers Tracker & Individual Progress:").grid(row=8, column=0, sticky="w", padx=5)

        self.active_scrollable_frame = ctk.CTkScrollableFrame(main_frame, height=130, fg_color="#2b2b2b")
        self.active_scrollable_frame.grid(row=9, column=0, sticky="nsew", padx=5, pady=2)
        self.active_scrollable_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.grid(row=10, column=0, sticky="ew", padx=5, pady=2)
        self.progress_bar.set(0)

        btn_bar3 = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_bar3.grid(row=11, column=0, sticky="ew", pady=2)
        self.clear_comp_btn = ctk.CTkButton(btn_bar3, text="Clear Completed", command=self.clear_completed)
        self.clear_comp_btn.pack(side="left", padx=2)
        self.clear_unfin_btn = ctk.CTkButton(btn_bar3, text="Clear Unfinished", fg_color="darkorange", command=self.clear_unfinished)
        self.clear_unfin_btn.pack(side="left", padx=5)
        self.check_broken_btn = ctk.CTkButton(btn_bar3, text="Check Broken / Resume", fg_color="slate gray", command=self.check_broken_downloads)
        self.check_broken_btn.pack(side="left", padx=5)

        # Right Column
        meta_panel = ctk.CTkFrame(main_frame)
        meta_panel.grid(row=0, column=1, rowspan=12, sticky="nsew", padx=(10, 0), pady=3)
        meta_panel.grid_columnconfigure(0, weight=1)
        meta_panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(meta_panel, text="Live Release Preview (RAWG / TMDB / TVMaze)", font=("Arial", 14, "bold")).grid(row=0, column=0, pady=(10, 5))

        details_sub = ctk.CTkFrame(meta_panel)
        details_sub.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        details_sub.grid_columnconfigure(0, weight=1)
        details_sub.grid_rowconfigure(1, weight=1)

        self.poster_label = ctk.CTkLabel(details_sub, text="No Poster\nAvailable", width=150, height=220, fg_color=("gray70", "gray30"))
        self.poster_label.grid(row=0, column=0, pady=10)

        self.desc_box = ctk.CTkTextbox(details_sub, wrap="word", font=("Consolas", 11))
        self.desc_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.desc_box.insert("0.0", "Select any search result from the list to load live metadata preview and poster artwork.")
        self.desc_box.configure(state="disabled")

        # Bottom System Log Frame
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        bottom_frame.grid_rowconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=1)
        self.log_box = ctk.CTkTextbox(bottom_frame)
        self.log_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=2)

        self.log_box.tag_config("system", foreground="#81d4fa")
        self.log_box.tag_config("sent", foreground="#ffb74d")
        self.log_box.tag_config("dcc", foreground="#29b6f6")
        self.log_box.tag_config("notice", foreground="#ab47bc")
        self.log_box.tag_config("error", foreground="yellow", underline=True)
        self.log_box.tag_config("success", foreground="#00e676")
        self.log_box.tag_config("default", foreground="#e0e0e0")

        self.log_menu = tk.Menu(self.log_box, tearoff=0)
        self.log_menu.add_command(label="Copy Selected", command=self.copy_log_selection)
        self.log_menu.add_command(label="Copy All", command=self.copy_all_logs)
        self.log_box.bind("<Button-3>", self.show_log_context_menu)
        
        btn_bar4 = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_bar4.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.pop_log_btn = ctk.CTkButton(btn_bar4, text="Pop-Out Log Window", width=140, fg_color="#37474f", command=self.open_log_window)
        self.pop_log_btn.pack(side="left")

        self.update_db_stats_ui()
        self.update_disk_space_ui()
        self.update_server_combos()

        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_async_loop, daemon=True).start()
        
        self.check_for_updates()

    def change_theme_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode)
        self.config["theme"] = new_mode
        self.save_config()

        lb_bg = "#ffffff" if new_mode.lower() == "light" else "#2b2b2b"
        lb_fg = "#000000" if new_mode.lower() == "light" else "white"

        for lb in [self.results_list, self.queue_list]:
            try:
                lb.configure(bg=lb_bg, fg=lb_fg)
            except Exception:
                pass

        self.log(f"[System] UI appearance theme set to: {new_mode}")

    def open_instructions(self):
        if self.instructions_win is None or not self.instructions_win.winfo_exists():
            self.instructions_win = InstructionsWindow(self)
        else:
            self.instructions_win.focus()

    def check_for_updates(self):
        def _check():
            try:
                url = "https://raw.githubusercontent.com/DemiG33k/CipherStream_XDCC/main/version.json"
                req = urllib.request.Request(url, headers={'User-Agent': f'XDCC-Client/{CURRENT_VERSION}'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    latest_version = data.get("version", CURRENT_VERSION)
                    download_url = data.get("download_url", "")
                    
                    if self.is_newer_version(latest_version, CURRENT_VERSION):
                        self.after(0, lambda: self.prompt_update(latest_version, download_url))
            except Exception as e:
                self.log(f"[System] GitHub update check skipped or failed: {e}")
                
        threading.Thread(target=_check, daemon=True).start()

    def is_newer_version(self, latest, current):
        try:
            l = [int(x) for x in latest.lower().replace('v', '').split('.')]
            c = [int(x) for x in current.lower().replace('v', '').split('.')]
            return l > c
        except Exception:
            return False

    def prompt_update(self, version, url):
        if not url: return
        if messagebox.askyesno("Update Available", f"Version {version} is available!\n\nWould you like to download and update now?\n(Your database and config will remain intact)"):
            self.perform_update(url)

    def perform_update(self, url):
        self.log(f"[System] Downloading update from {url}...")
        def _download():
            try:
                import sys
                update_exe = "CipherStream_XDCC.exe"
                req = urllib.request.Request(url, headers={'User-Agent': f'XDCC-Client/{CURRENT_VERSION}'})
                with urllib.request.urlopen(req, timeout=30) as response, open(update_exe, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                
                bat_path = "update_client.bat"
                current_exe = os.path.basename(sys.executable)
                
                target_exe = current_exe if current_exe.lower().endswith(".exe") and "python" not in current_exe.lower() else "XDCC_Monitor.exe"

                bat_content = f"""@echo off
echo Updating XDCC Monitor...
timeout /t 3 /nobreak > NUL
move /Y "{update_exe}" "{target_exe}"
start "" "{target_exe}"
del "%~f0"
"""
                with open(bat_path, "w") as f:
                    f.write(bat_content)
                    
                self.log("[System] Update downloaded. Restarting application to apply...")
                import subprocess
                subprocess.Popen([bat_path], shell=True)
                self.after(1000, self.destroy)
            except Exception as e:
                self.after(0, lambda: self.log(f"[Error] Update failed: {e}"))
                
        threading.Thread(target=_download, daemon=True).start()

    def load_alien_icon(self):
        try:
            img_data = base64.b64decode(ALIEN_ICON_BASE64)
            image = Image.open(BytesIO(img_data))
            image.load()
            self.alien_icon = ImageTk.PhotoImage(image)
            self.iconphoto(True, self.alien_icon)
        except Exception as e:
            print(f"Failed to load icon: {e}")
            self.alien_icon = None

    def set_window_icon(self, window):
        if self.alien_icon:
            try:
                window.after(200, lambda: window.iconphoto(False, self.alien_icon))
            except Exception:
                pass

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    
                    if "theme" not in data:
                        data["theme"] = "Dark"

                    if "servers" in data:
                        if isinstance(data["servers"], list):
                            srv_dict = {}
                            for s in data["servers"]:
                                srv_dict[s] = {"auto_connect": True, "nick": "", "nickserv_pass": "", "nickserv_email": "", "channels": []}
                            data["servers"] = srv_dict
                        elif isinstance(data["servers"], dict):
                            for srv, srv_data in data["servers"].items():
                                if "channels" not in srv_data:
                                    srv_data["channels"] = []
                                if "nick" not in srv_data:
                                    srv_data["nick"] = ""
                                if "nickserv_pass" not in srv_data:
                                    srv_data["nickserv_pass"] = ""
                                if "nickserv_email" not in srv_data:
                                    srv_data["nickserv_email"] = ""
                                    
                    if "api_keys" not in data:
                        data["api_keys"] = {"tmdb": "", "rawg": ""}
                    else:
                        if "tmdb" not in data["api_keys"]:
                            data["api_keys"]["tmdb"] = ""
                        if "rawg" not in data["api_keys"]:
                            data["api_keys"]["rawg"] = ""

                    self.config.update(data)
            except Exception: pass

    def save_config(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception: pass

    def update_server_combos(self):
        srv_keys = list(self.config["servers"].keys())
        if srv_keys:
            self.server_combo.configure(values=srv_keys)
        else:
            self.server_combo.configure(values=[""])
            self.server_combo.set("")

        db_servers = self.db.get_servers()
        combined_srvs = sorted(list(set(["All Servers"] + srv_keys + db_servers)))
        self.search_srv_combo.configure(values=combined_srvs)

    def open_network_manager(self):
        if self.net_mgr_win is None or not self.net_mgr_win.winfo_exists():
            self.net_mgr_win = NetworkManagerWindow(self)
        else:
            self.net_mgr_win.focus()

    def open_log_window(self):
        if not hasattr(self, 'pop_log_win') or self.pop_log_win is None or not self.pop_log_win.winfo_exists():
            self.pop_log_win = LogWindow(self)
        else:
            self.pop_log_win.focus()

    def prompt_nick_registration(self, server_str=None):
        if threading.current_thread() != threading.main_thread():
            self.after(0, lambda: self.prompt_nick_registration(server_str))
            return

        srv_title = server_str if server_str else (self.server_combo.get() if self.server_combo.get() else "IRC Server")

        popup = ctk.CTkToplevel(self)
        popup.title(srv_title)
        popup.geometry("400x290")
        popup.minsize(400, 290)
        popup.attributes("-topmost", True)
        self.set_window_icon(popup)
        popup.grab_set()

        popup.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(popup, text=f"Register Nickname on {srv_title}", font=("Arial", 13, "bold"), text_color="orange").grid(row=0, column=0, pady=(15, 5))
        ctk.CTkLabel(popup, text="NickServ registration required for this server.", font=("Arial", 10), text_color="gray").grid(row=1, column=0, pady=(0, 10))

        pass_entry = ctk.CTkEntry(popup, placeholder_text="New Password", show="*", width=320, height=32)
        pass_entry.grid(row=2, column=0, pady=6)
        
        email_entry = ctk.CTkEntry(popup, placeholder_text="Email Address", width=320, height=32)
        email_entry.grid(row=3, column=0, pady=6)

        def submit_registration(event=None):
            password = pass_entry.get().strip()
            email = email_entry.get().strip()
            if password and email:
                if server_str and server_str in self.connections:
                    proto = self.connections[server_str]
                    proto.register_nickserv(password, email)
                else:
                    for srv_key, proto in self.connections.items():
                        if proto and proto.transport:
                            proto.register_nickserv(password, email)
                popup.destroy()
            else:
                self.log("[Error] Registration cancelled: Password and Email cannot be blank.")

        email_entry.bind("<Return>", submit_registration)
        ctk.CTkButton(popup, text="Register Nickname", command=submit_registration, fg_color="green", width=180, height=32).grid(row=4, column=0, pady=(15, 10))

    def add_channel_nicks(self, srv, chan, nicks):
        if threading.current_thread() != threading.main_thread():
            self.after(0, self.add_channel_nicks, srv, chan, nicks)
            return

        key = (srv, chan)
        if key not in self.channel_nicks:
            self.channel_nicks[key] = set()

        for raw_nick in nicks:
            if raw_nick:
                self.channel_nicks[key].add(raw_nick)

        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.refresh_nicklist(srv, chan)
            
        self.update_queue_bot_status()

    def remove_channel_nick(self, srv, chan, nick):
        if threading.current_thread() != threading.main_thread():
            self.after(0, self.remove_channel_nick, srv, chan, nick)
            return

        key = (srv, chan)
        if key in self.channel_nicks:
            clean_input = nick.lstrip("~&@%+")
            to_remove = [n for n in self.channel_nicks[key] if n.lstrip("~&@%+") == clean_input]
            for n in to_remove:
                self.channel_nicks[key].remove(n)

        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.refresh_nicklist(srv, chan)

    def is_bot_online(self, server, bot_nick):
        if server not in self.connections:
            return "DISCONNECTED"
        
        bot_clean = bot_nick.lower()
        for (srv, chan), nicks in self.channel_nicks.items():
            if srv == server:
                if any(n.lstrip("~&@%+").lower() == bot_clean for n in nicks):
                    return "ONLINE"
        return "OFFLINE"

    def update_queue_bot_status(self):
        if threading.current_thread() != threading.main_thread():
            self.after(0, self.update_queue_bot_status)
            return

        for idx in range(self.queue_list.size()):
            item_text = self.queue_list.get(idx)
            
            srv_match = re.search(r'\[Srv:\s*([^\]]+)\]', item_text)
            bot_match = re.search(r'\[Bot:\s*(.+?)\](?=\s*(?:\[Srv:|\bPack\b))', item_text)
            
            server = srv_match.group(1) if srv_match else (next(iter(self.connections.keys()), "") if self.connections else "")
            bot = bot_match.group(1) if bot_match else ""

            if server and bot:
                status = self.is_bot_online(server, bot)
                if status == "ONLINE":
                    self.queue_list.itemconfig(idx, fg="#00e676")
                elif status == "OFFLINE":
                    self.queue_list.itemconfig(idx, fg="#ef5350")
                else:
                    self.queue_list.itemconfig(idx, fg="#b0bec5")

    def update_disk_space_ui(self):
        try:
            total, used, free = shutil.disk_usage(self.dl_path)
            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)

            color = "#81d4fa"
            if free_gb < 10.0: color = "orange"
            if free_gb < 3.0: color = "#ff5252"

            self.disk_lbl.configure(text=f"Disk Free: {free_gb:.1f} GB / {total_gb:.1f} GB", text_color=color)
        except Exception:
            self.disk_lbl.configure(text="Disk Free: Unknown")

        self.after(10000, self.update_disk_space_ui)

    def open_chat_window(self):
        if self.chat_window is None or not self.chat_window.winfo_exists():
            self.chat_window = ChannelChatWindow(self)
            self.chat_window.protocol("WM_DELETE_WINDOW", self.close_chat_window)
        else:
            self.chat_window.focus()

    def close_chat_window(self):
        if self.chat_window:
            self.chat_window.destroy()
            self.chat_window = None

    def refresh_chat_window(self):
        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.update_server_list()

    def route_channel_message(self, srv, chan, nick, msg, msg_type="normal"):
        if threading.current_thread() != threading.main_thread():
            self.after(0, self.route_channel_message, srv, chan, nick, msg, msg_type)
            return

        clean_msg = re.sub(r'\x03(?:\d{1,2}(?:,\d{1,2})?)?|\x02|\x1f|\x16|\x0f', '', msg)
        
        if clean_msg.startswith("\x01ACTION ") and clean_msg.endswith("\x01"):
            clean_msg = clean_msg[8:-1]
            msg_type = "action"

        key = (srv, chan)
        if key not in self.chat_history:
            self.chat_history[key] = []

        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        entry = {
            "ts": timestamp,
            "nick": nick,
            "msg": clean_msg,
            "type": msg_type
        }
        
        self.chat_history[key].append(entry)
        if len(self.chat_history[key]) > 300:
            self.chat_history[key].pop(0)

        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.on_new_message(srv, chan, entry)

    def auto_extract_archive(self, file_path):
        if not os.path.exists(file_path):
            return

        base_dir, filename = os.path.split(file_path)
        ext = os.path.splitext(filename)[1].lower()
        extract_folder = os.path.join(base_dir, os.path.splitext(filename)[0])

        try:
            if ext == ".zip":
                self.log(f"[Auto-Extract] Extracting zip archive: {filename}...")
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_folder)
                self.log(f"[Auto-Extract Success] Extracted into folder: {extract_folder}")
            elif ext in [".tar", ".gz", ".bz2", ".xz", ".tgz"]:
                self.log(f"[Auto-Extract] Extracting tar archive: {filename}...")
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_folder)
                self.log(f"[Auto-Extract Success] Extracted into folder: {extract_folder}")
            elif ext in [".rar", ".7z"]:
                self.log(f"[Auto-Extract Notice] Downloaded {filename}. For .rar or .7z extraction, install 'rarfile' or 'py7zr' via pip.")
        except Exception as e:
            self.log(f"[Auto-Extract Error] Failed to extract {filename}: {e}")

    def update_db_stats_ui(self):
        stats = self.db.get_stats()
        text = f"DB Size: {stats['file_size']} | Indexed Packs: {stats['total_packs']:,} | Bots: {stats['unique_bots']} | Last Update: {stats['last_updated']}"
        self.db_stats_lbl.configure(text=text)
        self.update_server_combos()

    def optimize_database(self):
        self.db.optimize_db()
        self.update_db_stats_ui()
        self.log("[Database] Database optimized and defragmented successfully.")

    def show_log_context_menu(self, event):
        try:
            self.log_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.log_menu.grab_release()

    def copy_log_selection(self):
        try:
            selected_text = self.log_box.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.clipboard_clear()
            self.clipboard_append(selected_text)
        except tk.TclError:
            pass

    def copy_all_logs(self):
        all_text = self.log_box.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(all_text)

    def start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def log(self, message):
        if threading.current_thread() != threading.main_thread():
            self.after(0, self.log, message)
            return

        timestamp = datetime.datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
        formatted_msg = f"{timestamp} {message}\n"

        tag = "default"
        if "[Success]" in message or "[Auto-Extract Success]" in message: tag = "success"
        elif "[Error]" in message or "[KICK]" in message or "[Server Error" in message or "[Auto-Extract Error]" in message: tag = "error"
        elif "[DCC]" in message or "[DCC Resume]" in message or "[DCC Pause]" in message: tag = "dcc"
        elif "[Notice" in message or "[NickServ" in message or "[Auto-Extract Notice]" in message: tag = "notice"
        elif "[Sent]" in message or "[Search]" in message: tag = "sent"
        elif "[System]" in message or "[MODE]" in message or "[Topic" in message or "[Database]" in message or "[Auto-Extract]" in message: tag = "system"

        self.log_box.insert("end", formatted_msg, tag)
        self.log_box.see("end")
        
        self.log_history.append((formatted_msg, tag))
        if len(self.log_history) > 2000:
            self.log_history.pop(0)

        if hasattr(self, 'pop_log_win') and self.pop_log_win and self.pop_log_win.winfo_exists():
            active_filter = self.pop_log_win.filter_var.get()
            if active_filter == "All Logs" or active_filter in formatted_msg:
                self.pop_log_win.log_box.configure(state="normal")
                self.pop_log_win.log_box.insert("end", formatted_msg, tag)
                self.pop_log_win.log_box.see("end")
                self.pop_log_win.log_box.configure(state="disabled")

        try:
            with open("xdcc_debug.log", "a", encoding="utf-8") as f:
                f.write(formatted_msg)
        except Exception:
            pass

    def browse_dl_path(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.dl_path = dir_path
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, dir_path)
            self.update_disk_space_ui()
            self.log(f"[System] Download directory updated to: {dir_path}")

    def connect_selected_server(self):
        selected_srv = self.server_combo.get().strip()
        if not selected_srv:
            self.log("[Error] No server selected in dropdown.")
            return

        if selected_srv in self.connections:
            self.log(f"[System] Already connected to {selected_srv}.")
            return

        if ":" in selected_srv:
            srv, port_str = selected_srv.split(":", 1)
            port = int(port_str)
        else:
            srv, port = selected_srv, 6667
            selected_srv = f"{srv}:{port}"

        asyncio.run_coroutine_threadsafe(self.async_connect_server(selected_srv, srv, port), self.loop)
        self.is_connected = True
        self.conn_btn.configure(text="Disconnect All", fg_color="firebrick")

    def toggle_connection(self):
        if not self.is_connected:
            to_connect = [srv for srv, data in self.config["servers"].items() if data.get("auto_connect", True)]
            if not to_connect and self.server_combo.get():
                to_connect = [self.server_combo.get()]

            if not to_connect:
                self.log("[Error] No servers enabled for connection.")
                return

            for srv_str in to_connect:
                if ":" in srv_str:
                    srv, port_str = srv_str.split(":", 1)
                    port = int(port_str)
                else:
                    srv, port = srv_str, 6667
                    srv_str = f"{srv}:{port}"

                asyncio.run_coroutine_threadsafe(self.async_connect_server(srv_str, srv, port), self.loop)

            self.is_connected = True
            self.conn_btn.configure(text="Disconnect All", fg_color="firebrick")
        else:
            self.handle_disconnect_all()

    async def async_connect_server(self, srv_key, server, port):
        proto = IRCClient(self, srv_key)
        
        if not proto.nick:
            self.log(f"[Error] No Nick configured for {srv_key} in Network Configuration.")
            return

        self.log(f"[System] Connecting to {server}:{port} as {proto.nick}...")
        try:
            _, transport = await self.loop.create_connection(lambda: proto, server, port)
            self.connections[srv_key] = proto
            self.after(0, self.refresh_chat_window)
        except Exception as e:
            self.log(f"[Connection Error ({srv_key})] {e}")

    def handle_server_disconnect(self, srv_key):
        if srv_key in self.connections:
            del self.connections[srv_key]
        if srv_key in self.joined_channels:
            del self.joined_channels[srv_key]
        
        self.refresh_chat_window()
        self.update_queue_bot_status()

        if not self.connections:
            self.is_connected = False
            self.conn_btn.configure(text="Connect All", fg_color=["#3b8ed0", "#1f538d"])

    def handle_disconnect_all(self):
        self.is_connected = False
        
        for srv_key, proto in list(self.connections.items()):
            if proto and proto.transport:
                try: proto.send("QUIT :User disconnected")
                except Exception: pass
                try: proto.transport.abort()
                except Exception: pass

        self.connections.clear()
        self.joined_channels.clear()
        self.channel_nicks.clear()
        self.chat_history.clear()

        if self.chat_window and self.chat_window.winfo_exists():
            self.chat_window.clear_display()
            self.chat_window.update_server_list()

        for transfer_key, widget_data in self.active_transfers_widgets.items():
            writer = widget_data.get("writer")
            if writer:
                try: writer.close()
                except Exception: pass
            task = widget_data.get("task")
            if task and not task.done():
                task.cancel()

        self.conn_btn.configure(text="Connect All", fg_color=["#3b8ed0", "#1f538d"])
        self.update_queue_bot_status()
        self.log("[System] Forcefully disconnected all IRC servers and stopped all DCC transfers.")

    def run_search(self):
        query = self.search_entry.get().strip()
        srv_filter = self.search_srv_combo.get()
        res_filter = self.res_combo.get()
        codec_filter = self.codec_combo.get()
        year_filter = self.year_entry.get().strip()
        sort_order = self.sort_combo.get()
        is_unique = self.unique_var.get()

        self.results_list.delete(0, tk.END)
        cursor = self.db.conn.cursor()
        sql = "SELECT bot, pack_num, title, size, speed, server FROM packs WHERE 1=1"
        params = []

        if query:
            for w in query.split():
                sql += " AND title LIKE ?"
                params.append(f"%{w}%")
        if srv_filter and srv_filter != "All Servers":
            sql += " AND server = ?"
            params.append(srv_filter)
        if res_filter != "Any":
            sql += " AND resolution = ?"
            params.append(res_filter)
        if year_filter:
            sql += " AND year = ?"
            params.append(year_filter)
        if is_unique:
            sql += " GROUP BY title"

        if sort_order == "Name (A-Z)": sql += " ORDER BY title ASC"
        elif sort_order == "Name (Z-A)": sql += " ORDER BY title DESC"
        elif sort_order == "Newest First": sql += " ORDER BY timestamp DESC"
        elif sort_order == "Oldest First": sql += " ORDER BY timestamp ASC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        matched_count = 0

        for row in rows:
            bot, pack, title, size, speed, srv = row
            title_lower = title.lower()

            if codec_filter == "x264/h264" and not ("x264" in title_lower or "h264" in title_lower): continue
            if codec_filter == "x265/HEVC" and not ("x265" in title_lower or "hevc" in title_lower): continue

            srv_str = f" [Srv: {srv}]" if srv else ""
            line = f"[Bot: {bot}]{srv_str} Pack #{pack} ({size}) | {title}"
            self.results_list.insert(tk.END, line)
            matched_count += 1

        self.log(f"[Search] Found {matched_count} matching result(s).")
        self.update_db_stats_ui()

    def add_to_queue(self):
        selected_indices = self.results_list.curselection()
        if not selected_indices:
            self.log("[Error] No item selected from search results.")
            return

        for i in selected_indices:
            line = self.results_list.get(i)
            self.queue_list.insert(tk.END, line)
            
        self.update_queue_bot_status()
        self.log(f"[System] Added {len(selected_indices)} item(s) to Staging Queue.")

    def remove_from_queue(self):
        selected_indices = self.queue_list.curselection()
        for i in reversed(selected_indices):
            self.queue_list.delete(i)
        self.update_queue_bot_status()

    def clear_queue(self):
        self.queue_list.delete(0, tk.END)
        self.log("[System] Cleared all items from Staging Queue.")

    def push_queue_to_active(self):
        queue_items = self.queue_list.get(0, tk.END)
        if not queue_items:
            self.log("[Error] Staging Queue is empty.")
            return

        def send_sequentially(index=0):
            if index >= len(queue_items):
                self.log("[System] Batch queue sequence completed.")
                return

            line = queue_items[index]
            bot_match = re.search(r'\[Bot:\s*(.+?)\](?=\s*(?:\[Srv:|\bPack\b))', line) or re.search(r'\[(.*?)\]\s+Pack\s+#(\d+)', line)
            pack_match = re.search(r'Pack\s+#(\d+)', line)
            srv_match = re.search(r'\[Srv:\s*([^\]]+)\]', line)

            if bot_match and pack_match:
                bot = bot_match.group(1)
                pack = pack_match.group(1)
                target_srv = srv_match.group(1) if srv_match else None
                
                transfer_key = f"{bot.lower()}_{pack}"

                proto = None
                if target_srv and target_srv in self.connections:
                    proto = self.connections[target_srv]
                elif not target_srv and self.connections:
                    proto = next(iter(self.connections.values()))

                if not proto or not proto.transport:
                    err_srv = target_srv if target_srv else "Server"
                    self.log(f"[Error] Cannot request pack #{pack} from {bot}: Network '{err_srv}' is not connected!")
                    self.after(1000, lambda: send_sequentially(index + 1))
                    return

                card_frame = ctk.CTkFrame(self.active_scrollable_frame, fg_color="#333333")
                card_frame.pack(fill="x", padx=5, pady=3)

                lbl = ctk.CTkLabel(card_frame, text=f"Status: Requested... [0%] | {line}", font=("Consolas", 11), anchor="w")
                lbl.pack(side="top", fill="x", padx=5, pady=2)

                pbar = ctk.CTkProgressBar(card_frame, height=8)
                pbar.pack(side="top", fill="x", padx=5, pady=2)
                pbar.set(0)

                ctrl_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
                ctrl_frame.pack(side="top", fill="x", padx=2, pady=2)

                pause_btn = ctk.CTkButton(ctrl_frame, text="Pause", width=60, height=22, command=lambda k=transfer_key: self.pause_transfer(k))
                pause_btn.pack(side="left", padx=2)
                resume_btn = ctk.CTkButton(ctrl_frame, text="Resume", width=60, height=22, fg_color="green", command=lambda b=bot, p=pack, k=transfer_key: self.resume_transfer(b, p, k))
                resume_btn.pack(side="left", padx=2)
                stop_btn = ctk.CTkButton(ctrl_frame, text="Stop", width=60, height=22, fg_color="firebrick", command=lambda k=transfer_key: self.stop_transfer(k))
                stop_btn.pack(side="left", padx=2)

                self.active_transfers_widgets[transfer_key] = {
                    "frame": card_frame, "label": lbl, "pbar": pbar, "line": line,
                    "completed": False, "paused": False, "stopped": False, "task": None,
                    "writer": None, "bot": bot, "pack": pack, "server": target_srv,
                    "pause_btn": pause_btn, "resume_btn": resume_btn, "stop_btn": stop_btn
                }

                proto.send(f"PRIVMSG {bot} :XDCC SEND {pack}")
                self.log(f"[{proto.server_str} Sent] Requested Pack #{pack} from {bot}")

            self.after(4000, lambda: send_sequentially(index + 1))

        send_sequentially(0)
        self.queue_list.delete(0, tk.END)
        self.log("[System] Pushing queue to active tracker (4s stagger active)...")

    def pause_transfer(self, transfer_key):
        if transfer_key in self.active_transfers_widgets:
            widget_data = self.active_transfers_widgets[transfer_key]
            widget_data["paused"] = True
            widget_data["label"].configure(text=f"Status: Paused | {widget_data['line']}")
            self.log(f"[System] Paused transfer: {transfer_key}")

    def resume_transfer(self, bot, pack, transfer_key):
        if transfer_key in self.active_transfers_widgets:
            widget_data = self.active_transfers_widgets[transfer_key]
            widget_data["paused"] = False
            widget_data["stopped"] = False
            widget_data["task"] = None
            widget_data["label"].configure(text=f"Status: Resuming request... | {widget_data['line']}")

            target_srv = widget_data.get("server")
            proto = self.connections.get(target_srv) if target_srv in self.connections else next(iter(self.connections.values()), None)
            
            if proto:
                proto.send(f"PRIVMSG {bot} :XDCC SEND {pack}")
                self.log(f"[{proto.server_str} Sent] Resuming/Re-requesting Pack #{pack} from {bot}")

    def stop_transfer(self, transfer_key):
        if transfer_key in self.active_transfers_widgets:
            widget_data = self.active_transfers_widgets[transfer_key]
            widget_data["stopped"] = True

            writer = widget_data.get("writer")
            if writer:
                try: writer.close()
                except Exception: pass

            task = widget_data.get("task")
            if task and not task.done():
                task.cancel()

            widget_data["label"].configure(text=f"Status: Stopped | {widget_data['line']}")
            self.log(f"[System] Stopped transfer: {transfer_key}")

    def update_active_status(self, transfer_key, new_status):
        if threading.current_thread() != threading.main_thread():
            self.after(0, self.update_active_status, transfer_key, new_status)
            return

        if transfer_key in self.active_transfers_widgets:
            widget_data = self.active_transfers_widgets[transfer_key]
            if not widget_data["completed"]:
                widget_data["label"].configure(text=f"Status: {new_status} | {widget_data['line']}")

    def update_active_progress(self, transfer_key, received, total, custom_status="", speed_bps=0.0):
        if threading.current_thread() != threading.main_thread():
            self.after(0, self.update_active_progress, transfer_key, received, total, custom_status, speed_bps)
            return

        percent = (received / total) * 100 if total > 0 else 0
        self.progress_bar.set(percent / 100.0)

        speed_str = f"{speed_bps / (1024 * 1024):.2f} MB/s" if speed_bps > 1024 * 1024 else f"{speed_bps / 1024:.2f} KB/s"
        if speed_bps > 0:
            eta_secs = int((total - received) / speed_bps)
            mins, secs = divmod(eta_secs, 60)
            eta_str = f"ETA {mins}m {secs}s"
        else:
            eta_str = "ETA calculating..."

        status_text = custom_status if custom_status else f"[{percent:.1f}%] {speed_str} | {eta_str}"

        if transfer_key in self.active_transfers_widgets:
            widget_data = self.active_transfers_widgets[transfer_key]
            if not widget_data["completed"]:
                widget_data["pbar"].set(percent / 100.0)
                widget_data["label"].configure(text=f"Status: {status_text} | {widget_data['line']}")

    def update_active_complete(self, transfer_key, total, file_path=None):
        if threading.current_thread() != threading.main_thread():
            self.after(0, self.update_active_complete, transfer_key, total, file_path)
            return

        self.progress_bar.set(1.0)
        if transfer_key in self.active_transfers_widgets:
            widget_data = self.active_transfers_widgets[transfer_key]
            widget_data["completed"] = True
            widget_data["pbar"].set(1.0)
            widget_data["label"].configure(text=f"Status: Completed! (100%) | {widget_data['line']}")

            for btn_key in ["pause_btn", "resume_btn", "stop_btn"]:
                btn = widget_data.get(btn_key)
                if btn and btn.winfo_exists():
                    btn.configure(state="disabled")

        self.update_disk_space_ui()
        if file_path:
            self.auto_extract_archive(file_path)

    def clear_completed(self):
        to_delete = []
        for key, widget_data in self.active_transfers_widgets.items():
            if widget_data["completed"]:
                widget_data["frame"].destroy()
                to_delete.append(key)
        for key in to_delete:
            del self.active_transfers_widgets[key]
        self.progress_bar.set(0)
        self.log("[System] Cleared completed transfers from tracker.")

    def clear_unfinished(self):
        to_delete = []
        for key, widget_data in self.active_transfers_widgets.items():
            if not widget_data["completed"]:
                widget_data["frame"].destroy()
                to_delete.append(key)
        for key in to_delete:
            del self.active_transfers_widgets[key]
        self.progress_bar.set(0)
        self.log("[System] Cleared all unfinished/active transfers from tracker.")

    def check_broken_downloads(self):
        self.log("[System] Scanning download directory for broken or partial files...")
        count = 0
        if os.path.exists(self.dl_path):
            for file in os.listdir(self.dl_path):
                full_path = os.path.join(self.dl_path, file)
                if os.path.isfile(full_path):
                    sz = os.path.getsize(full_path)
                    if sz < 1024 * 1024 * 5:
                        self.log(f"[Check] Potential broken/small file found: {file} ({sz} bytes)")
                        count += 1
        messagebox.showinfo("Resume Checker", f"Scan complete. Found {count} small or partial file(s) in download directory.")

    def on_search_select_event(self, event):
        selection = self.results_list.curselection()
        if selection:
            raw_line = self.results_list.get(selection[0])
            self.on_search_select(raw_line)

    def clean_filename(self, raw_title):
        if "|" in raw_title:
            raw_title = raw_title.split("|")[-1]
            
        name = re.sub(r'\.(mkv|mp4|avi|iso|bin|tar|zip|rar)$', '', raw_title, flags=re.IGNORECASE)
        name = name.replace('.', ' ').replace('_', ' ')
        
        name = re.sub(r'\b(19\d\d|20\d\d)\b', '', name)
        name = re.sub(r'\s*\(\s*\)\s*', ' ', name)
        
        name = re.sub(r'\b(S\d+E\d+|\d{3,4}p|HEVC|x265|x264|WEB-DL|WEBRip|BluRay|DSNP|AMZN|MeGusta|RAWR|NTb|sylix|DH)\b.*', '', name, flags=re.IGNORECASE)
        return name.strip()

    def on_search_select(self, raw_line_text):
        clean_title = self.clean_filename(raw_line_text)
        self.update_desc_ui(f"Fetching live metadata for: {clean_title}...")
        threading.Thread(target=self._query_api_task, args=(clean_title, raw_line_text), daemon=True).start()

    def _query_api_task(self, title, raw_line_text):
        try:
            encoded_title = urllib.parse.quote(title)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            desc_text = ""
            poster_url = None
            
            tmdb_key = self.config.get("api_keys", {}).get("tmdb", "").strip()
            rawg_key = self.config.get("api_keys", {}).get("rawg", "").strip()

            is_game = any(k in raw_line_text.lower() for k in ['.iso', '.bin', '.exe', '.tar', '.zip', '.rar', 'game', 'update', 'skidrow', 'reloaded', 'tenoke', 'gemupc'])

            if is_game and rawg_key:
                try:
                    url = f"https://api.rawg.io/api/games?key={rawg_key}&search={encoded_title}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
                        data = json.loads(response.read().decode())
                        results = data.get("results", [])
                        if results:
                            game = results[0]
                            game_name = game.get('name', 'Unknown')
                            released = game.get('released', 'N/A')
                            rating = game.get('rating', 'N/A')
                            poster_url = game.get('background_image')
                            desc_text = f"**{game_name}** (Released: {released})\nRating: {rating}/5\n\n(Game metadata provided by RAWG)"
                except Exception as e:
                    self.log(f"[Metadata] RAWG query failed: {e}")

            if not desc_text and tmdb_key:
                try:
                    url = f"https://api.themoviedb.org/3/search/multi?api_key={tmdb_key}&query={encoded_title}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
                        data = json.loads(response.read().decode())
                        results = data.get("results", [])
                        if results:
                            item = results[0]
                            name = item.get('title') or item.get('name', 'Unknown')
                            overview = item.get('overview', 'No description available.')
                            release_date = item.get('release_date') or item.get('first_air_date', 'N/A')
                            poster_path = item.get('poster_path')
                            if poster_path:
                                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                            desc_text = f"**{name}** ({release_date})\n\n{overview}"
                except Exception as e:
                    self.log(f"[Metadata] TMDB query failed: {e}")

            if not desc_text:
                url = f"https://api.tvmaze.com/search/shows?q={encoded_title}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=6, context=ctx) as response:
                    results = json.loads(response.read().decode())
                    if not results:
                        self._render_fallback(title)
                        return
                    show_data = results[0].get('show', {})
                    show_name = show_data.get('name', 'Unknown')
                    summary = re.sub(r'<.*?>', '', show_data.get('summary', 'No description available.'))
                    genres = ", ".join(show_data.get('genres', []))
                    if show_data.get('image'):
                        poster_url = show_data['image'].get('medium')
                    desc_text = f"**{show_name}** (TV)\nGenres: {genres}\n\n{summary}"

            img_data = None
            if poster_url:
                try:
                    with urllib.request.urlopen(poster_url, timeout=6, context=ctx) as img_resp:
                        img_data = img_resp.read()
                except Exception as img_err:
                    self.log(f"Failed to fetch remote poster image: {img_err}")

            self.after(0, lambda: self.render_metadata(desc_text, img_data))

        except Exception as e:
            error_msg = f"Could not retrieve metadata for '{title}'.\nReason: {str(e)}"
            self.after(0, lambda: self.update_desc_ui(error_msg))

    def _render_fallback(self, title):
        fallback_text = f"Title: {title}\n\nNo online metadata matched.\nThe release file is fully ready for staging and download queue insertion."
        self.after(0, lambda: self.render_metadata(fallback_text, None))

    def update_desc_ui(self, text):
        self.desc_box.configure(state="normal")
        self.desc_box.delete("0.0", "end")
        self.desc_box.insert("0.0", text)
        self.desc_box.configure(state="disabled")

    def render_metadata(self, desc_text, img_bytes):
        self.update_desc_ui(desc_text)
        
        if img_bytes:
            try:
                pil_image = Image.open(BytesIO(img_bytes))
                pil_image = pil_image.resize((150, 220), Image.Resampling.LANCZOS)
                
                self.current_poster_ref = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(150, 220))
                self.poster_label.configure(image=self.current_poster_ref, text="")
            except Exception as e:
                self.log(f"Error processing image bytes: {e}")
                self.current_poster_ref = None
                self.poster_label.configure(image="", text="Image Error")
        else:
            self.current_poster_ref = None
            self.poster_label.configure(image="", text="No Poster\nAvailable")


if __name__ == "__main__":
    app = XDCCApp()
    app.mainloop()
