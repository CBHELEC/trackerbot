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
    @app_commands.describe(
    user="The user the statbar is for (Default = You)",
    labcaches="Whether labcaches are included in your total finds (Default = True)"
    )
    async def statbar(self, interaction: discord.Interaction, user: discord.Member = None, labcaches: bool = None):
        """Sends a statbar image."""
        if user == None:
            user = interaction.user
        now = datetime.now()
        intYear = now.year
        intMonth = now.month
        intDay = now.day
        quotetimeusa = f"{intYear}/{intMonth:02d}/{intDay:02d}"
        if labcaches == False:
            await interaction.response.send_message(f"https://cdn2.project-gc.com/statbar.php?quote=discord.gg/EKn8z23KkC+-+{quotetimeusa}&user={user.display_name}")
        else:
            await interaction.response.send_message(f"https://cdn2.project-gc.com/statbar.php?quote=discord.gg/EKn8z23KkC+-+{quotetimeusa}&includeLabcaches&user={user.display_name}")
        
# BADGEBAR
    @app_commands.command()
    @app_commands.describe(
    user="The user the badgebar is for (Default = You)",
    )
    async def badgebar(self, interaction: discord.Interaction, user: discord.Member = None):
        """Sends a badgebar image."""
        if user == None:
            user = interaction.user
        await interaction.response.send_message(f"https://cdn2.project-gc.com/BadgeBar/{user.display_name}.png")
        
async def setup(bot):
    await bot.add_cog(Geocaching(bot))