from functions import *
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # HOST
    @app_commands.command()
    async def host_info(self, interaction: discord.Interaction):
        """Shows info about me and my host."""
        now = datetime.now()
        delta = now - self.bot.start_time
        formatted = str(delta).split('.')[0]
        embed = discord.Embed(title="Tracker's Status",
                      description=f"Heya, I am running on a Raspberry Pi 3b cable tied behind my Dev's monitor, taped inside a cardboard box. I'm not a fan of it, but I can't do anything about it. Heres a lil more about me:\n⌚ | Uptime: **{formatted}** (HH:MM:SS)\n{get_formatted_ram_usage()}\n{get_formatted_cpu_usage()}\n{get_formatted_storage_usage()}",
                      colour=0xad7e66)

        embed.set_footer(text="Developed by not.cbh | /invite support")
        await interaction.response.send_message(embed=embed)
        
    # UPTIME
    @commands.hybrid_command()
    async def uptime(self, ctx):
        """Display bot's uptime (H:M:S)."""
        now = datetime.now()
        delta = now - self.bot.start_time
        formatted = str(delta).split('.')[0]
        await ctx.reply(f"Bot Uptime: **{formatted}**")

    # PING
    @commands.hybrid_command()
    async def ping(self, ctx):
        """Sends the bot's latency."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! {latency}ms")
        
    # STATUS  
    @app_commands.command()
    @is_dev()
    @app_commands.describe(new_status="The new status for the bot.")
    async def status(self, interaction: discord.Interaction, *, new_status: str):
        """⚙️ | Change the Bot's status."""
        await self.bot.change_presence(activity=discord.CustomActivity(name=new_status))
        await interaction.response.send_message(f'Status changed to: `{new_status}`', ephemeral=True)
        await master_log_message(interaction.guild, self.bot, interaction.command.name,f"{interaction.user.mention} ({interaction.user.name}) changed my status to `{new_status}`.")

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
        embed = discord.Embed(description="'Tracker' brought to you by <@820297275448098817> w/ help from <@624616551898808322>\n[Click for Bot Invite](https://discord.com/oauth2/authorize?client_id=1322305662973116486)",
                            colour=0xad7e66)

        embed.add_field(name="Message",
                        value="/say <saying> - Says what you wanted where you wanted\n/reply <message_id> <message> - Replies to a specific message\n/react <messageID> <reaction> - Reacts to a specific message\n/delete <messageID> - Deletes a specific message\n/edit <messageID> <newmessage> - Edits a specific message",
                        inline=False)
        embed.add_field(name="Geocaching",
                        value="/badgebar <dc_user> <gc_user> - Sends a badgebar image\nIf dc_user or gc_user are blank, it defaults to your Discord display name\n/badgeinfo - Shows info about badges and belts\n/statbar <dc_user> <gc_user> <labcaches> - Sends a statbar image\nIf dc_user or gc_user are blank, it defaults to your Discord display name\nlabcaches = optional, default = true\n/ftf - Shows how to get your FTFs recognised on PGC (Project-GC)",
                        inline=False)
        embed.add_field(name="Other",
                        value="/sync - Admin / Dev Only - Syncs the Bot's app commands\n/ping - Shows the bot's latency\n/help - Shows the help menu\n/uptime - Shows the bot's uptime (HH:MM:SS)\n/host_info - Shows info about me and my host\n/foxfil - Shows info that @FoxFil made about Geocaching\n/status - Admin / Dev Only - Changes the bot's custom status\n/clear_commands - Admin / Dev Only - Clears the Bot's app commands",
                        inline=False)
        embed.add_field(name="Command Sets",
                        value="/fun help - Shows all Fun commands and what they do\n/verify help - IS NOT AVAILABLE OUTSIDE OF THE MAIN SERVER (/invite geocaching)\n-> Shows info about the verifications system and what commands do\n/tb help - Shows all commands for the public TB database and what they do",
                        inline=False)
        embed.add_field(name="Bot Configuration",
                        value="/setperm <@user or @role> - Sets users or roles that can use the message commands (/say, /delete, /edit, /react, /reply)\n/setskullboard <status (enable or disable)> <#channel (optional, if you set status to enabled)> - Sets whether the skullboard feature is enabled, and if so what channel the highlights go to\n/settings - Shows the bot configuration for your server",
                        inline=False)
        await ctx.send(embed=embed)
        
    # CLEAR CMD  
    @commands.hybrid_command()
    @is_dev()
    async def clear_cmds(self, ctx):
        """⚙️ | Clears the Bot's app commands."""
        if ctx.interaction: 
            await ctx.interaction.response.defer() 
        
        self.bot.tree.clear_commands(guild=None)
        
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
        """⚙️ | Syncs the Bot's app commands."""
        if ctx.interaction: 
            await ctx.interaction.response.defer() 
        
        await self.bot.tree.sync()
        
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