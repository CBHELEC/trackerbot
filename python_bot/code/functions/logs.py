import discord
from functions import static_var

async def log_message(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the guild's log channel and the global log channel."""
    log_channel = get_log_channel(guild, bot)  
    global_log_channel = bot.get_channel(static_var.GOD_LOG_ID)  

    if log_channel:
        await log_channel.send(f"{command_name} | {message}") 

    if global_log_channel:
        await global_log_channel.send(f"God Log - Guild: {guild.name}, ID: {guild.id} | {command_name} | {message}") 

async def master_log_message(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the guild's log channel and the global log channel."""
    master_log_channel = bot.get_channel(static_var.GOD_LOG_ID)  

    if master_log_channel:
        await master_log_channel.send(f"{guild.name} ({guild.id}) | {command_name} | {message}") 

async def log_error(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the error channel."""
    log_channel = bot.get_channel(static_var.ERROR_LOG_ID)

    if log_channel:
        await log_channel.send(f"Error Log - Guild: {guild.name}, ID: {guild.id} | {command_name} | {message}") 