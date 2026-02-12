import os
import aiosqlite
from datetime import datetime, date
from dotenv import load_dotenv

import discord
from discord import app_commands
from discord.ext import commands

# ───────── ENV ─────────
load_dotenv()

TOKEN = (os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN") or "").strip()
BOOSTER_ROLE_ID = int(os.getenv("BOOSTER_ROLE_ID") or 0)
STAFF_ROLE_ID = int(os.getenv("STAFF_ROLE_ID") or 0)
DB_PATH = os.getenv("DATABASE_PATH", "bot_data.db")

# ───────── BOT ─────────
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ───────── DATABASE ─────────
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            games TEXT,
            is_used INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS gens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS referrals (
            owner_id TEXT,
            code TEXT UNIQUE,
            uses INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS referral_uses (
            referrer_id TEXT,
            referred_id TEXT,
            used_at TEXT
        );
        """)
        await db.commit()

# ───────── HELPERS ─────────
def is_staff(member: discord.Member):
    if member.guild_permissions.manage_guild:
        return True
    if STAFF_ROLE_ID:
        return any(r.id == STAFF_ROLE_ID for r in member.roles)
    return False


def boost_count(member: discord.Member):
    return 1 if BOOSTER_ROLE_ID and any(r.id == BOOSTER_ROLE_ID for r in member.roles) else 0


async def daily_used(user_id: int):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM gens WHERE user_id=? AND DATE(created_at)=?",
            (str(user_id), today),
        )
        return (await cur.fetchone())[0]

# ───────── EVENTS ─────────
@bot.event
async def on_ready():
    await init_db()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

# ───────── SLASH COMMANDS ─────────

@bot.tree.command(name="steamaccount", description="Get a Steam account for a game")
@app_commands.describe(game="Game name")
async def steamaccount(interaction: discord.Interaction, game: str):
    user = interaction.user

    limit = 2
    if boost_count(user) == 1:
        limit = 4

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM referral_uses WHERE referred_id=?",
            (str(user.id),),
        )
        if (await cur.fetchone())[0] > 0:
            limit += 1

    if await daily_used(user.id) >= limit:
        await interaction.response.send_message(
            f"You reached your daily limit ({limit})", ephemeral=True
        )
        return

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, username, password, games FROM accounts WHERE is_used=0 AND games LIKE ? LIMIT 1",
            (f"%{game}%",),
        )
        row = await cur.fetchone()
        if not row:
            await interaction.response.send_message(
                "No accounts available for that game.", ephemeral=True
            )
            return

        acc_id, u, p, g = row
        await db.execute("UPDATE accounts SET is_used=1 WHERE id=?", (acc_id,))
        await db.execute(
            "INSERT INTO gens (user_id, created_at) VALUES (?,?)",
            (str(user.id), datetime.utcnow().isoformat()),
        )
        await db.commit()

    await interaction.response.send_message(
        "Account sent to your DMs!", ephemeral=True
    )
    await user.send(f"🎮 **{game}**\n```{u}:{p}```\nGames: {g}")

# ───────── STAFF COMMANDS ─────────

@bot.tree.command(name="addaccount", description="Add a Steam account")
@app_commands.checks.has_permissions(manage_guild=True)
async def addaccount(interaction: discord.Interaction, username: str, password: str, games: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO accounts (username, password, games) VALUES (?,?,?)",
            (username, password, games),
        )
        await db.commit()
    await interaction.response.send_message("Account added.", ephemeral=True)


@bot.tree.command(name="stock", description="Show remaining stock")
async def stock(interaction: discord.Interaction):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM accounts WHERE is_used=0")
        count = (await cur.fetchone())[0]
    await interaction.response.send_message(f"{count} accounts in stock.")

bot.run(TOKEN)


