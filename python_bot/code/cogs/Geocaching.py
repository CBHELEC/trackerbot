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
        self._last_member = None
    
    from dotenv import load_dotenv
    load_dotenv(".env")
    EMAIL = os.getenv('EMAIL')
    PASSWORD = os.getenv('PASSWORD')
    
# FTF
    @app_commands.command()
    async def ftf(self, interaction: discord.Interaction):
        """Shows how to get your FTFs recognised on PGC."""
        embed = discord.Embed(title="How to get your FTFs recognised on /statbar (Project-GC)",
                      description="There are multiple ways for Project-GC to detect your FTFs. Either you tag your logs with one of these tags: `{*FTF*}`, `{FTF}`, or `[FTF]`. Alternatively you can add an FTF bookmark list under Settings (<https://project-gc.com/User/Settings/>) that will be checked once per day. Please understand that FTF isn't anything offical and not everyone tags their FTFs. Therefore this list won't be 100% accurate.",
                      colour=0xad7e66)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
# STATBAR
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
    @app_commands.command()
    @app_commands.describe(
    gc_user="The Geocaching username the statbar will be made for",
    dc_user="The Discord user display name the statbar will be made for",
    )
    async def badgebar(self, interaction: discord.Interaction, gc_user: str = None, dc_user: discord.Member = None):
        """Sends a badgebar image."""
        user = gc_user if gc_user else dc_user.display_name if dc_user else interaction.user.display_name
        user = user.replace(" ", "%20")
        await interaction.response.send_message(f"https://cdn2.project-gc.com/BadgeBar/{user}.png")
        
# GC_INFO
    @app_commands.user_install()
    @app_commands.command()
    @app_commands.describe(gc_code="The gc code to get info for")
    @app_commands.allowed_installs(guilds=False, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def gc_info(self, interaction: discord.Interaction, gc_code: str):
        """Sends info about a GC code."""
        await interaction.response.defer()
        clean_content = re.sub(r'[^A-Za-z0-9\s]', '', gc_code)
        matches = re.findall(r'\bGC\w*\b', clean_content, re.IGNORECASE)
        match = re.findall(r'\bTB\w*\b', clean_content, re.IGNORECASE)

        gc_codes = [item.upper() for item in matches]
        tb_codes = [item.upper() for item in match]

        gcblacklist = ["GC", "GCHQ"]
        tbblacklist = ["TB", "TBF", "TBH", "TBS"]

        if any(code in gcblacklist for code in gc_codes):
            return 
        if any(code in tbblacklist for code in tb_codes):
            return  

        if matches or match:
            finalmessage = get_cache_basic_info(gc_codes, tb_codes)
            await interaction.followup.send(finalmessage)
        
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