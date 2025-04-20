import discord
from discord.ext import commands, tasks
import os
import asyncio
import warnings
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(".env")
TOKEN2 = os.getenv('1BOT_TOKEN_2')
TRACKER_TOKEN = os.getenv('TRACKER_OFFICIAL_TOKEN')

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    application_id=1322305662973116486
    )

bot.start_time = datetime.now()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('------------------------')
    #await bot.tree.sync()
    await bot.change_presence(
        activity=discord.CustomActivity(f"Invite Me! | {len(bot.guilds)} Servers"))
    update_presence.start()
        
last_server_count = 4
@tasks.loop(minutes=5)
async def update_presence():
    global last_server_count
    current_server_count = len(bot.guilds)
    if current_server_count != last_server_count:
        await bot.change_presence(
            activity=discord.CustomActivity(f"Invite Me! | {current_server_count} Servers"))
        last_server_count = current_server_count

warnings.filterwarnings('ignore') 
bot.remove_command('help') 
    
async def load_extensions():
    initial_extensions = []

    for filename in os.listdir('main_code/cogs'):
    #for filename in os.listdir('/home/pi/code/PublicTrackerRelease/main_code/cogs'):
        if filename.endswith('.py'):
            initial_extensions.append("cogs." + filename[:-3])

    print(initial_extensions)
    
    for extension in initial_extensions:
        await bot.load_extension(extension)

if __name__ == '__main__':
    asyncio.run(load_extensions())
    bot.run(TOKEN2)
  #  bot.run(TRACKER_TOKEN)
