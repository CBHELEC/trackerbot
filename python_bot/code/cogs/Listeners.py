import asyncio
import re
import discord
import random
import sqlite3
from functions import *
from discord.ext import commands
from datetime import datetime
# from economy import *

reminded_users = load_reminded_users()
async def send_vote_reward_topgg(self, user_id, new_streak, voted_at):
    try:
        discord_user = await self.bot.fetch_user(int(user_id))
        if discord_user:
            if user_id in reminded_users:
                del reminded_users[user_id]
                save_reminded_users(reminded_users)
           # amount = random.randint(10, 35)
            amount = random.randint(2, 5)
            embed = discord.Embed(
                title="Thank you for voting on top.gg! 🎉",
                #description=f"You voting helps a lot, so take {amount} G$ as your reward!\nThanks! <3",
                description=f"You voting helps a lot, so take {amount} Vote Crates as your reward!\nThanks! <3",
                colour=0xad7e66,
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Vote Streak: {new_streak}")

  #          async with Session() as session:
   #             userinfo = await get_db_settings(session, user_id)
    #            if userinfo is None:
     #               await add_user_to_db(session, user_id)
      #              userinfo1 = await get_db_settings(session, user_id)
       #             balance = userinfo1.balance
        #        else:
         #           balance = userinfo.balance
          #      new_balance = balance + amount
           #     await update_balance(session, user_id, new_balance)
            self.c.execute('SELECT moneh FROM moneh WHERE user_id = ?', (user_id,))
            row1 = self.c.fetchone()
            if row1:
                moneh = row1[0]
            else:
                moneh = 0
            new_moneh = moneh + amount
            self.c.execute(
                "INSERT INTO moneh (user_id, moneh) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET moneh = excluded.moneh",
                (str(user_id), new_moneh)
            )
            self.conn2.commit()

            await discord_user.send(embed=embed)
            
    except Exception as e:
        print(e)
        return

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn2 = sqlite3.connect(f'{DATA_DIR}/votes.db')
        self.c = self.conn2.cursor()

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
    async def on_message_edit(self, before, after):
        if after.author.bot:
            return
        if not after.guild:
            return

        content = after.content
        setting = get_guild_settings(after.guild.id)
        detection_status = bool(setting.detection_status) if hasattr(setting, 'detection_status') else True
        link_embed_status = bool(setting.link_embed_status) if hasattr(setting, 'link_embed_status') else True
        gc_matches = re.findall(r'\bGC[0-9A-Z]{1,5}\b', content, re.IGNORECASE)
        gc_matches += re.findall(r'geocache/GC[0-9A-Z]{1,5}', content, re.IGNORECASE)
        tb_matches = re.findall(r'\bTB[0-9A-Z]{1,5}\b', content, re.IGNORECASE)
        tb_matches += re.findall(r'/track/TB[0-9A-Z]{1,5}', content, re.IGNORECASE)
        gcblacklist = {"GC", "GCHQ", "GCFAQ"}
        tbblacklist = {"TB", "TBF", "TBH", "TBS", "TBDISCOVER", "TBDROP", "TBGRAB", "TBMISSING", "TBRETRIEVE", "TBVISIT"}
        gc_codes = list({code[-7:].upper() for code in gc_matches if code[-7:].upper() not in gcblacklist})
        tb_codes = list({code[-7:].upper() for code in tb_matches if code[-7:].upper() not in tbblacklist})
        before_gc = set(code[-7:].upper() for code in re.findall(r'\bGC[0-9A-Z]{1,5}\b|geocache/GC[0-9A-Z]{1,5}', before.content, re.IGNORECASE))
        before_tb = set(code[-7:].upper() for code in re.findall(r'\bTB[0-9A-Z]{1,5}\b|/track/TB[0-9A-Z]{1,5}', before.content, re.IGNORECASE))
        after_gc = set(gc_codes)
        after_tb = set(tb_codes)

        if re.search(r'https?://(www\.)?(geocaching\.com|coord\.info)', after.content, re.IGNORECASE):
            if after.author.bot:
                return
            if not link_embed_status:
                return
            if not after.embeds: 
                return
            await asyncio.sleep(2)
            await after.reply("Heya, I cleared the embed from your message since it doesn't show any extra info! <:happy_tracker:1329914691656614042>", delete_after=5)
            await after.edit(suppress=True)

     #   if any(code in gcblacklist for code in gc_codes):
      #      return 
       # if any(code in tbblacklist for code in tb_codes):
        #    return  
        if before_gc == after_gc and before_tb == after_tb:
            return 

        if before.embeds and not after.embeds:
            return

        elif gc_codes or tb_codes:
            if not detection_status:
                return
            
            if not after.embeds:
                if not before.embeds and not after.embeds:
                    finalmessage = get_cache_basic_info(gc_codes, tb_codes)
                    await after.reply(finalmessage)
                return
            finalmessage = get_cache_basic_info(gc_codes, tb_codes)
            await after.reply(finalmessage)

        elif "good bot" in after.content.lower():
            await after.reply("<:happy_tracker:1329914691656614042>")

        else:
            return

        await self.bot.process_commands(after)

    @commands.Cog.listener()
    async def on_message(self, message): 
        global last_poll_date

        content = message.content
        gc_matches = re.findall(r'\bGC[0-9A-Z]{1,5}\b(?!:)', content, re.IGNORECASE)
        gc_matches_l = re.findall(r'geocache/GC[0-9A-Z]{1,5}(?!:)', content, re.IGNORECASE)
        tb_matches = re.findall(r'\bTB[0-9A-Z]{1,5}\b(?!:)', content, re.IGNORECASE)
        tb_matches_l = re.findall(r'/track/TB[0-9A-Z]{1,5}(?!:)', content, re.IGNORECASE)
        print(f"GCM: {gc_matches}, GCML: {gc_matches_l}, TBM: {tb_matches}, TBML: {tb_matches_l}, MID: {message.id}, AUTHOR: {message.author.id}, CHANNEL: {message.channel.id}, GUILD: {message.guild.id if message.guild else 'DM'}")
        gcblacklist = ["GC", "GCHQ", "GCFAQ", "GCHQBLOCKPARTY", "GCHQCE"]
        tbblacklist = ["TB", "TBF", "TBH", "TBS", "TBDISCOVER", "TBDROP", "TBGRAB", "TBMISSING", "TBRETRIEVE", "TBVISIT"]        
        gc_codes = list(set(code[-7:].upper() for code in gc_matches if code.upper() not in gcblacklist))
        tb_codes = list(set(code[-7:].upper() for code in tb_matches if code.upper() not in tbblacklist))
        gc_codes_l = list(set(code[-7:].upper() for code in gc_matches_l if code.upper() not in gcblacklist))
        tb_codes_l = list(set(code[-7:].upper() for code in tb_matches_l if code.upper() not in tbblacklist))
        print(f"GCC: {gc_codes}, GCCL: {gc_codes_l}, TBC: {tb_codes}, TBCL: {tb_codes_l}, MID: {message.id}, AUTHOR: {message.author.id}, CHANNEL: {message.channel.id}, GUILD: {message.guild.id if message.guild else 'DM'}")

  #      if any(code in gcblacklist for code in gc_codes):
  #          return 
   #     if any(code in tbblacklist for code in tb_codes):
    #        return  
#
 #       if any(code in gcblacklist for code in gc_codes_l):
  #          return 
   #     if any(code in tbblacklist for code in tb_codes_l):
    #        return 

        if not message.guild:
            return
        
        setting = get_guild_settings(message.guild.id)
        if setting:
            detection_status = bool(setting.detection_status) if hasattr(setting, 'detection_status') else True
            link_embed_status = bool(setting.link_embed_status) if hasattr(setting, 'link_embed_status') else True
        else:
            link_embed_status = True
            detection_status = True

        if gc_codes or tb_codes or gc_codes_l or tb_codes_l:
            if message.author.bot:
                return
            if not detection_status:
                return
            if gc_codes_l or tb_codes_l:
                await message.reply("Heya, I cleared the embed from your message since it doesn't show any extra info! <:happy_tracker:1329914691656614042>", delete_after=5)
                await message.edit(suppress=True)

            finalmessage = get_cache_basic_info(gc_codes, tb_codes)
            await message.reply(finalmessage)
            
        elif message.poll:
            if message.guild.id != 1368978029056888943:
                return
            if message.channel.id == 1368978994518556844:
                today = datetime.now().date()

                if last_poll_date != today:
                    last_poll_date = today
                    save_poll_date(str(today))
                    await message.channel.send(f"It's poll time! <@&1369003389576417300>")
            else:
                return

        elif message.webhook_id:
            if message.channel.id == 1365079297919811725:
                if message.embeds:
                    embed = message.embeds[0]
                    voter_match = re.search(r"<@(\d+)> Voted for <@(\d+)>!", embed.description or "")
                    if voter_match:
                        voter = voter_match.group(1)
                        bot_voted = voter_match.group(2)
                        voter1 = self.bot.get_user(int(voter))
                    else:
                        return 

                    fields = {field.name: field.value for field in embed.fields}
                    vote_again_time = fields.get("Can vote again at:")
                    total_votes = fields.get("Total Votes:")
                    vote_streak = fields.get("Current Vote Streak:")
                    
                    self.c.execute(
                        "INSERT INTO topgg_votes (user_id, reminded) VALUES (?, ?) "
                        "ON CONFLICT(user_id) DO UPDATE SET reminded = excluded.reminded",
                        (str(voter1.id), 0)
                    )
                    self.conn2.commit()
                    
                    await send_vote_reward_topgg(self, voter, vote_streak, datetime.now())
                else:
                    return
            else:
                return

        elif re.search(r'https?://(www\.)?(geocaching\.com|coord\.info)', message.content, re.IGNORECASE):
            if message.author.bot:
                return
            if not link_embed_status:
                return
            await asyncio.sleep(2)
            await message.reply("Heya, I cleared the embed from your message since it doesn't show any extra info! <:happy_tracker:1329914691656614042>", delete_after=5)
            await message.edit(suppress=True)

        elif "good bot" in message.content.lower():
            await message.reply("<:happy_tracker:1329914691656614042>")

        else:
            return
    
        await self.bot.process_commands(message)
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title="New Server!",
                      description=f"Name: {guild.name}\nID: {guild.id}\nOwner: {guild.owner.name} ({guild.owner.id})\nMember Count: {guild.member_count} \nBoosts: {guild.premium_subscription_count}",
                      colour=0x6ad2a2)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
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
