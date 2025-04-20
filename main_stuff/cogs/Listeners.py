import re
from functions import *
import discord
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
            if message.guild.id != 1321978962078994495:
                return
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
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title="New Server!",
                      description=f"Name: {guild.name}\nID: {guild.id}\nOwner: {guild.owner.name} ({guild.owner.id})\nMember Count: {guild.member_count} \nBoosts: {guild.premium_subscription_count}",
                      colour=0x6ad2a2)

        embed.set_thumbnail(url=f"{guild.icon.url if guild.icon else None}")
        await self.bot.get_channel(1360214049278787816).send(embed=embed)
        
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                try:
                    aembed = discord.Embed(title="Heya, Thanks for adding me!",
                      description="Configuration is easy, simply follow these commands and you're good to go!\n</setperm:1362738130918314149> - Add roles which can use Message commands\n</removeperm:1362738130918314150> - Remove roles from being able to use Message commands\n</setskullboard:1362738130918314151> - Set whether skullboard function is enabled, and if so what channel is used\n</settings:1362738130918314152> - Display guild configuration\n-----------------------------------------------------------------------------------------------\n</help:1323052604623683779> - View info on all commands!\n-----------------------------------------------------------------------------------------------\nIf you need more help, run </invite support:1362738130490490908> and join that server to get help, or simply message `not.cbh` (<@820297275448098817>)\n\nHope you enjoy having me in your server, I'm glad to be here! Any suggestions please also do the same as above, we listen to all suggestions.",
                      colour=0xad7e66)
                    await channel.send(embed=aembed)
                    break  
                except discord.Forbidden:
                    continue  
        
async def setup(bot):
    await bot.add_cog(Listeners(bot))