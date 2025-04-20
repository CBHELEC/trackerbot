from functions import *
import discord
from discord.ext import commands
from discord import app_commands
from database import *

class Debug(app_commands.Group):
    """Debug Developer commands."""
    
    @app_commands.command()
    @is_dev()
    async def setperm(self, interaction: discord.Interaction, roles: str, server_id: str = None):
        """Force add roles to the permission roles."""
        guild_id = server_id if server_id else interaction.guild.id
        settings = get_guild_settings(guild_id)

        existing_roles = set(settings.perm_role_ids.split(",")) if settings.perm_role_ids else set()
        new_roles = {str(role.id) for role in roles}
        updated_roles = existing_roles.union(new_roles)

        update_guild_settings(guild_id, perm_role_ids=",".join(updated_roles))
        await interaction.response.send_message(f"⚙️🔧✅ Force added permission roles: {', '.join(role.mention for role in roles)}")
        
    @setperm.error
    async def setperm_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(embed=YOUCANTDOTHIS, ephemeral=True)
        else:
            raise error
    
dbug_commands = Debug(name="debug", description="Developer Debug Commands.")

async def setup(bot):
    bot.tree.add_command(dbug_commands)