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

from dotenv import load_dotenv
load_dotenv(".env")
TOKEN = os.getenv('TOKEN')
TRACKER_TOKEN = os.getenv('TRACKER_OFFICIAL_TOKEN')
BOTLISTME_API = os.getenv('BOTLISTME_API')

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix='!',
    intents=intents
    )

bot.start_time = datetime.now()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('------------------------')
    # await bot.tree.sync()
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
        channel = await bot.fetch_channel(1341107185777643573)
        if channel:
            prefix = f"❌ **{title}**\n```py\n"
            suffix = "\n```"
            max_error_len = 2000 - len(prefix) - len(suffix)
            chunks = [error_text[i:i+max_error_len] for i in range(0, len(error_text), max_error_len)]
            # Send the first chunk with the title
            await channel.send(f"{prefix}{chunks[0]}{suffix}")
            # Send any additional chunks as follow-ups
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
    bot.run("uwu")
  #  bot.run(TRACKER_TOKEN)
