import os
import discord
from discord.ext import commands, tasks
import requests
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# === Flask App to Keep Alive ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# === Discord Bot Setup ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

CHANNEL_ID = 1401420936271499305
CODES_FILE = "posted_codes.txt"

# === Utilities ===
def load_posted_codes():
    if not os.path.exists(CODES_FILE):
        return set()
    with open(CODES_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_posted_codes(all_codes):
    with open(CODES_FILE, "w") as f:
        for code in all_codes:
            f.write(code + "\n")

# === Scraping Functions ===
def get_genshin_codes():
    url = "https://genshin-impact.fandom.com/wiki/Promotional_Code"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="wikitable")
    if not table:
        return []

    codes = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 2:
            code = cols[0].text.strip()
            status = cols[-1].text.strip().lower()
            if any(word in status for word in ["active", "yes", "valid", "working", "currently", "available"]):
                codes.append(code)
    return codes

def get_zzz_codes():
    url = "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="wikitable")
    if not table:
        return []

    codes = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 2:
            code = cols[0].text.strip()
            status = cols[-1].text.strip().lower()
            if any(word in status for word in ["active", "yes", "valid", "working", "currently", "available"]):
                codes.append(code)
    return codes

# === Bot Events and Commands ===
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    auto_post_codes.start()

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command()
async def genshincode(ctx):
    codes = get_genshin_codes()
    if codes:
        await ctx.send("🎁 **Active Genshin Impact Codes:**\n" + "\n".join(codes))
    else:
        await ctx.send("😕 No active Genshin codes found.")

@bot.command()
async def zzzcode(ctx):
    codes = get_zzz_codes()
    if codes:
        await ctx.send("🎮 **Active Zenless Zone Zero Codes:**\n" + "\n".join(codes))
    else:
        await ctx.send("😕 No active ZZZ codes found.")

# === Auto Post Loop ===
@tasks.loop(hours=24)
async def auto_post_codes():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("⚠️ Channel not found.")
        return

    old_codes = load_posted_codes()
    new_codes = []
    all_codes = set()

    genshin = get_genshin_codes()
    zzz = get_zzz_codes()

    for code in genshin:
        all_codes.add(code)
        if code not in old_codes:
            new_codes.append(f"🎁 Genshin: `{code}`")

    for code in zzz:
        all_codes.add(code)
        if code not in old_codes:
            new_codes.append(f"🎮 ZZZ: `{code}`")

    if new_codes:
        message = "**📢 New Codes Found:**\n" + "\n".join(new_codes)
        await channel.send(message)
        save_posted_codes(all_codes)
    else:
        print("ℹ️ No new codes to post.")

# === Start Everything ===
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
