from functions import *
import discord
from discord import app_commands

class Invite(app_commands.Group):
    """Fun Commands!"""

# HELP
    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Shows the help command."""
        embed = discord.Embed(title="Invite Commands",
                      description="/fun support - Sends the support server invite.\n/fun geocaching - Sends the Geocaching server invite.\n/fun bot - Sends the bot invite.",
                      colour=0xad7e66)
        await interaction.response.send_message(embed=embed)

# GEOCACHING
    @app_commands.command()
    async def geocaching(self, interaction: discord.Interaction):
        """Shows the Geocaching server invite."""
        await interaction.response.send_message(f"You wanted to join the most active Geocaching server? Here's the permanent invite! discord.gg/pmuuVNptg3", ephemeral=False)
    
# SUPPORT
    @app_commands.command()
    async def support(self, interaction: discord.Interaction):
        """Shows the support server invite."""
        await interaction.response.send_message(f"You wanted to join the support server? Here's the permanent invite! discord.gg/cAXp5DSMr4", ephemeral=False)
        
# BOT INVITE
    @app_commands.command()
    async def bot_invite(self, interaction: discord.Interaction):
        """Shows the bot invite."""
        await interaction.response.send_message(f"You wanted to invite me to your server? Here's the invite! https://discord.com/oauth2/authorize?client_id=1322305662973116486", ephemeral=False)
        
# TAG INVITE
    @app_commands.command()
    async def tag(self, interaction: discord.Interaction):
        """Shows the tag server invite."""
        await interaction.response.send_message(f"You wanted to join the tag server? Here's the permanent invite! discord.gg/Srh3ZtNrP3", ephemeral=False)

invite_commands = Invite(name="invite", description="Server Invite Commands.")

async def setup(bot):
    bot.tree.add_command(invite_commands)