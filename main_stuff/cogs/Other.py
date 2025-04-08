from functions import *
from discord.ext import commands
from discord import app_commands
import discord
from database import get_guild_settings, update_guild_settings
from datetime import datetime

class Other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="setmod", description="Set the moderator roles.")
    @commands.has_permissions(administrator=True)
    async def setmod(self, ctx, roles: commands.Greedy[discord.Role]):
        role_ids = ",".join(str(role.id) for role in roles)  
        update_guild_settings(ctx.guild.id, mod_role_ids=role_ids)
        await ctx.reply(f"✅ Moderator roles set: {', '.join(role.mention for role in roles)}")

    @commands.hybrid_command(name="setperm", description="Set the permission roles.")
    @commands.has_permissions(administrator=True)
    async def setperm(self, ctx, roles: commands.Greedy[discord.Role]):
        role_ids = ",".join(str(role.id) for role in roles)  
        update_guild_settings(ctx.guild.id, perm_role_ids=role_ids)
        await ctx.reply(f"✅ Permission roles set: {', '.join(role.mention for role in roles)}")

    @commands.hybrid_command(name="setskullboard", description="Enable or disable the skullboard feature.")
    @commands.has_permissions(administrator=True)
    async def setskullboard(self, ctx, status: bool, channel: discord.TextChannel = None):
        if status and not channel:
            await ctx.reply("❌ You must specify a channel when enabling Skullboard!", ephemeral=True)
            return

        update_guild_settings(ctx.guild.id, skullboard_status=status, skullboard_channel_id=channel.id if status else None)
        
        if status:
            await ctx.reply(f"✅ Skullboard enabled in {channel.mention}!")
        else:
            await ctx.reply("✅ Skullboard disabled!")
            
    @commands.hybrid_command()
    async def settings(self, ctx):
        """Fetch and display the guild settings."""
        guild_id = ctx.guild.id
        settings = get_guild_settings(guild_id)

        embed = discord.Embed(title="Guild Settings", color=0xad7e66)
        
        mod_roles = settings.mod_role_ids.split(",") if settings.mod_role_ids else []
        perm_roles = settings.perm_role_ids.split(",") if settings.perm_role_ids else []

        embed.add_field(
            name="Mod Roles",
            value=", ".join(f"<@&{role_id}>" for role_id in sorted(set(mod_roles))) if mod_roles else "None",
            inline=False
        )

        embed.add_field(
            name="Perm Roles",
            value=", ".join(f"<@&{role_id}>" for role_id in sorted(set(perm_roles))) if perm_roles else "None",
            inline=False
        )
        embed.add_field(name="Skullboard Enabled", value="Yes" if settings.skullboard_status else "No", inline=False)
        embed.add_field(name="Skullboard Channel", value=f"<#{settings.skullboard_channel_id}>" if settings.skullboard_channel_id else "Not set", inline=False)

        await ctx.send(embed=embed)

    # FOXFIL
    @app_commands.command()
    @is_perm_mod()
    async def foxfil(self, interaction: discord.Interaction):
        """Sends some useful websites."""
        embed = discord.Embed(title="Websites, applications, and other resources for Geocaching",
                                description="**Websites**\n- [Geocaching.com](https://www.geocaching.com/) - Official international website.\n- [Shop Geocaching](https://shop.geocaching.com/) - Official geocaching shop where you can buy cache containers, trackables, wearables and more.    \n- [Project-GC](https://project-gc.com/) - Website that gives a lot of statistics about your geocaching account.\n- [GeoCheck](https://geocheck.org/) - Coordinates checker for geocaches.\n- [Certitude](https://certitudes.org/) - Tool used to validate solutions for geocaching puzzles.\n- [Geocaching.su](https://geocaching.su/) - Website for geocaching in the post-Soviet countries.\n- [Geocaching Toolbox](https://www.geocachingtoolbox.com/) - A lot of tools for geocachers mainly to solve puzzles and do operations with coordinates.\n- [My Geocaching Profile](https://mygeocachingprofile.com/) - Website to build a detailed profile of your geocaching accomplishments.\n- [CacheSleuth](https://www.cachesleuth.com/) - Website with many useful tools for geocaching (mainly text decoders).\n- [LonelyCache](https://www.lonelycache.com/) - Website with the list of geocaches that were not found in many years.\n- [GC Wizard Web View](https://gcwizard.net/) - A web view of the GC Wizard app.\n- [SolvedJigidi](https://solvedjigidi.com/) - The database of solved Jigidi geocaches.\n- [Webwigo](https://www.webwigo.net/) - Website for virtual playing of Wherigo geocaches.\n\n\n**Apps**\n- [Geocaching®](https://www.geocaching.com/play/mobile) - An official app for geocaching.\n- [Wherigo](https://apps.apple.com/us/app/wherigo/id1538051913) - `[iOS]` An official app to play Wherigo geocaches.\n- [WhereYouGo](https://play.google.com/store/apps/details?id=menion.android.whereyougo&pcampaignid=web_share) - `[Android]` Open source, unofficial app for playing Whereigo geocaches.\n- [c:geo](https://play.google.com/store/apps/details?id=cgeo.geocaching) - `[Android]` The most popular free unofficial app for geocaching. Has many tools the official app doesn't have.\n- [Cachly](https://www.cachly.com/) - `[iOS]` Paid unofficial app for geocaching. Has many tools the official app doesn't have.\n- [GC Wizard](https://blog.gcwizard.net/about/) - An open-source tool collection for Android and iOS. It was created to offer Geocachers an offline tool to support them with in-field mysteries and riddles.\n- [Geocaching Buddy](https://gcbuddy.com/) - Paid geocaching app that recalculates waypoint formulas based on discovered clues when solving multi-caches.\n- [TBScan](https://tbscan.com/) - An app to discover trackables just by pointing your camera at the code.\n- [Raccoon](https://apps.apple.com/us/app/raccoon-geocaching-tool/id424398764) - `[iOS]` Geocaching app that should help you with multi or mystery caches.\n- [Geocaching4Locus](https://geocaching4locus.eu/) - `[Android]` Locus map add-on which allows you to download and import caches directly from Geocaching.com site.\n- [GeoGet](https://www.geoget.cz/doku.php/start) - `[Windows]` Geocache manager, where you can manage your final waypoints, add notes or waypoints to geocache or import/export geocache from/to GeoGet.\n- [GSAK (Geocaching Swiss Army Knife)](https://gsak.net/index.php/) - `[Windows]` Desktop app for managing geocaches and waypoints.\n- [CacheStats](https://logicweave.com/) - `[Windows]` Application that displays your geocaching statistics.\n- [Caching on Kai](https://caching-on-kai.com/) - `[KaiOS]` Geocaching app for KaiOS users.\n- [Cacher](https://apps.garmin.com/apps/624aed67-b068-45b4-92af-cbc1885b7e1d) - `[Garmin]` Gatmin watch app for geocaching.\n\n**Other**\n- [pycaching](https://pypi.org/project/pycaching) - Python 3 interface for working with Geocaching.com website.\n- [GC little helper II](https://github.com/2Abendsegler/GClh/tree/collector) - Powerful tool to enhance and extend the functionality of the geocaching website.\n⠀",
                                colour=0xad7e66,
                                timestamp=datetime.now())
        
        embed.add_field(name="Do you know some other awesome recources for geocaching?",
                        value="Feel free to contribute on [GitHub](https://github.com/foxfil/awesome-geocaching) or just message @foxfil in Discord!",
                        inline=False)
        
        embed.set_footer(text="Made by FoxFil and contributors with 🧡",
                            icon_url="https://cdn-icons-png.flaticon.com/512/25/25231.png")

        await interaction.response.send_message(embed=embed)
    
    @foxfil.error
    async def foxfil_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(embed=YOUCANTDOTHIS, ephemeral=True)
        else:
            raise error   
        
async def setup(bot):
    await bot.add_cog(Other(bot))