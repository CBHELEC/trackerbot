import discord
from functions import *
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Geocaching(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
    
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
        user = user.replace(" ", "%20")
        now = datetime.now()
        intYear = now.year
        intMonth = now.month
        intDay = now.day
        quotetimeusa = f"{intYear}/{intMonth:02d}/{intDay:02d}"
        if labcaches == None or labcaches.value == "2":
            await interaction.response.send_message(f"https://cdn2.project-gc.com/statbar.php?quote=discord.gg/EKn8z23KkC+-+{quotetimeusa}&includeLabcaches&user={user}")
        else:
            await interaction.response.send_message(f"https://cdn2.project-gc.com/statbar.php?quote=discord.gg/EKn8z23KkC+-+{quotetimeusa}&user={user}")
        
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
        
async def setup(bot):
    await bot.add_cog(Geocaching(bot))