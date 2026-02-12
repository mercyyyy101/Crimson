# Steam Accounts Bot

This is a starter Discord bot (Python) that lets members generate Steam accounts, track usage, and lets staff manage stock and reports.

Contents
- `bot.py` — main bot implementation using `discord.py` and `aiosqlite`.
- `requirements.txt` — Python dependencies.
- `.env.example` — example environment variables.

Quick start

1. Copy `.env.example` to `.env` and set `DISCORD_TOKEN`.
2. (Optional) set `BOOSTER_ROLE_ID` and `MEMBER_ROLE_ID` to the role IDs you use.
3. Install deps: `python -m pip install -r requirements.txt`.
4. Run: `python bot.py`.

Railway deploy

1. Push this repository to GitHub and create a Railway project.
2. Add environment variables to Railway from `.env`.
3. Use start command `python bot.py`.

Role IDs
- Booster: 1469733875709378674
- Member: 1471512804535046237

Notes
- Staff commands require the `Manage Guild` permission by default. You can set `STAFF_ROLE_ID` in the `.env` to allow a specific role.
- This project is a scaffold — test and extend the logic for bulk imports, better rate limits, error handling, and persistence as needed.
