import re
from functions import *
import discord
from bot import bot
from discord.ext import commands
from datetime import datetime

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild_id = payload.guild_id
        settings = get_guild_settings(guild_id)
        
        STARBOARD_CHANNEL_ID = settings.skullboard_channel_id if settings.skullboard_channel_id else None
        
        if settings.skullboard_channel_id is None:
            return
        
        if not payload.guild_id:
            return  
        
        if payload.channel_id == STARBOARD_CHANNEL_ID:
            return  
        
        if str(payload.emoji.name) not in STAR_EMOJIS:
            return  
        
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)  
        
        if message.id in skullboarded_messages:
            return 
        
        reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
        if reaction and reaction.count == REACTION_THRESHOLD:
            starboard_channel = self.bot.get_channel(STARBOARD_CHANNEL_ID)
            if not starboard_channel:
                return  
            
            await message.forward(destination=starboard_channel)
            await starboard_channel.send(f"**lmao get clipped 💀** - {message.author.mention}")
            
            skullboarded_messages.append(message.id) 
            save_skullboarded_messages(skullboarded_messages) 
            
            
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        global last_poll_date

        clean_content = re.sub(r'[^A-Za-z0-9\s]', '', message.content)

        matches = re.findall(r'\bGC\w*\b', clean_content, re.IGNORECASE)
        match = re.findall(r'\bTB\w*\b', clean_content, re.IGNORECASE)

        gc_codes = [item.upper() for item in matches]
        tb_codes = [item.upper() for item in match]

        if any(code in gcblacklist for code in gc_codes):
            return 
        if any(code in tbblacklist for code in tb_codes):
            return  

        if matches or match:
            finalmessage = get_cache_basic_info(gc_codes, tb_codes)
            await message.channel.send(finalmessage)
            
        elif message.poll:
            if message.channel.id == 1321981187585081384:
                today = datetime.now().date()

                if last_poll_date != today:
                    last_poll_date = today
                    save_poll_date(str(today))
                    await message.channel.send(f"It's poll time! <@&1354064754204872714>")
            else:
                return
        else:
            return
        await self.bot.process_commands(message)
        
async def setup(bot):
    await bot.add_cog(Listeners(bot))