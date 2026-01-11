import asyncio
import re
import discord
import sqlite3
from functions import static_var, skullboard, codedetection, coorddetect, poll
from discord.ext import commands
from datetime import datetime
from database import *

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn2 = sqlite3.connect(static_var.DATA_DIR / 'votes.db')
        self.c = self.conn2.cursor()
        self.recently_processed_embeds = set() 

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

        if str(payload.emoji.name) not in SKULL_EMOJI:
            return  

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)  

        if message.id in skullboard.skullboarded_messages:
            return 

        reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
        if reaction and reaction.count == skullboard.REACTION_THRESHOLD:
            starboard_channel = self.bot.get_channel(STARBOARD_CHANNEL_ID)
            if not starboard_channel:
                return  

            await message.forward(destination=starboard_channel)
            await starboard_channel.send(f"**lmao get clipped 💀** - {message.author.mention}")

            skullboard.skullboarded_messages.append(message.id) 
            skullboard.save_skullboarded_messages(skullboard.skullboarded_messages) 

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
        cd_split_status = bool(setting.cd_split_status) if hasattr(setting, 'cd_split_status') else True

        if detection_status:
            if message.author.bot:
                return
            
        # GC / TB
        succ, gc_codes, tb_codes = codedetection.find_gc_tb_codes(message.content)
        if succ:
            finalmessage, deadcode = codedetection.get_cache_basic_info(message.guild.id, gc_codes, tb_codes)
            if deadcode:
                return
            await codedetection.split_message(message, finalmessage, cd_split_status)

        # PR
        pr_codes = await codedetection.find_pr_codes(message.content)
        if pr_codes:
            finalmessage = await codedetection.get_pr_code_info(pr_codes, self.bot, message.guild.id)
            if finalmessage:
                await codedetection.split_message(message, finalmessage, cd_split_status)

        # GL / TL
        gl_codes, tl_codes = await codedetection.find_gl_tl_codes(message.content)
        if gl_codes or tl_codes:
            finalmessage = await codedetection.get_gl_tl_code_info(gl_codes, tl_codes, message.guild.id)
            if finalmessage:
                await codedetection.split_message(message, finalmessage, cd_split_status)

        # GT
        gt_codes = await codedetection.find_gt_codes(message.content)
        if gt_codes:
            finalmessage = await codedetection.get_gt_code_info(gt_codes, message.guild.id)
            if finalmessage:
                await codedetection.split_message(message, finalmessage, cd_split_status)
            
        # Coordinates
        coords = coorddetect.find_coordinates(message.content)
        if coords:
            await message.reply("\n".join(coords))

        if message.poll:
            if message.guild.id != 1368978029056888943:
                return
            if message.channel.id == 1368978994518556844:
                today = datetime.now().date()

                if poll.last_poll_date != today:
                    poll.last_poll_date = today
                    poll.save_poll_date(today)
                    await message.channel.send(f"It's poll time! <@&1369003389576417300>")
            else:
                return

        if link_embed_status and len(message.embeds) and re.search(static_var.GC_LINK_SEARCH, message.content, re.IGNORECASE):
            if message.author.bot:
                return
            if message.id in self.recently_processed_embeds:
                return
            if message.flags.suppress_embeds:
                return
            self.recently_processed_embeds.add(message.id)
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
        detection_status = bool(setting.detection_status) if hasattr(setting, "detection_status") else True
        link_embed_status = bool(setting.link_embed_status) if hasattr(setting, "link_embed_status") else True
        cd_split_status = bool(setting.cd_split_status) if hasattr(setting, "cd_split_status") else True

        if link_embed_status and len(after.embeds) and re.search(static_var.GC_LINK_SEARCH, after.content, re.IGNORECASE):
            if after.id in self.recently_processed_embeds:
                return
            if after.flags.suppress_embeds:
                return
            self.recently_processed_embeds.add(after.id)
            asyncio.create_task(self._remove_from_processed(after.id, delay=10))
            await asyncio.sleep(2)
            await after.reply(
                "Heya, I cleared the embed from your message since it doesn't show any extra info!",
                delete_after=5,
            )
            await after.edit(suppress=True)

        if before.content == after.content:
            return

        if detection_status:
            # GC / TB
            before_succ, before_gc, before_tb = codedetection.find_gc_tb_codes(before.content)
            after_succ, after_gc, after_tb = codedetection.find_gc_tb_codes(after.content)
            if after_succ and (before_gc != after_gc or before_tb != after_tb):
                finalmessage, deadcode = codedetection.get_cache_basic_info(
                    after.guild.id,
                    list(after_gc),
                    list(after_tb)
                )
                if not deadcode:
                    await codedetection.split_message(after, finalmessage, cd_split_status)

            # PR
            before_pr = await codedetection.find_pr_codes(before.content)
            after_pr = await codedetection.find_pr_codes(after.content)
            if after_pr and before_pr != after_pr:
                finalmessage = await codedetection.get_pr_code_info(after_pr, self.bot, after.guild.id)
                if finalmessage:
                    await codedetection.split_message(after, finalmessage, cd_split_status)

            # GL / TL
            before_gl, before_tl = await codedetection.find_gl_tl_codes(before.content)
            after_gl, after_tl = await codedetection.find_gl_tl_codes(after.content)
            if (after_gl or after_tl) and (before_gl != after_gl or before_tl != after_tl):
                finalmessage = await codedetection.get_gl_tl_code_info(after_gl, after_tl, after.guild.id)
                if finalmessage:
                    await codedetection.split_message(after, finalmessage, cd_split_status)

            # GT
            before_gt = await codedetection.find_gt_codes(before.content)
            after_gt = await codedetection.find_gt_codes(after.content)
            if after_gt and before_gt != after_gt:
                finalmessage = await codedetection.get_gt_code_info(after_gt, after.guild.id)
                if finalmessage:
                    await codedetection.split_message(after, finalmessage, cd_split_status)

        # Coordinates
        before_coords = coorddetect.find_coordinates(before.content)
        after_coords = coorddetect.find_coordinates(after.content)
        if after_coords and before_coords != after_coords:
            await codedetection.split_message(after, "\n".join(after_coords))

        if "good bot" in after.content.lower() and "good bot" not in before.content.lower():
            await after.reply("thank yous OwO")

    async def _remove_from_processed(self, message_id: int, delay: float):
        """Remove a message ID from the recently processed set after a delay."""
        await asyncio.sleep(delay)
        self.recently_processed_embeds.discard(message_id)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        owner_name = f"<@{guild.owner_id}>" if guild.owner_id else "Unknown"
        embed = discord.Embed(title="New Server!",
                      description=f"Name: {guild.name}\nID: {guild.id}\nOwner: {owner_name} ({guild.owner_id})\nMember Count: {guild.member_count} \nBoosts: {guild.premium_subscription_count}",
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
