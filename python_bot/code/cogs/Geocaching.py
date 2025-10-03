import rot_cipher
import os
import discord
import re
from functions import *
from discord import app_commands
from discord.ext import commands
from num2words import num2words
from datetime import datetime
from urllib.parse import quote

class Geocaching(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
# FTF
    @app_commands.command()
    async def ftf(self, interaction: discord.Interaction):
        """Shows how to get your FTFs recognised on PGC."""
        embed = discord.Embed(title="How to get your FTFs recognised on /statbar (Project-GC)",
                      description="There are multiple ways for Project-GC to detect your FTFs. Either you tag your logs with one of these tags: `{*FTF*}`, `{FTF}`, or `[FTF]`. Alternatively you can add an FTF bookmark list under Settings (<https://project-gc.com/User/Settings/>) that will be checked once per day. Please understand that FTF isn't anything offical and not everyone tags their FTFs. Therefore this list won't be 100% accurate.",
                      colour=0xad7e66)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
# STATBAR
    @app_commands.user_install()
    @app_commands.command()
    @app_commands.choices(labcaches=[
        app_commands.Choice(name="Exclude", value="1"),
        app_commands.Choice(name="Include (default)", value="2")
    ])
    @app_commands.describe(
    gc_user="The Geocaching username the statbar will be made for",
    dc_user="The Discord user display name the statbar will be made for",
    labcaches="Whether labcaches are included in your total finds (Default = Included)"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def statbar(self, interaction: discord.Interaction, gc_user: str = None, dc_user: discord.Member = None, labcaches: app_commands.Choice[str] = None):
        """Sends a statbar image."""
        user = gc_user if gc_user else dc_user.display_name if dc_user else interaction.user.display_name
        user = quote(user)
        now = datetime.now()
        intYear = now.year
        intMonth = now.month
        intDay = now.day
        quotetimeusa = f"{intYear}/{intMonth:02d}/{intDay:02d}"
        if labcaches == None or labcaches.value == "2":
            await interaction.response.send_message(f"https://cdn2.project-gc.com/statbar.php?quote=discord.gg/pmuuVNptg3+-+{quotetimeusa}&includeLabcaches&user={user}")
        else:
            await interaction.response.send_message(f"https://cdn2.project-gc.com/statbar.php?quote=discord.gg/pmuuVNptg3+-+{quotetimeusa}&user={user}")
        
# BADGEBAR
    @app_commands.user_install()
    @app_commands.command()
    @app_commands.describe(
    gc_user="The Geocaching username the statbar will be made for",
    dc_user="The Discord user display name the statbar will be made for",
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def badgebar(self, interaction: discord.Interaction, gc_user: str = None, dc_user: discord.Member = None):
        """Sends a badgebar image."""
        user = gc_user if gc_user else dc_user.display_name if dc_user else interaction.user.display_name
        user = quote(user)
        await interaction.response.send_message(f"https://cdn2.project-gc.com/BadgeBar/{user}.png")
        
# GC_INFO
    @app_commands.user_install()
    @app_commands.command()
    @app_commands.describe(codes="The code(s) to get info for")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def gc_info(self, interaction: discord.Interaction, codes: str):
        """Sends info about GC/TB code(s)."""
        guildiddm = interaction.guild.id if interaction.guild else 0
        succ, gc_codes, tb_codes = find_gc_tb_codes(codes)
        guildsettings = get_guild_settings(guildiddm)

        if succ:
            guildid = interaction.guild.id if interaction.guild else 0
            finalmessage, deadcode = get_cache_basic_info(guildid, gc_codes, tb_codes)
            if not guildsettings.detection_status:
                # detection_status is disabled (not normal)
                if not deadcode:
                    # detection_status is disabled, deadcode is disabled
                    if not interaction.guild:
                        # detection_status is disabled, deadcode is disabled, no guild
                        await interaction.response.send_message("<:DNF:1368989100220092516> **That Geocache doesn't exist!**")
                    else:
                        # detection_status is disabled, deadcode is enabled, yes guild
                        await interaction.response.send_message("<:DNF:1368989100220092516> **That Geocache doesn't exist!** | This message has been disabled by the guild Administrator.", ephemeral=True)
                else:
                    # detection_status is disabled, deadcode is disabled, any guild
                    if interaction.guild:
                        await interaction.response.send_message(finalmessage + "\n" + "**This message has been disabled by the guild Administrator.**", ephemeral=True)
                    else:
                        await interaction.response.send_message(finalmessage)
            else:
                # detection_status is enabled (normal)
                if deadcode:
                    # detection_status is enabled, deadcode is disabled
                    if not interaction.guild:
                        # detection_status is enabled, deadcode is disabled, no guild
                        await interaction.response.send_message("<:DNF:1368989100220092516> **That Geocache doesn't exist!**")
                    else:
                        # detection_status is enabled, deadcode is disabled, yes guild
                        await interaction.response.send_message("<:DNF:1368989100220092516> **That Geocache doesn't exist!** | This message has been disabled by the guild Administrator.", ephemeral=True)
                else:
                    # detection_status is enabled, deadcode is enabled, any guild
                    if interaction.guild:
                        await interaction.response.send_message(finalmessage)
                    else:
                        await interaction.response.send_message(finalmessage)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await interaction.followup.send("I couldn't find any valid Geocache or Trackable codes in your input. Please try again.")
        
# ROT DECODE|ENCODE
    @app_commands.command(name="rotcipher", description="Encode or decode text with ROT-N letter and number ciphers.")
    @app_commands.describe(
        mode="Encode or decode the text",
        text_rot="How much to rotate letters (1–25)",
        num_rot="How much to rotate numbers (1–9)",
        text="The text to process"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="Encode", value="encode"),
        app_commands.Choice(name="Decode", value="decode"),
    ])
    async def rotcipher(
        self,
        interaction: discord.Interaction,
        mode: app_commands.Choice[str],
        text: str,
        text_rot: app_commands.Range[int, 1, 25] = None,
        num_rot: app_commands.Range[int, 1, 9] = None
    ):
        if text_rot:
            word = num2words(text_rot)
        else:
            text_rot = 0
        if num_rot:
            word = num2words(num_rot)
        else:
            num_rot = 0

        alpha_shift = text_rot if mode.value == "encode" else -text_rot
        digit_shift = num_rot if mode.value == "encode" else -num_rot

        result = rot_cipher.rot_combo(text, alpha_shift, digit_shift)
        if mode.value == "encode":
            await interaction.channel.send(f"That's ROTten... or is it ROT{word}? {result}")
            await interaction.response.send_message(f"I encoded it...", ephemeral=True)
        if mode.value == "decode":
            await interaction.response.send_message(f"I decoded that ROTten text... wait nevermind its ROT{word}. {result}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Geocaching(bot))