import discord
from discord.ext import commands
import os
import asyncio
import warnings

from dotenv import load_dotenv
load_dotenv(".env")
TOKEN2 = os.getenv('1BOT_TOKEN_2')

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('------------------------')
    await bot.tree.sync()
    await bot.change_presence(
        activity=discord.CustomActivity(f"Finding Caches and Friends"))

warnings.filterwarnings('ignore') 
bot.remove_command('help') 
    
async def load_extensions():
    initial_extensions = []

    for filename in os.listdir('the code i need for the bot/cogs'):
        if filename.endswith('.py'):
            initial_extensions.append("cogs." + filename[:-3])

    print(initial_extensions)
    
    for extension in initial_extensions:
        await bot.load_extension(extension)

if __name__ == '__main__':
    asyncio.run(load_extensions())
    bot.run(TOKEN2)