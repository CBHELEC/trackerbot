from dotenv import load_dotenv
load_dotenv(verbose=True, override=True)

import discord
import requests
import traceback
import sys
import os
import asyncio
import warnings
import ezcord
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from discord.ext import commands, tasks
from datetime import datetime
from discord import app_commands
from votefunctions import *
from discord.ext.ipc import ClientPayload, Server
from functions import static_var

# NOTE: 8080 = DBL, 7070 = top.gg, 9797 = ping

TOKEN = os.getenv("BOT_TOKEN")
DBL_SECRET = os.getenv("DBL_WEBHOOK")

class Bot(ezcord.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=static_var.BOT_PREFIX, intents=intents)
        self.ipc = Server(self, secret_key=static_var.SECRET_KEY)

    @Server.route()
    async def guild_count(self, _):
        return str(len(self.guilds))

    @Server.route()
    async def bot_guilds(self, _):
        guild_ids = [str(guild.id) for guild in self.guilds]
        return {"data": guild_ids}

    @Server.route()
    async def guild_stats(self, data: ClientPayload):
        guild = self.get_guild(data.guild_id)
        if not guild:
            return {
                "member_count": 69,
                "name": "Unknown"
            }

        return {
            "member_count": guild.member_count,
            "name": guild.name,
        }
    
    @Server.route()
    async def guild_icon_hash(self, data: ClientPayload):
        guild = self.get_guild(data.guild_id)
        if not guild:
            print("oh noes gwuild has nwot been fwound uwu >:e")
            return {"guild_icon_hash": None}

        icon_hash = guild.icon.key if guild.icon else None 
        return {"guild_icon_hash": icon_hash}

    @Server.route()
    async def check_perms(self, data: ClientPayload):
        guild = self.get_guild(data.guild_id)
        if not guild:
            return {"perms": False}

        try:
            member = await guild.fetch_member(int(data.user_id))
        except (discord.NotFound, discord.HTTPException):
            return {"perms": False}

        if member.id == guild.owner_id or member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return {"perms": True}

        return {"perms": False}
    
    @Server.route()
    async def guild_channels(self, data: ClientPayload):
        guild = self.get_guild(data.guild_id)
        if not guild:
            return {"channels": []}

        return {
            "channels": [
                {
                    "id": ch.id,
                    "name": ch.name
                }
                for ch in guild.text_channels
                if not ch.category and ch.name and ch.name.strip()
            ]
        }

    @Server.route()
    async def guild_categories(self, data: ClientPayload):
        guild = self.get_guild(data.guild_id)
        if not guild:
            return {"categories": []}
        categories = []
        for category in guild.categories:
            channels = [{"id": ch.id, "name": ch.name} for ch in category.channels]
            categories.append({"name": category.name, "channels": channels})
        return {"categories": categories}
    
    @Server.route()
    async def guild_roles(self, data: ClientPayload):
        guild = self.get_guild(data.guild_id)
        if not guild:
            return {"roles": []}
        roles = [{"id": str(role.id), "name": role.name} for role in guild.roles if not role.is_default()]
        return {"roles": roles}

    async def on_ipc_error(self, endpoint: str, exc: Exception) -> None:
        raise exc

bot = Bot()

bot.start_time = datetime.now()

@bot.event
async def on_ready():
    print('------------------------')
    print(f"Start Time: {datetime.now()}")
    print(f'Logged in as {bot.user}')
    print('------------------------')
    # await bot.tree.sync()
    await bot.ipc.start()
    print(f'IPC Server Started')
    await bot.change_presence(
        activity=discord.CustomActivity(f"Merry Crimus! | {len(bot.guilds)} Servers"))
    update_presence.start()
    vote_reminders.start()
    vote_streakreset.start()

topgg = FastAPI()
topgg.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@topgg.post("/topgg")
async def topgg_webhook(request: Request) -> None:
    data = await request.json()
    user_id = int(data.get("user"))
    if datetime.today().weekday() >= 5:
        await notify_vote(user_id, "topgg", bot, weekend=True)
    else:
        await notify_vote(user_id, "topgg", bot)

dbl = FastAPI()
dbl.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@dbl.post("/dbl")
async def dbl_webhook(request: Request):
    data = await request.json()
    user_id = int(data.get("id"))
    if datetime.today().weekday() >= 5:
        await notify_vote(user_id, "dbl", bot, weekend=True)
    else:
       await notify_vote(user_id, "dbl", bot)
    return {"received_user_id": user_id}

ping_app = FastAPI()
ping_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@ping_app.get("/ping")
async def ping():
    uptime_seconds = int((datetime.now() - bot.start_time).total_seconds())
    latency_ms = int(bot.latency * 1000)
    return {
        "status": "online",
        "uptime_seconds": uptime_seconds,
        "latency_ms": latency_ms,
        "server_count": len(bot.guilds)
    }

@tasks.loop(minutes=2)
async def vote_reminders():
    await send_vote_reminders(bot)

@tasks.loop(minutes=2)
async def vote_streakreset():
    await streak_reset(bot)

last_server_count = 4
@tasks.loop(minutes=5)
async def update_presence():
    global last_server_count
    current_server_count = len(bot.guilds)
    if current_server_count != last_server_count:
        await bot.change_presence(
            activity=discord.CustomActivity(f"Merry Crimus! | {current_server_count} Servers"))

        if os.getenv("TOPGG_WEBHOOK_FLAG") == "0":
            url = f"https://top.gg/api/bots/1322305662973116486/stats"
            headers = {
                "Authorization": os.getenv("TOPGG_TOKEN"),
                "Content-Type": "application/json"
            }
            payload = {
                "server_count": len(bot.guilds),
            }
            requests.post(url, headers=headers, json=payload)

        last_server_count = current_server_count

async def log_unhandled_error(bot, title: str, error_text: str):
    try:
        channel = await bot.fetch_channel(static_var.ERROR_LOG_ID)
        if channel:
            prefix = f"❌ **{title}**\n```py\n"
            suffix = "\n```"
            max_error_len = 2000 - len(prefix) - len(suffix)
            chunks = [error_text[i:i+max_error_len] for i in range(0, len(error_text), max_error_len)]
            await channel.send(f"{prefix}{chunks[0]}{suffix}")
            for chunk in chunks[1:]:
                await channel.send(f"```py\n{chunk}\n```")
    except Exception as e:
        print(f"[Error Logger Failed] {e}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    error = getattr(error, 'original', error)  

    if isinstance(error, app_commands.CheckFailure):
        if interaction.command.name == "unverified":
            return
        if str(error) == "COMMANDS_DISABLED_BY_ADMIN":
            return
        if str(error) == "M_COMMANDS_DISABLED_BY_ADMIN":
            return
        if str(error) == "USER_SUSPENDED":
            return
        if str(error) == "TB_BLACKLIST":
            return
        try:
            await interaction.response.send_message(embed=static_var.YOUCANTDOTHIS, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(embed=static_var.YOUCANTDOTHIS, ephemeral=True)
        return  

    import traceback
    tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    await log_unhandled_error(bot, f"Slash command error (`{interaction.command}`)", tb)

@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        return  
    if isinstance(error, commands.CommandNotFound):
        if ctx.invoked_with == "randomsteven":
            return
        else:
            error = getattr(error, 'original', error)
            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            await log_unhandled_error(bot, f"Prefix/Hybrid command error (`{ctx.command}`)", tb)

@bot.event
async def on_error(event, *args, **kwargs):
    tb = "".join(traceback.format_exception(*sys.exc_info()))
    await log_unhandled_error(bot, f"Listener error in `{event}`", tb)

warnings.filterwarnings('ignore') 
bot.remove_command('help') 

async def load_extensions():
    initial_extensions = []

    for filename in os.listdir(static_var.CODE_DIR / "cogs"):
        if filename.endswith('.py'):
            initial_extensions.append("cogs." + filename[:-3])

    print(initial_extensions)
    
    for extension in initial_extensions:
        await bot.load_extension(extension)

async def main():
    config = uvicorn.Config(dbl, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)

    config2 = uvicorn.Config(ping_app, host="0.0.0.0", port=9090, log_level="info")
    server2 = uvicorn.Server(config2)

    config3 = uvicorn.Config(topgg, host="0.0.0.0", port=9797, log_level="info")
    server3 = uvicorn.Server(config3)

    dbl_task = asyncio.create_task(server.serve())
    ping_task = asyncio.create_task(server2.serve())
    topgg_task = asyncio.create_task(server3.serve())

    await load_extensions()
    print("Extensions Loaded")

    await asyncio.gather(
        topgg_task,
        ping_task,
        dbl_task,
        bot.start(TOKEN)
    )

if __name__ == "__main__":
    asyncio.run(main())