from functions import *
import discord
from discord.ext import commands
from discord import app_commands
from bot import bot
import asyncio

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # PING
    @commands.hybrid_command()
    async def ping(self, ctx):
        """Sends the bot's latency."""
        latency = round(bot.latency * 1000)
        await ctx.send(f"Pong! {latency}ms")
        
    # STATUS  
    @app_commands.command()
    @is_dev()
    async def status(self, interaction: discord.Interaction, *, new_status: str):
        """⚙️ | Change the Bot's status."""
        await bot.change_presence(activity=discord.CustomActivity(name=new_status))
        await interaction.response.send_message(f'Status changed to: `{new_status}`', ephemeral=True)
        await master_log_message(interaction.guild, bot, interaction.command.name,f"{interaction.user.mention} ({interaction.user.name}) changed my status to `{new_status}`.")

    @status.error
    async def status_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(embed=YOUCANTDOTHIS, ephemeral=True)
        else:
            raise error   
        
    # HELP
    @commands.hybrid_command()
    async def help(self, ctx):
        """Shows the help menu."""
        embed = discord.Embed(description="'Tracker' brought to you by <@820297275448098817> w/ help from <@624616551898808322>",
                        colour=0xad7e66)
        embed.add_field(name="Message",
                        value="/say <saying> - Says what you wanted where you wanted\n/reply <message_id> <message> - Replies to a specific message\n/react <messageID> <reaction> - Reacts to a specific message\n/delete <messageID> - Deletes a specific message\n/edit <messageID> <newmessage> - Edits a specific message",
                        inline=False)
        embed.add_field(name="Geocaching",
                        value="/badgebar <user> - Sends a badgebar image \n    user = optional, default = you\n/badgeinfo - Shows info about badges and belts\n/statbar <user> <labcaches> - Sends a statbar image\n    user = optional, default = you,\n    labcaches = optional, default = true\n/ftf - Shows how to get your FTFs recognised on PGC",
                        inline=False)
        embed.add_field(name="Other",
                        value="/sync - Admin / Dev Only - Syncs the Bot's app commands\n/ping - Shows the bot's latency\n/verify help - View verification commands - Only available in ONE server\n/tb help - View TB database commands\n/unverified - Shows a list of unverified users\n/help - Shows the help menu",
                        inline=False)
        await ctx.send(embed=embed)
        
    # CLEAR CMD  
    @commands.hybrid_command()
    @is_dev()
    async def clear_cmds(self, ctx):
        """⚙️ - Clears the Bot's app commands."""
        if ctx.interaction: 
            await ctx.interaction.response.defer() 
        
        bot.tree.clear_commands(guild=None)
        
        message = await ctx.reply("Commands Cleared!", mention_author=False)
        
        await asyncio.sleep(5)
        if message:
            await message.delete()
        else:
            return
        
    @clear_cmds.error
    async def clear_commands_error(self, ctx, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await ctx.send(embed=YOUCANTDOTHIS, ephemeral=True)
        else:
            raise error 
        
    # SYNC    
    @commands.hybrid_command()
    @is_dev()
    async def sync(self, ctx):
        """⚙️ - Syncs the Bot's app commands."""
        if ctx.interaction: 
            await ctx.interaction.response.defer() 
        
        await bot.tree.sync()
        
        message = await ctx.reply("Synced!", mention_author=False)
        
        await asyncio.sleep(5)
        if message:
            await message.delete()
        else:
            return
        
    @sync.error
    async def sync_error(self, ctx, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await ctx.send(embed=YOUCANTDOTHIS, ephemeral=True)
        else:
            raise error   
        
async def setup(bot):
    await bot.add_cog(Dev(bot))