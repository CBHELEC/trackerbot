import discord
from functions import *
from discord import app_commands
from discord.ext import commands

class BadgeInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# BADGEINFO
    @app_commands.command()
    async def badgeinfo(self, interaction: discord.Interaction):
        """Shows info about badges and belts."""
        home_embed = discord.Embed(title="What do the badges and belts mean?",
                    description="You used this command because you wanted to know what they mean, and I don't blame you. Press the respective button below to find out what the belts mean, and what the badges mean.",
                    colour=0xad7e66)
        view = BadgeInfoView()
        await interaction.response.send_message(embed=home_embed, view=view, ephemeral=False)
        
async def setup(bot):
    await bot.add_cog(BadgeInfo(bot))