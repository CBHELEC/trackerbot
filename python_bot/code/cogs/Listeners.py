import asyncio
import re
import discord
import sqlite3
from functions import *
from discord.ext import commands
from datetime import datetime

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn2 = sqlite3.connect(DATA_DIR / 'votes.db')
        self.c = self.conn2.cursor()
        self.recently_processed_embeds = set()  # Track messages that recently had embeds removed

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
    async def on_message(self, message: discord.Message):
        global last_poll_date

        if message.author.id == self.bot.user.id:
            return

        if not message.guild:
            return

        setting = get_guild_settings(message.guild.id)
        detection_status = bool(setting.detection_status) if hasattr(setting, 'detection_status') else True
        link_embed_status = bool(setting.link_embed_status) if hasattr(setting, 'link_embed_status') else True

        if detection_status:
            if message.author.bot:
                return
            succ, gc_codes, tb_codes = find_gc_tb_codes(message.content)
            if succ:
                finalmessage, deadcode = get_cache_basic_info(message.guild.id, gc_codes, tb_codes)
                if deadcode:
                    return
                await message.reply(finalmessage)

        if message.poll:
            if message.guild.id != 1368978029056888943:
                return
            if message.channel.id == 1368978994518556844:
                today = datetime.now().date()

                if last_poll_date != today:
                    last_poll_date = today
                    save_poll_date(today)
                    await message.channel.send(f"It's poll time! <@&1369003389576417300>")
            else:
                return

        if link_embed_status and len(message.embeds) and re.search(GC_LINK_SEARCH, message.content, re.IGNORECASE):
            if message.author.bot:
                return
            # Check if we've already processed this message recently
            if message.id in self.recently_processed_embeds:
                return
            # Check if embeds are already suppressed
            if message.flags.suppress_embeds:
                return
            self.recently_processed_embeds.add(message.id)
            # Remove from set after 10 seconds to prevent memory buildup
            asyncio.create_task(self._remove_from_processed(message.id, delay=10))
            await message.reply("Heya, I cleared the embed from your message since it doesn't show any extra info!", delete_after=5)
            await message.edit(suppress=True)

        if "good bot" in message.content.lower():
            await message.reply("thank yous OwO")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return
        if not after.guild:
            return

        setting = get_guild_settings(after.guild.id)
        detection_status = bool(setting.detection_status) if hasattr(setting, 'detection_status') else True
        link_embed_status = bool(setting.link_embed_status) if hasattr(setting, 'link_embed_status') else True
        before_succ, before_gc, before_tb = find_gc_tb_codes(before.content)
        after_succ, after_gc, after_tb = find_gc_tb_codes(after.content)

        if link_embed_status and len(after.embeds) and re.search(GC_LINK_SEARCH,after.content,re.IGNORECASE):
            if after.author.bot:
                return
            # Check if we've already processed this message recently
            if after.id in self.recently_processed_embeds:
                return
            # Check if embeds are already suppressed
            if after.flags.suppress_embeds:
                return
            self.recently_processed_embeds.add(after.id)
            # Remove from set after 10 seconds to prevent memory buildup
            asyncio.create_task(self._remove_from_processed(after.id, delay=10))
            await asyncio.sleep(2)
            await after.reply(
                "Heya, I cleared the embed from your message since it doesn't show any extra info!",
                delete_after=5,
            )
            await after.edit(suppress=True)

        if before_gc == after_gc and before_tb == after_tb:
            return

        if before.embeds and not after.embeds:
            return

        elif after_succ:
            if not detection_status:
                return

            if not after.embeds:
                if not before.embeds and not after.embeds:
                    finalmessage, deadcode = get_cache_basic_info(after.guild.id, after_gc, after_tb)
                    if deadcode: 
                        return
                    await after.reply(finalmessage)
                return
            finalmessage, deadcode = get_cache_basic_info(after.guild.id, after_gc, after_tb)
            if deadcode:
                return
            await after.reply(finalmessage)

        elif "good bot" in after.content.lower():
            await after.reply("thank yous OwO")

        else:
            return

    async def _remove_from_processed(self, message_id: int, delay: float):
        """Remove a message ID from the recently processed set after a delay."""
        await asyncio.sleep(delay)
        self.recently_processed_embeds.discard(message_id)

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
                    aembed = discord.Embed(title="Hey! Thanks for adding me...",
                                        description="If you want to configure me, I have a dashboard!\n" \
                                        "LINK: [**CLICK ME**](<https://dashboard.trackerbot.xyz/>)\n" \
                                        "If you want help, I have a command for that!\n" \
                                        "COMMAND: </help:1370815537059205173> (<--- CLICK)\n" \
                                        "If none of that has helped, join my support server!\n" \
                                        "INVITE COMMAND: </invite support:1370815537151606928> (<--- CLICK)\n\n" \
                                        "Hope you enjoy having me in your server, I'm glad to be here! \n" \
                                        "Any suggestions please use:\n" \
                                        "COMMAND: </misc suggest_report:1419276756874952828> (<--- CLICK)\n" \
                                        "to send it straight to the Dev!\n" \
                                        "All suggestions are listened to, and likely added.",
                                        colour=0xad7e66)
                    await channel.send(embed=aembed)
                    break  
                except discord.Forbidden:
                    continue  

async def setup(bot):
    await bot.add_cog(Listeners(bot))
