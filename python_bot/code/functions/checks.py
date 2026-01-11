import discord
from database import *
from functions import static_var
from discord import app_commands

def is_perm_mod():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        mod_role_ids = {int(role) for role in settings.mod_role_ids.split(",") if role}
        perm_role_ids = {int(role) for role in settings.perm_role_ids.split(",") if role}

        if interaction.user.id == static_var.DEV_USER_ID or \
           any(role.id in mod_role_ids for role in interaction.user.roles) or \
           any(role.id in perm_role_ids for role in interaction.user.roles1):
            return True

        return False
    
    return app_commands.check(predicate)

def is_dev():
    return app_commands.check(lambda interaction: interaction.user.id == static_var.DEV_USER_ID)