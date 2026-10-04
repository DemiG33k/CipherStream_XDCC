# CipherStream_XDCC
Cipher Stream XDCC Multi Client 🚀

Cipher Stream XDCC is a feature-rich, modern, and asynchronous multi-server IRC XDCC client and downloader built in Python using CustomTkinter, asyncio, and SQLite. Designed for media enthusiasts and power users, it streamlines searching, queueing, downloading, and managing files from IRC XDCC bots with automated unpacking, real-time chat, and live metadata previews.

✨ Key Features

🌐 Multi-Server & Network Management

Concurrent Connections: Connect to multiple IRC networks simultaneously.

Auto-Connect & Channel Auto-Join: Automatically connects to configured servers and joins designated channels upon startup.

NickServ Authentication: Built-in automated NickServ identification (IDENTIFY) and account registration flow with built-in 30-second nickname age handling.

Network & API Manager UI: Easily add, edit, or remove IRC servers, configure ports, nicknames, passwords, and global API keys.

📦 Robust Search & Local SQLite Indexing

Local Pack Caching: Indexes packs into a local SQLite database (xdcc_database.db) for instant offline searching.

Advanced Filters: Filter search results by server, resolution (2160p, 1080p, 720p, 480p), release year, codecs (x264/h265), and a toggle for unique titles.

Database Maintenance: Built-in vacuum optimization (VACUUM) to keep your database lean and fast.

⚡ Advanced Download & Queue Manager

Staging Queue: Stage packs from search results before pushing them into an active batch download queue with staggered delays.

Active Transfer Tracking: Real-time progress bars, speed monitoring (MB/s or KB/s), estimated time remaining (ETA), and individual card controls.

DCC Pause / Resume / Stop: Full support for DCC file transfers with automatic resume prompting for partial/interrupted downloads.

Auto-Extraction: Automatically detects and extracts downloaded .zip, .tar, .gz, .bz2, .xz, or .tgz archives into organized folders upon completion.

🎬 Live Media & Game Metadata Preview

Multi-API Integration: Integrates with TMDB (Movies & TV Shows), RAWG (PC Games), and TVmaze to fetch release summaries, ratings, release dates, and high-resolution posters dynamically when selecting search results.

💬 Multi-Server IRC Channel Chat

Interactive Chat Room: Full-featured channel chat window with server and channel switcher dropdowns.

User List & Roles: Live user list showing operator (@, ~, &, %), voiced (+), and standard users with statistics.

Command Support: Supports common IRC commands (/join, /part, /nick, /msg, /me).

Color-Coded Logging: Color-tagged logging for system messages, DCC transfers, notices, errors, and chat outputs, complete with log pop-out views and context menus.

🛠️ Prerequisites & Installation

1. Requirements

Python 3.8 or higher.

Required Python packages:

pip install customtkinter pillow


2. Cloning & Running

Clone the repository and run the main application script:

git clone [https://github.com/DemiG33k/CipherStream-XDCC.git
cd CipherStream-XDCC
python CipherStream_XDCC.py


⚙️ Configuration

Upon first launch, the application creates an xdcc_config.json configuration file. You can configure your servers, nicknames, and optional global API keys directly through the Network & API Settings GUI window or by editing the JSON file:

{
    "servers": {
        "irc.server.net:6667": {
            "auto_connect": true,
            "nick": "YourNickname",
            "nickserv_pass": "YourPassword",
            "nickserv_email": "your@email.com",
            "channels": ["#yourchannel"]
        }
    },
    "api_keys": {
        "tmdb": "YOUR_TMDB_API_KEY",
        "rawg": "YOUR_RAWG_API_KEY"
    }
}


📦 Project Structure

CipherStream_XDCC.py — Main application entry point containing the full GUI implementation, asyncio network protocol handlers, SQLite database manager, and UI windows.

xdcc_database.db — Local SQLite cache for indexed XDCC pack lists (auto-generated).

xdcc_config.json — User network configurations and API keys (auto-generated).

🔄 Auto-Update Checker

The application includes a built-in update checker that pings a remote version manifest to notify you when newer releases are available on GitHub, featuring an automated update script runner.

📄 License

Distributed under the MIT License. See LICENSE for more information.
