from functions import *
from discord.ext import commands
from discord import app_commands, Role
import discord
from discord.app_commands import Transform, Transformer
from database import get_guild_settings, update_guild_settings
from datetime import datetime
from typing import List
from logger import log

class RoleTransformer(Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> List[Role]:
        roles = []
        for role_id in value.split():
            role = discord.utils.get(interaction.guild.roles, id=int(role_id.strip("<@&>")))
            if not role:
                raise ValueError(f"Role {role_id} not found.")
            roles.append(role)
        return roles

class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# SETPERM
    @app_commands.command()
    @app_commands.describe(roles="The roles to add as permission roles.")
    async def setperm(self, interaction: discord.Interaction, roles: Transform[List[Role], RoleTransformer]):
        """Add roles to the permission roles."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=YOUCANTDOTHIS, ephemeral=True)
            return
        
        for role in roles:
            if isinstance(role, (discord.User, discord.Member)):
                await interaction.response.send_message("❌ You must specify at least one role! Users cannot be added.", ephemeral=True)
                return
        
        guild_id = interaction.guild.id
        settings = get_guild_settings(guild_id)

        existing_roles = set(settings.perm_role_ids.split(",")) if settings.perm_role_ids else set()
        new_roles = {str(role.id) for role in roles}
        updated_roles = existing_roles.union(new_roles)

        update_guild_settings(guild_id, perm_role_ids=",".join(updated_roles))
        await interaction.response.send_message(f"✅ Added permission roles: {', '.join(role.mention for role in roles)}")
        await log(interaction, f"Added permission roles: {', '.join(role.mention for role in roles)}")

# REMOVEPERM
    @app_commands.command()
    @app_commands.describe(roles="The roles to remove from permission roles.")
    async def removeperm(self, interaction: discord.Interaction, roles: Transform[List[Role], RoleTransformer]):
        """Remove roles from the permission roles."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=YOUCANTDOTHIS, ephemeral=True)
            return
        guild_id = interaction.guild.id
        settings = get_guild_settings(guild_id)

        existing_roles = set(settings.perm_role_ids.split(",")) if settings.perm_role_ids else set()
        roles_to_remove = {str(role.id) for role in roles}
        updated_roles = existing_roles - roles_to_remove

        update_guild_settings(guild_id, perm_role_ids=",".join(updated_roles))
        await interaction.response.send_message(f"✅ Removed permission roles: {', '.join(role.mention for role in roles)}")
        await log(interaction, f"Removed permission roles: {', '.join(role.mention for role in roles)}")

# SETSKULLBOARD
    @app_commands.command()
    @app_commands.choices(status=[
        app_commands.Choice(name="Enable ", value="1"),
        app_commands.Choice(name="Disable", value="2")
    ])
    @commands.has_permissions(administrator=True)
    @app_commands.describe(channel="The channel to send skullboard messages to if enabled.")
    @app_commands.describe(status="Enable or disable the skullboard feature.")
    async def setskullboard(self, interaction: discord.Interaction, status: app_commands.Choice[str], channel: discord.TextChannel = None):
        """Enable or disable the skullboard feature."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=YOUCANTDOTHIS, ephemeral=True)
            return
        if status.value == "1" and not channel:
            await ctx.reply("❌ You must specify a channel when enabling Skullboard!", ephemeral=True)
            return

        skullboard_status = True if status.value == "1" else False

        update_guild_settings(interaction.guild.id, skullboard_status=skullboard_status, skullboard_channel_id=channel.id if status.value == "1" else None)
        
        if status.value == "1":
            await interaction.response.send_message(f"✅ Skullboard enabled in {channel.mention}!")
            await log(interaction, f"Skullboard enabled in {channel.mention}")
        else:
            await interaction.response.send_message("✅ Skullboard disabled!") 
            await log(interaction, "Skullboard disabled")

# SETTINGS          
    @app_commands.command()
    @commands.has_permissions(administrator=True)
    async def settings(self, interaction: discord.Interaction):
        """Fetch and display the guild settings."""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=YOUCANTDOTHIS, ephemeral=True)
            return
        guild_id = interaction.guild.id
        settings = get_guild_settings(guild_id)

        embed = discord.Embed(title="Guild Settings", color=0xad7e66)
        
        perm_roles = settings.perm_role_ids.split(",") if settings.perm_role_ids else []

        embed.add_field(
            name="Perm Roles",
            value=", ".join(f"<@&{role_id}>" for role_id in sorted(set(perm_roles))) if perm_roles else "None",
            inline=False
        )
        embed.add_field(name="Skullboard Enabled", value="Yes" if settings.skullboard_status else "No", inline=False)
        embed.add_field(name="Skullboard Channel", value=f"<#{settings.skullboard_channel_id}>" if settings.skullboard_channel_id else "Not set", inline=False)

        await interaction.response.send_message(embed=embed) 

# FOXFIL
    @app_commands.command()
    @is_perm_mod()
    async def foxfil(self, interaction: discord.Interaction):
        """Sends some useful websites."""
        embed = discord.Embed(title="Websites, applications, and other resources for Geocaching",
                            description="**Websites**\n- [Geocaching.com](https://www.geocaching.com/) - Official international website.\n- [Shop Geocaching](https://shop.geocaching.com/) - Official geocaching shop where you can buy cache containers, trackables, wearables and more.    \n- [Project-GC](https://project-gc.com/) - Website that gives a lot of statistics about your geocaching account.\n- [GeoCheck](https://geocheck.org/) - Coordinates checker for geocaches.\n- [Certitude](https://certitudes.org/) - Tool used to validate solutions for geocaching puzzles.\n- [Geocaching.su](https://geocaching.su/) - Website for geocaching in the post-Soviet countries.\n- [Geocaching Toolbox](https://www.geocachingtoolbox.com/) - A lot of tools for geocachers mainly to solve puzzles and do operations with coordinates.\n- [My Geocaching Profile](https://mygeocachingprofile.com/) - Website to build a detailed profile of your geocaching accomplishments.\n- [CacheSleuth](https://www.cachesleuth.com/) - Website with many useful tools for geocaching (mainly text decoders).\n- [LonelyCache](https://www.lonelycache.com/) - Website with the list of geocaches that were not found in many years.\n- [GC Wizard Web View](https://gcwizard.net/) - A web view of the GC Wizard app.\n- [SolvedJigidi](https://solvedjigidi.com/) - The database of solved Jigidi geocaches.\n- [Webwigo](https://www.webwigo.net/) - Website for virtual playing of Wherigo geocaches.\n- [The A-Team Caching - Souvenirs](https://thea-team.net/souvenir) - Website with information on all souvenirs.\n\n\n**Apps**\n- [Geocaching®](https://www.geocaching.com/play/mobile) - An official app for geocaching.\n- [Wherigo](https://apps.apple.com/us/app/wherigo/id1538051913) - `[iOS]` An official app to play Wherigo geocaches.\n- [WhereYouGo](https://play.google.com/store/apps/details?id=menion.android.whereyougo&pcampaignid=web_share) - `[Android]` Open source, unofficial app for playing Whereigo geocaches.\n- [c:geo](https://play.google.com/store/apps/details?id=cgeo.geocaching) - `[Android]` The most popular free unofficial app for geocaching. Has many tools the official app doesn't have.\n- [Cachly](https://www.cachly.com/) - `[iOS]` Paid unofficial app for geocaching. Has many tools the official app doesn't have.\n- [GC Wizard](https://blog.gcwizard.net/about/) - An open-source tool collection for Android and iOS. It was created to offer Geocachers an offline tool to support them with in-field mysteries and riddles.\n- [Geocaching Buddy](https://gcbuddy.com/) - Paid geocaching app that recalculates waypoint formulas based on discovered clues when solving multi-caches.\n- [TBScan](https://tbscan.com/) - An app to discover trackables just by pointing your camera at the code.\n- [Raccoon](https://apps.apple.com/us/app/raccoon-geocaching-tool/id424398764) - `[iOS]` Geocaching app that should help you with multi or mystery caches.\n- [Geocaching4Locus](https://geocaching4locus.eu/) - `[Android]` Locus map add-on which allows you to download and import caches directly from Geocaching.com site.\n- [GeoGet](https://www.geoget.cz/doku.php/start) - `[Windows]` Geocache manager, where you can manage your final waypoints, add notes or waypoints to geocache or import/export geocache from/to GeoGet.\n- [GSAK (Geocaching Swiss Army Knife)](https://gsak.net/index.php/) - `[Windows]` Desktop app for managing geocaches and waypoints.\n- [CacheStats](https://logicweave.com/) - `[Windows]` Application that displays your geocaching statistics.\n- [Caching on Kai](https://caching-on-kai.com/) - `[KaiOS]` Geocaching app for KaiOS users.\n- [Cacher](https://apps.garmin.com/apps/624aed67-b068-45b4-92af-cbc1885b7e1d) - `[Garmin]` Gatmin watch app for geocaching.\n\n\n**Other**\n- [pycaching](https://pypi.org/project/pycaching) - Python 3 interface for working with Geocaching.com website.\n- [GC little helper II](https://github.com/2Abendsegler/GClh/tree/collector) - Powerful tool to enhance and extend the functionality of the geocaching website.\n\n**Do you want to add something?**\nContribute on [GitHub](https://github.com/FoxFil/awesome-geocaching) or just message @foxfil in Discord!",
                            colour=0xff9661)

        embed.set_footer(text="Made by FoxFil and contributors with 🧡",
                        icon_url="https://cdn-icons-png.flaticon.com/512/25/25231.png")

        await interaction.response.send_message(embed=embed)  
        
# DEV CMD LIST
    @commands.command()
    async def dev_cmds(self, ctx):
        """List of Dev only commands."""
        embed = discord.Embed(title="Dev Only Commands",
                      description="- ALL /debug commands\n- Sync, status, clear_cmds\n- ALL /tb force__ commands\n- TB purge\n\nTrying to use these commands results in a 'You can't do this!' error.",
                      colour=0xf50000)
        await ctx.send(embed=embed)
        
# PERM CMD LIST
    @commands.command()
    async def perm_cmds(self, ctx):
        """List of Permission only commands."""
        embed = discord.Embed(title="Permission Only Commands",
                            description="- Say, react, edit, delete, reply\n- FoxFil\n\nYou can use these commands if you have a role allowed via /setperm.\nTrying to use these commands without permissions results in a 'You can't do this!' error.",
                            colour=0xf50000)
        await ctx.send(embed=embed)

# ABOUT ME
    @commands.hybrid_command()
    async def about(self, ctx):
        """About the bot, and the Dev team."""
        total, prefix, slash = get_command_counts(self.bot)
        embed = discord.Embed(title="About Me",
                            description=f"Yo! I'm Tracker, the ultimate Discord bot for Geocachers, made by Geocachers. Here's a bit about me...\nI'm made by a small team of Developers and Helpers. These people are:\n- CBH (me!, Lead Developer & Founder),\n- democat (Assistant Developer),\n- mikaboo055 (Tester & Helper),\n- echoperson (Tester & Helper),\n- fisk (Bugfixer & Tester),\n- FoxFil (Development Helper, yall can thank him for code detection)\nWe have worked hard to make this bot and grow it to how it is now, and your support means the world to us.\nHere's some info about me, the bot:\n- I am in **{len(self.bot.guilds)}** servers,\n- I have **{total}** commands,\n- I am written in Python, more specifically with the discord.py library,\n- My prefix is **!**, but I mainly use slash (**/**) commands,\n- My website is [trackerbot.xyz](<https://trackerbot.xyz>).",
                            colour=0xad7e66)
        await ctx.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(Other(bot))