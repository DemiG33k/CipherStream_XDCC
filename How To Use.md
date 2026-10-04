Here is the complete, exhaustive user manual for **Cipher Stream XDCC**. It covers everything from IRC basics and NickServ security to network setup, database searching, active transfer management, and API integration.

You can easily save this document as a professional PDF by copying the text into a document editor (like Microsoft Word, Google Docs, or Notion) and clicking **File > Export as PDF** (or **Print > Save as PDF**).

---

# Cipher Stream XDCC: Complete User Manual & Guide

## 1. Introduction: Understanding IRC, XDCC, and NickServ

If you are new to IRC and file-sharing protocols, understanding these foundational concepts will make navigating the application effortless:

* **IRC (Internet Relay Chat):** A classic, text-based communication system divided into different servers (networks) and chat rooms (called "channels", e.g., `#moviegods`).
* **XDCC:** A popular file-sharing system used on IRC networks. Instead of downloading files from a traditional website, you interact with automated computer programs called **bots** that host files and transfer them directly to you.
* **NickServ:** Because IRC does not have traditional password-protected user accounts built into its core protocol, networks use a security helper service called **NickServ**. NickServ allows you to "register" your chosen nickname with a password so nobody else can steal or impersonate your screen name while you are offline.
* **Important Note on Verification:** Some strict IRC networks require email verification. When registering your nickname for the first time, NickServ may email you a confirmation link or verification code that you must reply with in order to complete your registration.



---

## 2. Initial Setup: Network & NickServ Configuration

Before you can search for files or chat, you must configure your server connection and identity inside the application.

1. Launch **Cipher Stream XDCC** and click the **Network & API Settings** button near the top left of the main window.
2. On the left side of the Network Manager window, you will see a list of configured servers. You can select an existing one (such as `irc.abjects.net`) or type a new server address into the box and click **Add Server**.
3. Select your server to load its configuration on the right-hand side and fill out your identity:
* **Auto-Connect:** Check this box so the app connects to the server automatically upon startup.
* **Nickname:** Enter the unique screen name you want to use on the network.
* **NickServ Pass:** Create a secure password to lock and protect your nickname.
* **NickServ Email:** Enter your active email address. *(Keep an eye on your inbox in case the server sends a verification code or token).*
* **Auto-Join Channels:** Add the chat channels you want the app to enter automatically upon connection (e.g., `#moviegods`).


4. Click the green **Save Server Config** button at the bottom.
5. Close the settings window, select your server from the main screen dropdown menu, and click **Connect Selected** (or **Connect All**). Watch the system log at the bottom of the app to confirm successful connection and NickServ identification.

---

## 3. Navigating Channels & Chat

Once connected, your client automatically joins your configured channels where bots announce available files.

* **Channel Chat Window:** Click the **Channel Chat** button on the main toolbar to open the live chat interface.
* **User Lists & Roles:** The right-hand panel in the chat window displays all users currently in the channel, color-coded and sorted by privileges (Channel Ops `~&@%`, Voiced users `+`, and regular members).
* **Nick Completion:** Double-clicking any user's name in the user list will automatically insert their name or a direct mention into your chat input bar.
* **Standard IRC Commands:** You can type standard commands directly into the chat bar, such as:
* `/join #channelname` — Join a new channel.
* `/part #channelname` — Leave a current channel.
* `/nick NewNickname` — Change your active nickname.
* `/msg TargetUser message` — Send a private message.
* `/me action` — Send an action message.



---

## 4. Searching, Filtering, & Bot Status

As you stay connected to channels, the application automatically reads incoming announcements and indexes every pack into your local SQLite database (`xdcc_database.db`).

* **Search Bar:** Type keywords (e.g., movie names, game titles, or keywords) into the search entry box.
* **Advanced Filters:** Refine your search using the dropdown menus:
* **Resolution:** Filter by `2160p`, `1080p`, `720p`, or `480p`.
* **Codecs:** Filter by `x264/h264` or `x265/HEVC`.
* **Year:** Type a specific release year.
* **Server:** Filter results by a specific IRC network.
* **Unique Checkbox:** Check this to group and display unique titles only.


* **Bot Online Status Indicators:** When you add items to your Staging Queue, the bot names automatically change color based on their live presence in the chat channel:
* 🟢 **Green (`#00e676`):** The bot is currently online and present in the channel.
* 🔴 **Red (`#ef5350`):** The bot is offline or not detected in the channel.



---

## 5. Queue Management & Downloading

1. **Staging Queue:** Double-click any search result (or select multiple items and click **Add Selected to Queue**) to place them into your pending staging list.
2. **Push to Active:** Click **Download All (Push to Active)**. The app will initiate downloads with a built-in 4-second stagger between requests to prevent flooding the IRC server with commands.
3. **Active Transfers Tracker:** Watch your live progress in the active transfers panel:
* **Individual Controls:** Each transfer card features dedicated **Pause**, **Resume**, and **Stop** buttons.
* **DCC Resumes:** If a download is interrupted or paused, clicking **Resume** automatically negotiates a byte-resume (`DCC RESUME`) with the bot so you never lose your progress.
* **Auto-Extraction:** Once an archive file (such as `.zip`, `.tar`, `.gz`, `.tgz`) finishes downloading, the app automatically extracts its contents into a matching subfolder in your download directory.


4. **Disk Space Monitoring:** Keep an eye on the bottom-left disk space counter, which warns you if your drive gets low on free space.

---

## 6. Setting Up Global API Keys (TMDB & RAWG)

To enjoy rich metadata (synopses, release dates, ratings) and high-resolution posters on the right-hand preview panel when you click a search result, you can add two free API keys:

### 🎬 Part A: Get a TMDB API Key (For Movies & TV Shows)

1. Go to [themoviedb.org](https://www.themoviedb.org/) and create a free account.
2. Go to your account **Settings**, then click **API** on the left sidebar.
3. Request an API key (choose the **Developer** plan) and fill out the brief form (listing your project as personal or educational use).
4. Copy your generated **API Key (v3 auth)**.

### 🎮 Part B: Get a RAWG API Key (For PC & Console Games)

1. Go to [rawg.io](https://rawg.io/) and create a free account.
2. Navigate to their developer portal or API documentation section to generate your free personal API key.
3. Copy your key.

### 📥 Part C: Save the Keys in the App

1. Open the app and click **Network & API Settings**.
2. Switch to the tab labeled **API Keys (Global)**.
3. Paste your **TMDB API Key** and **RAWG API Key** into their respective fields.
4. Click **Save Global API Keys**.

Whenever you click on a search result from then on, official posters and rich summaries will load automatically!