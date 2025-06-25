from pathlib import Path
from dotenv import load_dotenv
load_dotenv(verbose=True, override=True)

import discord
from discord.ext import commands, tasks
import os
import asyncio
import warnings
from datetime import datetime
import traceback
import sys
from discord import app_commands
from functions import *
import ezcord
from discord.ext.ipc import ClientPayload, Server

TOKEN = os.getenv('TOKEN')
TRACKER_TOKEN = os.getenv('TRACKER_OFFICIAL_TOKEN')
BOTLISTME_API = os.getenv('BOTLISTME_API')

class Bot(ezcord.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.members = True

        super().__init__(intents=intents)
        self.ipc = Server(self, secret_key="keks")

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

        icon_hash = guild.icon.key if guild.icon else None  # Extract only the raw hash
        print(f"owo yay gwuild icon has been fwound: {icon_hash}")
        return {"guild_icon_hash": icon_hash}

    @Server.route()
    async def check_perms(self, data: ClientPayload):
        guild = self.get_guild(data.guild_id)
        if not guild:
            return {"perms": False}

        member = guild.get_member(int(data.user_id))
        if not member or not member.guild_permissions.administrator:
            return {"perms": False}

        return {"perms": True}
    
    @Server.route()
    async def guild_channels(self, data: ClientPayload):
        guild = self.get_guild(data.guild_id)
        if not guild:
            return {"channels": []}
        return {"channels": [channel.name for channel in guild.text_channels]}

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
    print(f'Logged in as {bot.user}')
    print('------------------------')
    # await bot.tree.sync()]
    await bot.ipc.start()
    print(f'IPC Server Started')
    await bot.change_presence(
        activity=discord.CustomActivity(f"Invite Me! | {len(bot.guilds)} Servers"))
    update_presence.start()

#    async with aiohttp.ClientSession() as session:
#        await session.post(
#        "https://api.botlist.me/api/v1/bots/1322305662973116486/stats",
#        headers={"Authorization": "owo", "Content-Type": "application/json"},
#        json={"server_count": 13}
#        )

last_server_count = 4
@tasks.loop(minutes=5)
async def update_presence():
    global last_server_count
    current_server_count = len(bot.guilds)
    if current_server_count != last_server_count:
        await bot.change_presence(
            activity=discord.CustomActivity(f"Invite Me! | {current_server_count} Servers"))
        last_server_count = current_server_count

async def log_unhandled_error(bot, title: str, error_text: str):
    try:
        channel = await bot.fetch_channel(ERROR_LOG_ID)
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
        try:
            await interaction.response.send_message(embed=YOUCANTDOTHIS, ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(embed=YOUCANTDOTHIS, ephemeral=True)
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

    script_dir = os.path.dirname(os.path.abspath(__file__))
    for filename in os.listdir(f"{script_dir}/cogs"):
        if filename.endswith('.py'):
            initial_extensions.append("cogs." + filename[:-3])

    print(initial_extensions)
    
    for extension in initial_extensions:
        await bot.load_extension(extension)

if __name__ == '__main__':
    asyncio.run(load_extensions())
    bot.run(TOKEN)
