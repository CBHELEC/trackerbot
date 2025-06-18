import discord
import asyncio
from functions import *
from discord.ext import commands
from discord import app_commands, Embed, Interaction, ButtonStyle
from datetime import datetime
from discord.ui import View, Button
from logger import log

class SectionButton(Button):
    def __init__(self, label: str, embed: Embed, view_obj: 'HelpView', style: ButtonStyle = ButtonStyle.secondary):
        super().__init__(label=label, style=style)
        self.embed = embed
        self.view_obj = view_obj

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.view_obj.author_id:
            await interaction.response.send_message("This menu isn't for you.", ephemeral=True)
            return

        self.view_obj.has_left_landing = True 
        await interaction.response.edit_message(embed=self.embed, view=self.view_obj)


class HelpView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.message = None
        self.has_left_landing = False 

        self.section_embeds = self.create_section_embeds()
        for label, embed in self.section_embeds.items():
            self.add_item(SectionButton(label=label, embed=embed, view_obj=self, style=ButtonStyle.success))

    def create_section_embeds(self):
        color = 0xad7e66
        return {
            "Message": Embed(
                title="📨 | Message Commands",
                description="/message say <saying> - Says what you wanted where you wanted\n"
                            "/message reply <message_id> <message> - Replies to a specific message\n"
                            "/message react <messageID> <reaction> - Reacts to a specific message\n"
                            "/message delete <messageID> - Deletes a specific message\n"
                            "/message edit <messageID> <newmessage> - Edits a specific message",
                color=color
            ),
            "Geocaching": Embed(
                title="🧭 | Geocaching Commands",
                description="/badgebar <dc_user> <gc_user> - Sends a badgebar image\n"
                            "If dc_user or gc_user are blank, it defaults to your Discord display name\n"
                            "/badgeinfo - Shows info about badges and belts\n"
                            "/statbar <dc_user> <gc_user> <labcaches> - Sends a statbar image\n"
                            "If dc_user or gc_user are blank, it defaults to your Discord display name\n"
                            "labcaches = optional, default = true\n"
                            "/ftf - Shows how to get your FTFs recognised on PGC (Project-GC)",
                color=color
            ),
            "Other": Embed(
                title="⚙️ | Other Commands",
                description="/sync - 🔧⚙️ - Syncs the Bot's app commands\n"
                            "/ping - Shows the bot's latency\n"
                            "/help - Shows the help menu\n"
                            "/uptime - Shows the bot's uptime (HH:MM:SS)\n"
                            "/host_info - Shows info about me and my host\n"
                            "/foxfil - Shows info that @FoxFil made about Geocaching\n"
                            "/status - 🔧⚙️ - Changes the bot's custom status\n"
                            "/about - Shows info about the bot and its developers\n"
                            "/clear_commands - 🔧⚙️ - Clears the Bot's app commands",
                color=color
            ),
            "Command Sets": Embed(
                title="📦 | Command Sets",
                description="/fun help - Shows all Fun commands and what they do\n"
                            "/verify help - IS NOT AVAILABLE OUTSIDE OF THE MAIN SERVER (/invite geocaching)\n"
                            "shows info about the verification system and what commands do\n"
                            "/tb help - Shows all commands for the public TB database and what they do\n"
                            "/invite help - Shows all invite commands and what they do",
                color=color
            ),
            "Bot Configuration": Embed(
                title="🔧 | Bot Configuration",
                description="/setperm <@role> - Sets roles that can use the message commands\n"
                            "(/say, /delete, /edit, /react, /reply)\n"
                            "/setskullboard <status (enable or disable)> <#channel> - Sets whether skullboard is enabled and which channel it posts to\n"
                            "/toggles - Toggles the bot's features on or off\n"
                            "/settings - Shows the bot configuration for your server",
                color=color
            ),
        }

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            print(self.message.id)
            await self.message.edit(view=self)

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
        await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) changed my status to `{new_status}`.")
        
# HELP
    @commands.hybrid_command()
    async def help(self, ctx):
        """Shows the help menu."""
        view = HelpView(author_id=ctx.author.id)

        landing_embed = Embed(
            title="📘 Help Menu",
            description="'Tracker' brought to you by <@820297275448098817> w/ help from friends (!about)\n"
                        "**__[Click for Bot Invite](https://discord.com/oauth2/authorize?client_id=1322305662973116486)__**\n"
                        "**__[Click for Dashboard Link](https://dashboard.trackerbot.xyz)__**\n\n"
                        "***Press a button below to view a section.***",
            color=0xad7e66
        )

        view.message = await ctx.send(embed=landing_embed, view=view)
        
# CLEAR CMD  
    @commands.hybrid_command()
    @is_dev()
    async def clear_cmds(self, ctx):
        """⚙️ | Clears the Bot's app commands."""
        if ctx.interaction: 
            await ctx.interaction.response.defer() 
        
        self.bot.tree.clear_commands(guild=None)
        
        message = await ctx.reply("Commands Cleared!", mention_author=False)
        await log(ctx, f"{ctx.user.mention} ({ctx.user.name}) cleared the bot's app commands.")
        
        await asyncio.sleep(5)
        if message:
            await message.delete()
        else:
            return
        
# SYNC    
    @commands.hybrid_command()
    @is_dev()
    async def sync(self, ctx):
        """⚙️ | Syncs the Bot's app commands."""
        if ctx.interaction: 
            await ctx.interaction.response.defer() 
        
        await self.bot.tree.sync()
        
        message = await ctx.reply("Synced!", mention_author=False)
        await log(ctx, f"{ctx.user.mention} ({ctx.user.name}) synced the bot's app commands.")
        
        await asyncio.sleep(5)
        if message:
            await message.delete()
        else:
            return   
    
# RELOAD    
    @app_commands.command(name="reload", description="Reloads all cogs.")
    @is_dev()
    async def reload(self, interaction: discord.Interaction):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for filename in os.listdir(script_dir):
            if filename.endswith(".py"):
                try:
                    await self.bot.unload_extension(f"cogs.{filename[:-3]}")
                    await self.bot.load_extension(f"cogs.{filename[:-3]}")
                except Exception as e:
                    print(f"Failed to reload {filename}: {e}")
        await interaction.response.send_message("Cogs reloaded!")
        await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) reloaded all cogs.")
    
# meme mode
    @app_commands.command(name="meme_mode", description="Memes the memers.")
    @is_dev()
    async def meme_mode(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Toggles meme mode."""
        await interaction.response.send_message("meme time fuckers")
        for i in range(amount):
            await interaction.channel.send(f"wassup fucker {user.mention}, you have been memed")

    @app_commands.command(name="test", description="Test command for development purposes.")
    @is_dev()
    async def test(self, interaction: discord.Interaction):
        # Fetch all global commands
        commands = await interaction.client.tree.fetch()
        # Find your command by name
        for cmd in commands:
            if cmd.name == "test":
                await interaction.response.send_message(f"ID: {cmd.id}", ephemeral=True)
                return
        await interaction.response.send_message("Command ID not found.", ephemeral=True)
        
async def setup(bot):
    await bot.add_cog(Dev(bot))