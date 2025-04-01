import requests
import asyncio
from datetime import datetime, timezone
import operator
import os
import random
from random import uniform
import re
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from discord import app_commands, Embed
from discord.ui import Select, View, Button, Modal, TextInput
import json
import sqlite3
import pycaching
from google_images_search import GoogleImagesSearch
from googleapiclient.discovery import build
import warnings
from database import get_guild_settings, update_guild_settings, get_log_channel
from io import BytesIO
from PIL import Image, ImageSequence
from economy import (
    get_balance, get_hides, get_finds, get_fav_points_owned, get_fav_points_recieved,
    get_fake_finds_owned, get_fake_finds_recieved, get_logs_recieved, get_logs_created,
    get_trackables_owned, get_trackables_activated, get_trackables_discovered, 
    get_events_hosted, get_events_attended, get_souvenirs_recieved, get_caches_damaged,
    get_cache_damage_recieved, get_cache_damage_balance,
    update_balance, update_hides, update_finds, update_fav_points_owned, update_fav_points_recieved,
    update_fake_finds_owned, update_fake_finds_recieved, update_logs_recieved, update_logs_created,
    update_trackables_owned, update_trackables_activated, update_trackables_discovered, 
    update_events_hosted, update_events_attended, update_souvenirs_recieved, update_caches_damaged,
    update_cache_damage_recieved, update_cache_damage_balance, get_hide_by_id, get_hides_by_user, 
    get_inventory, remove_inv_item, add_inv_item,
    add_hide, delete_hide, get_db_settings, set_cacher_name, add_user_to_db, get_all_hide_ids, Session
)
import logging
import string

from dotenv import load_dotenv
load_dotenv(".env")
TOKEN = os.getenv('BOT_TOKEN')
TOKEN2 = os.getenv('BOT_TOKEN_2')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CX_ID = os.getenv('GOOGLE_SEARCH_ID')
GOOGLE_NORMAL_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
GOOGLE_NORMAL_SEARCH_ID = os.getenv('GOOGLE_SEARCH_NORMAL_ID')

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('------------------------')
    #bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    await bot.add_cog(Message(bot))
    await bot.add_cog(Geocaching(bot))
    await bot.add_cog(BadgeInfo(bot))
    await bot.change_presence(
        activity=discord.CustomActivity(f"Finding Caches and Friends"))

warnings.filterwarnings('ignore') 
#logging.basicConfig(level=logging.DEBUG)

GOD_LOG_ID = 1341819097591185479 
LOG_CHANNEL_ID = True

@bot.hybrid_command(name="setlog")
async def setlog(ctx, channel: discord.TextChannel):
    update_guild_settings(ctx.guild.id, log_channel_id=channel.id)
    await ctx.reply(f"✅ Log channel set to {channel.mention}")
    
@bot.hybrid_command(name="setmod", description="Set the moderator roles.")
@commands.has_permissions(administrator=True)
async def setmod(ctx, roles: commands.Greedy[discord.Role]):
    role_ids = ",".join(str(role.id) for role in roles)  # Convert role list to CSV
    update_guild_settings(ctx.guild.id, mod_role_ids=role_ids)
    await ctx.reply(f"✅ Moderator roles set: {', '.join(role.mention for role in roles)}")

@bot.hybrid_command(name="setperm", description="Set the permission roles.")
@commands.has_permissions(administrator=True)
async def setperm(ctx, roles: commands.Greedy[discord.Role]):
    role_ids = ",".join(str(role.id) for role in roles)  # Convert role list to CSV
    update_guild_settings(ctx.guild.id, perm_role_ids=role_ids)
    await ctx.reply(f"✅ Permission roles set: {', '.join(role.mention for role in roles)}")

@bot.hybrid_command(name="setskullboard", description="Enable or disable the skullboard feature.")
@commands.has_permissions(administrator=True)
async def setskullboard(ctx, status: bool, channel: discord.TextChannel = None):
    if status and not channel:
        await ctx.reply("❌ You must specify a channel when enabling Skullboard!", ephemeral=True)
        return

    update_guild_settings(ctx.guild.id, skullboard_status=status, skullboard_channel_id=channel.id if status else None)
    
    if status:
        await ctx.reply(f"✅ Skullboard enabled in {channel.mention}!")
    else:
        await ctx.reply("✅ Skullboard disabled!")
        
@bot.hybrid_command()
async def settings(ctx):
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
    embed.add_field(name="Log Channel", value=f"<#{settings.log_channel_id}>" if settings.log_channel_id else "Not set", inline=False)
    embed.add_field(name="Skullboard Enabled", value="Yes" if settings.skullboard_status else "No", inline=False)
    embed.add_field(name="Skullboard Channel", value=f"<#{settings.skullboard_channel_id}>" if settings.skullboard_channel_id else "Not set", inline=False)

    await ctx.send(embed=embed)

# IS_ CHECKS

def is_mod():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        mod_role_ids = {int(role) for role in settings.mod_role_ids.split(",") if role}

        if interaction.user.id == 820297275448098817 or any(role.id in mod_role_ids for role in interaction.user.roles):
            return True

        await interaction.response.send_message(
            "<:denied:1336100920039313448> | You do not have permission to execute this command!", 
            ephemeral=True
        )
        return False
    
    return app_commands.check(predicate)

def is_perm():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        perm_role_ids = {int(role) for role in settings.perm_role_ids.split(",") if role} 

        if interaction.user.id == 820297275448098817 or any(role.id in perm_role_ids for role in interaction.user.roles):
            return True

        await interaction.response.send_message(
            "<:denied:1336100920039313448> | You do not have permission to execute this command!", 
            ephemeral=True
        )
        return False
    
    return app_commands.check(predicate)

def is_perm_mod():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        mod_role_ids = {int(role) for role in settings.mod_role_ids.split(",") if role}
        perm_role_ids = {int(role) for role in settings.perm_role_ids.split(",") if role}

        if interaction.user.id == 820297275448098817 or \
           any(role.id in mod_role_ids for role in interaction.user.roles) or \
           any(role.id in perm_role_ids for role in interaction.user.roles):
            return True

        await interaction.response.send_message(
            "<:denied:1336100920039313448> | You do not have permission to execute this command!", 
            ephemeral=True
        )
        return False
    
    return app_commands.check(predicate)

def is_dev():
    async def predicate(interaction: discord.Interaction):
        dev_id = 820297275448098817
        
        if interaction.user.id != dev_id:  
            await interaction.response.send_message(
                "<:denied:1336100920039313448> | You do not have permission to execute this command!", 
                ephemeral=True
            )
            return False  
        
        return True
    
    return app_commands.check(predicate)

async def log_message(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the guild's log channel and the global log channel."""
    log_channel = get_log_channel(guild, bot)  
    global_log_channel = bot.get_channel(1341819097591185479)  

    if log_channel:
        await log_channel.send(f"{command_name} | {message}") 

    if global_log_channel:
        await global_log_channel.send(f"God Log - Guild: {guild.name}, ID: {guild.id} | {command_name} | {message}") 
        
async def master_log_message(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the guild's log channel and the global log channel."""
    master_log_channel = bot.get_channel(1341819097591185479)  

    if master_log_channel:
        await master_log_channel.send(f"{guild.name} ({guild.id}) | {command_name} | {message}") 
        
async def log_error(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the error channel."""
    log_channel = bot.get_channel(1341107185777643573)

    if log_channel:
        await log_channel.send(f"Error Log - Guild: {guild.name}, ID: {guild.id} | {command_name} | {message}") 

def is_moderator():
    async def predicate(interaction: discord.Interaction):
        staff_roles = [1321987484615315537, 1321985543139233813]
        user_role_ids = [role.id for role in interaction.user.roles]
        
        if not any(role_id in user_role_ids for role_id in staff_roles):
            await interaction.response.send_message(
                "<:denied:1336100920039313448> | You do not have permission to execute this command!", 
                ephemeral=True
            )
            return False  
        
        return True
    
    return app_commands.check(predicate)

# TB DB

import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "trackables.db")
conn1 = sqlite3.connect(db_path)
cursor1 = conn1.cursor()

cursor1.execute("""
CREATE TABLE IF NOT EXISTS trackables (
    user_id INTEGER NOT NULL,
    gc_username TEXT NOT NULL,
    uploaded_time TIMESTAMP CURRENT_TIMESTAMP,
    tb_code TEXT NOT NULL,
    code TEXT PRIMARY KEY NOT NULL
)
""")
conn1.commit()

def ensure_columns_exist_trackables():
    expected_columns = [
        "user_id", "gc_username", "uploaded_time", "code",  "tb_code"
    ]

    cursor.execute("PRAGMA table_info(trackables)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "code" not in columns:
        cursor.execute("""
        DROP TABLE IF EXISTS trackables;
        """)
        cursor.execute("""
        CREATE TABLE trackables (
            user_id INTEGER NOT NULL,
            gc_username TEXT NOT NULL,
            uploaded_time TIMESTAMP CURRENT_TIMESTAMP,
            tb_code TEXT NOT NULL,
            code TEXT PRIMARY_KEY NOT NULL
        );
        """)
    
    for column in expected_columns:
        if column not in columns:
            if column == "user_id":
                cursor.execute("""ALTER TABLE trackables ADD COLUMN user_id INTEGER NOT NULL""")
            elif column == "username":
                cursor.execute("""ALTER TABLE trackables ADD COLUMN gc_username TEXT NOT NULL""")
            elif column == "code":
                cursor.execute("""ALTER TABLE trackables ADD COLUMN code TEXT PRIMARY_KEY NOT NULL""")
            elif column == "uploaded_time":
                cursor.execute("""ALTER TABLE trackables ADD COLUMN uploaded_time TIMESTAMP CURRENT_TIMESTAMP""")
            elif column == "tb_code":
                cursor.execute("""ALTER TABLE trackables ADD COLUMN tb_code TEXT NOT NULL""")

    conn.commit()
    conn.close()
    
async def get_message_link(bot, guild_id: int, message_id: int) -> str:
    """
    Fetch the link of a message using its ID by searching all channels in a guild.

    :param bot: The bot instance.
    :param guild_id: The ID of the guild where the message is located.
    :param message_id: The ID of the message to find.
    :return: A link to the message if found.
    """
    guild = bot.get_guild(guild_id)
    if not guild:
        raise ValueError("Guild not found.")

    for channel in guild.text_channels:
        try:
            message = await channel.fetch_message(message_id)
            return f"https://discord.com/channels/{guild.id}/{channel.id}/{message.id}"
        except discord.NotFound:
            continue  # Message not found in this channel
        except discord.Forbidden:
            continue  # Bot lacks permissions for this channel

    raise ValueError("Message not found in any accessible channels.")
    
# SYNC    
@bot.hybrid_command()
@is_dev()
async def sync(ctx):
    """Admin / Dev Only - Syncs the Bot's app commands."""
    try:
        if ctx.interaction: 
            await ctx.interaction.response.defer() 
        
        await bot.tree.sync()
        
        message = await ctx.reply("Synced!", mention_author=False)
        
        await asyncio.sleep(5)
        if message:
            await message.delete()
        else:
            return
    except commands.CheckFailure:
        pass
    
# CLEAR CMD  
@bot.hybrid_command()
@is_dev()
async def clear_cmds(ctx):
    """Admin / Dev Only - Clears the Bot's app commands."""
    try:
        if ctx.interaction: 
            await ctx.interaction.response.defer() 
        
        bot.tree.clear_commands(guild=None)
        
        message = await ctx.reply("Commands Cleared!", mention_author=False)
        
        await asyncio.sleep(5)
        if message:
            await message.delete()
        else:
            return
    except commands.CheckFailure:
        pass
    
class Message(commands.Cog):
    DELETE_TIME_DELAY = 5
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

# SAY
    @app_commands.command()
    @is_perm_mod()
    @app_commands.describe(
    saying="What you want me to say",
    channel="Please ignore this"
    )
    async def say(self, interaction: discord.Interaction, saying: str, channel: discord.TextChannel = None):
        """Says what you wanted where you wanted."""
        try:
            speak_channel = channel or interaction.channel
            if not is_perm_mod(interaction.user):
                await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to make me say `{saying}` in {speak_channel} ({interaction.channel.name}) but didn't have permissions.")
            else:
                if "@everyone" not in saying or "@here" not in saying:
                    try:
                        sent_message = await speak_channel.send(saying)
                        await log_message(interaction.guild, bot,
                            f"[I spoke in this channel](<{sent_message.jump_url}>) at {interaction.user.mention} ({interaction.user.name})'s request, saying: `{saying}`"
                        )
                        await interaction.response.send_message(
                            f"Message sent.", ephemeral=True
                        )
                    except discord.Forbidden:
                        no_chan = f"<#{speak_channel.id}>"
                        await log_message(interaction.guild, bot, interaction.command.name, f"I do not have permissions to speak in {no_chan}.")
                        await interaction.response.send_message(
                            f"I do not have permission to send messages in {no_chan}. Please ask an Administrator to check the logs.",
                            ephemeral=True,
                        )
                    except Exception as e:
                        await log_error(interaction.guild, bot, interaction.command.name,
                            f"User: {interaction.user.mention} ({interaction.user.name}) in <#{interaction.channel.id}> ({interaction.channel.name}) saying `{saying}`. Error: \n```\n{str(e)}\n```"
                        )
                        await interaction.response.send_message(
                            "Unknown error speaking. The Dev has been notified.",
                            ephemeral=True,
                        )
                        await log_message(interaction.guild, bot, interaction.command.name, f"An unknown error occured while {interaction.user.mention} ({interaction.user.name}) was speaking. The Dev has been notified.")
                elif ("@everyone" in saying and "@here" in saying) and is_moderator():
                    try:
                        sent_message = await speak_channel.send(saying)
                        await log_message(interaction.guild, bot, interaction.command.name,  
                            f"[I spoke in this channel](<{sent_message.jump_url}>) at {interaction.user.mention}'s ({interaction.user.name}) request, saying: `{saying}`"
                        )
                        await interaction.response.send_message(
                            f"Message sent.", ephemeral=True
                        )
                    except discord.Forbidden:
                        no_chan = f"<#{speak_channel.id}>"
                        await log_message(interaction.guild, bot, interaction.command.name, f"User: {interaction.user.mention} ({interaction.user.name}) | Please give me permission to send messages in {no_chan}.")
                        await interaction.response.send_message(
                            f"I do not have permission to send messages in {no_chan}. Please ask an Administrator to check the logs.",
                            ephemeral=True,
                        )
                    except Exception as e:
                        await log_error(interaction.guild, bot, interaction.command.name, 
                            f"User: {interaction.user.mention} ({interaction.user.name}) ({interaction.user.name}) in <#{interaction.channel.id}> ({interaction.channel.name}) saying `{saying}`. Error: \n```\n{str(e)}\n```"
                        )
                        await log_message(interaction.guild, bot, interaction.command.name, f"An error occured while {interaction.user.mention} ({interaction.user.name}) was speaking. The Dev has been notified.")
                        await interaction.response.send_message(
                            "An unknown error occured. The Dev has been notified.",
                            ephemeral=True,
                        )
                else:
                    await interaction.response.send_message(f"Please do NOT put everyone or here pings in your message.", ephemeral=True)
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to send a message which contains an everyone or here ping: ```{saying}```")
        
        except commands.CheckFailure:
            pass

# REPLY
    @app_commands.command()
    @is_perm_mod()
    @app_commands.describe(
    message_id="The message ID I will reply to",
    message="What I will reply with"
    )
    async def reply(self, interaction: discord.Interaction, message_id: str, message: str):
        """Replies to a specific message."""
        try:
            await interaction.response.defer(ephemeral=True)
            if not is_perm_mod(interaction.user):
                link = await get_message_link(interaction.client, interaction.guild.id, message_id)
                await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to make me reply to [this message](<{link}>) in <#{interaction.channel.id}>, saying `{message}` but had no permissions.")
            else:
                try:
                    target_message = await interaction.channel.fetch_message(int(message_id))
                    reply_content = message
                    await target_message.reply(reply_content)
                    link = await get_message_link(interaction.client, interaction.guild.id, message_id)
                    await log_message(interaction.guild, bot, f"I replied to [this message](<{link}>) in <#{interaction.channel.id}> ({interaction.channel.name}) at {interaction.user.mention} ({interaction.user.name})'s ({interaction.user.name}) request, saying: `{message}`.")
                    await interaction.followup.send("I replied successfully.", ephemeral=True)
                except discord.NotFound:
                    await interaction.followup.send("The specified message was not found.", ephemeral=True)
                except discord.Forbidden:
                    await log_message(interaction.guild, bot, interaction.command.name, f"User: {interaction.user.mention} ({interaction.user.name}) | Please give me permission to send messages in <#{interaction.channel.id}> ({interaction.channel.name}).")
                    await interaction.response.send_message(
                        f"I do not have permission to send messages in <#{interaction.channel.id}>. Please ask an Administrator to check the logs.",
                        ephemeral=True,
                    )
                except Exception as e:
                    await log_error(interaction.guild, bot, interaction.command.name, 
                        f"User: {interaction.user.mention} ({interaction.user.name}) ({interaction.user.name}) in <#{interaction.channel.id}> ({interaction.channel.name}) replying with `{message}`. Error: \n```\n{str(e)}\n```"
                    )
                    await log_message(interaction.guild, bot, interaction.command.name, f"An error occured while {interaction.user.mention} ({interaction.user.name}) was replying. The Dev has been notified.")
                    await interaction.response.send_message(
                        "An unknown error occured. The Dev has been notified.",
                        ephemeral=True,
                    )
        except commands.CheckFailure:
            pass

# DELETE
    @app_commands.command()
    @is_perm_mod()
    @app_commands.describe(messageid="ID of the message to delete")
    async def delete(self, interaction: discord.Interaction, messageid: str):
        """Delete a specified message."""
        try:
            if not is_perm_mod(interaction.user):
                await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to make me delete [this message](<{origMessage.jump_url}>) in <#{interaction.channel.id}> ({interaction.channel.name}) but had no permissions.")
            else:
                if messageid is None or messageid == "" or not (re.search(r"^\d{18,19}$", messageid)):
                    await interaction.response.send_message("Invalid `/delete` Usage! messageID is invalid or blank!")
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to make me delete a message but left `messageID` blank or invalid.")
                origMessage = await interaction.channel.fetch_message(messageid)
                if origMessage.author != self.bot.user:
                    await interaction.response.send_message("I can only delete my own messages.", f"{origMessage.jump_url} is owned by <@{origMessage.author.id}>.")
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to make me delete {origMessage.jump_url} but that message wasn't sent by me.")
                if self.DELETE_TIME_DELAY > 0:
                    await origMessage.delete(delay=self.DELETE_TIME_DELAY)
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) made me delete my message. It read: `{origMessage.content}`.")
                    await interaction.response.send_message(f"The message will be deleted in approximately {self.DELETE_TIME_DELAY} seconds.", ephemeral=True)
                else:
                    await origMessage.delete()
                    await interaction.response.send_message(f"The message will be deleted shortly.", ephemeral=True)
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) made me delete my message in <#{origMessage.channel.id}> ({origMessage.channel.name}). It read: `{origMessage.content}`")
        except commands.CheckFailure:
            pass
            
# REACT       
    @app_commands.command(name="react", description="React to a specified message.")
    @app_commands.describe(messageid="ID of the message to react to")
    @app_commands.describe(reaction="How do you want me to react?")
    @is_perm_mod()
    async def react(self, interaction: discord.Interaction, messageid: str, reaction: str):
        try:
            if not is_perm_mod(interaction.user):
                await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to make me react to [this message](<{origMessage.jump_url}>) in <#{interaction.channel.id}> ({interaction.channel.name}) with {reaction} but had no permissions.")
            else:
                if not re.fullmatch(r"\d{18,19}", messageid):
                    await interaction.response.send_message("Invalid `/react` Usage", ephemeral=True)
                    await log_message(interaction.guild, bot, interaction.command.name, 
                        f"{interaction.user.mention} ({interaction.user.name}) tried to make me react to a message with {reaction} but provided an invalid message ID."
                    )
                    return
                try:
                    origMessage = await interaction.channel.fetch_message(int(messageid))
                except discord.NotFound:
                    await interaction.response.send_message("Message not found! Check the messageID is correct.", ephemeral=True)
                    return
                except discord.Forbidden:
                    await log_message(interaction.guild, bot, interaction.command.name, f"User: {interaction.user.mention} ({interaction.user.name}) | Please give me permission to send messages in <#{interaction.channel.id}> ({interaction.channel.name}).")
                    await interaction.response.send_message(
                        f"I do not have permission to send messages in <#{interaction.channel.id}>. Please ask an Administrator to check the logs.",
                        ephemeral=True,
                    )
                match = re.fullmatch(r"<:(\w+):(\d+)>", reaction)
                if match:
                    emoji = discord.utils.get(interaction.guild.emojis, id=int(match.group(2)))
                    if not emoji:
                        await interaction.response.send_message("I can't use that emoji!", ephemeral=True)
                        return
                else:
                    emoji = reaction 
                try:
                    await origMessage.add_reaction(emoji)
                    await interaction.response.send_message("Reacted!", ephemeral=True)
                    await log_message(interaction.guild, bot, interaction.command.name, 
                        f"{interaction.user.mention} ({interaction.user.name}) made me react to [this message](<{origMessage.jump_url}>) with {emoji}."
                    )
                except discord.HTTPException:
                    await interaction.response.send_message("Failed to react! Please try again.", ephemeral=True)
                    return   
        except commands.CheckFailure:
            pass
            
# EDIT
    @app_commands.command(name="edit", description="Edit a specified message.")
    @is_perm_mod()
    @app_commands.describe(messageid="ID of the message to delete")
    @app_commands.describe(newmessage="New message content")
    async def edit(self, interaction: discord.Interaction, messageid: str, newmessage: str):
        try:
            if not is_perm_mod(interaction.user):
                await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to make me edit [this message](<{origMessage.jump_url}>) in <#{interaction.channel.id}> ({interaction.channel.name}) to say {newmessage} but had no permissions.")
            else:
                if messageid is None or messageid == "" or not (re.search(r"^\d{18,19}$", messageid)):
                    await interaction.response.send_message("Invalid `/edit` Usage! messageID is invalid or blank.")
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to make me edit a message but left `messageID` blank or invalid.")
                    return
                origMessage = await interaction.channel.fetch_message(messageid)
                if origMessage.author != self.bot.user:
                    await interaction.response.send_message(f"I can only edit my own messages. {origMessage.jump_url} is owned by <@{origMessage.author.id}>.")
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to make me edit [a message](<{origMessage.jump_url}>) which I don't own.")
                    return
                await origMessage.edit(content=newmessage)
                await interaction.response.send_message("I edited the message!", ephemeral=True)
                await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) made me edit [this message](<{origMessage.jump_url}>). Before: `{origMessage.content}` After: `{newmessage}`.")
        except commands.CheckFailure:
            pass

class TBDatabase(app_commands.Group):
    """Commands for the public TB database."""
    
# TB HELP
    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Shows all of the public TB database commands."""
        embed = discord.Embed(title="Public TB Database",
                            colour=0xad7e66)

        embed.add_field(name="Everyone:",
                        value="/tb add <code> - Adds a TB to the public database.\n⮡   You MUST own the TB to add it. If you do not own it, but have permission to share it, please contact a Mod to have it added.\n\n/tb bulkadd - Bulk adds TBs to the public database as long as they are separated.\n⮡   You MUST own the TBs to add them. They MUST be separated via eg. space, comma etc.\n\n/tb remove <code> - Removes a TB from the public database.\n⮡   You MUST own the TB to remove it. If you do not own it, but need it removed / have a complaint, please contact a Mod to have it removed.\n\n/tb view - Shows the public TB database.\n⮡   Shows 5 codes in one embed. You must use the pagination (reactions) to move to the next page, if there is one.\n\n/tb bulkview - Sends all codes in the public TB database to your DMs.\n⮡   DMs you ALL codes in one message. They are separated by commas, so they are suitable for [logthemall](<https://www.logthemall.org/>) or the [PGC trackable tool](<https://project-gc.com/Tools/DiscoverTrackables>).",
                        inline=False)
        embed.add_field(name="Staff Only:",
                        value="/tb forceadd <code> - Smash crash forces a TB into the public database.\n⮡   Meant for staff to be able to add codes which users do not own but have permission to share.\n\n/tb forceremove <code> - Smash crash forces a TB out of the public database.\n⮡   Meant for staff to be able to remove codes which no longer exist, or violate the rules or were added without permission etc.\n\n/tb purge <name> - Smash crash forces all TBs owned by a specified user out of the public database.\n⮡   Meant for staff to be able to bulk remove codes faster than the user can do them one by one, in case they were accidentally added etc.",
                        inline=False)
        
        await interaction.response.send_message(embed=embed)
    
# TB ADD
    @app_commands.command()
    @app_commands.describe(code="The PRIVATE code of the TB you want to add")
    async def add(self, interaction: discord.Interaction, code: str):
        """Adds a TB to the public database."""
        if code.lower().startswith("tb"):
            await interaction.response.send_message(f"Please try again with the private code (this can be found on the TB itself) as the code, instead of `{code}`. If you believe this to be an error, please contact staff.")
            await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to use `tb add` but entered the public code instead of the private one: `{code}`.")
        else:
            headers = {
                "User-Agent": "GCDiscordBot/1.0 (+https://discord.gg/EKn8z23KkC)"
            }

            url = f"https://www.geocaching.com/track/details.aspx?tracker={code}"

            try:
                response = requests.get(url, headers=headers, timeout=(5, 10))
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                page_text = soup.get_text()
                match = re.search(r"Use\s+(\S+).*to reference this item", page_text)
                if match:
                    tb_code_line = match.group(0)
                    cleaned_text = re.sub(r"\b(?:Use|to|reference|this|item)\b", "", tb_code_line, flags=re.IGNORECASE).strip()
                    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
                else:
                    await interaction.response.send_message(f"The TB code you entered (`{code}`) was not valid. Please try again with a valid code.")
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) used `tb add` but the TB code was not valid.")
                    cleaned_text = "Not Found"

                owner_label = soup.find("dt", string=lambda text: text and "Owner:" in text)
                if owner_label:
                    owner_name_tag = owner_label.find_next_sibling("dd")
                    if owner_name_tag:
                        owner_name = owner_name_tag.get_text(strip=True)

                        cleaned_owner_name = re.sub(r"\s*Send\sMessage\sto\sOwner.*", "", owner_name)


                        cursor1.execute("SELECT * FROM trackables WHERE code = ?", (code,))
                        existing_entry = cursor1.fetchone()
                        if existing_entry:
                            await interaction.response.send_message(f"This TB code (`{code}`) is already in the database.")
                        else:
                            user_id = interaction.user.id
                            cursor1.execute("""
                                INSERT INTO trackables (code, gc_username, uploaded_time, user_id, tb_code) 
                                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
                            """, (code, cleaned_owner_name, user_id, cleaned_text))
                            conn1.commit()
                            await interaction.response.send_message(f"This TB (`{code}`) has been added to the public database - thanks for sharing!")
                            await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) has shared TB `{code}` and it has been added to the database!")
                    else:
                        await interaction.response.send_message("Owner name not found. Please make sure the TB is activated and try again.")
                        await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) used `tb add`, but the owner name was not found. Code: `{code}`")
                else:
                    await interaction.response.send_message("Owner label not found. Please make sure the TB is activated and try again.")
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) used `tb add`, but the owner label was not found. Code: `{code}`")

            except Exception as e:
                await interaction.response.send_message(f"An unknown error occured whilst processing code `{code}`. The Dev has been notified.")
                await log_error(interaction.guild, bot, interaction.command.name, 
                    f"User: {interaction.user.mention} ({interaction.user.name}) adding TB `{code}` to the database. Error: \n```\n{str(e)}\n```"
                )
                await log_message(interaction.guild, bot, interaction.command.name, f"An error occured while {interaction.user.mention} ({interaction.user.name}) was adding TB `{code}` to the database. The Dev has been notified.")
                print(e)
        
    @add.error
    async def add_error(self, interaction: discord.Interaction, error, code):
        """Handles errors for the `add` command."""
        if isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message("Error: Missing required argument `code`. Usage: `/tb add <code>`")
        elif isinstance(error, commands.CommandInvokeError):
            await interaction.response.send_message(f"An unknown error occurred while executing the command. The Dev has been notified.")
            await log_error(interaction.guild, bot, interaction.command.name, 
                    f"User: {interaction.user.mention} ({interaction.user.name}) adding a TB (`{code}`) to the database. Error: \n```\n{str(error)}\n```"
                )
            print({str(error)})
        else:
            await interaction.response.send_message(f"An unknown error occurred. The Dev has been notified.")
            await log_error(interaction.guild, bot, interaction.command.name, 
                    f"User: {interaction.user.mention} ({interaction.user.name}) adding a TB (`{code}`) to the database. Error: \n```\n{str(error)}\n```"
                )
            print({str(error)})
    
# TB BULKADD        
    @app_commands.command()
    @app_commands.describe(codes="The PRIVATE codes of the TBs you want to add, separated by commas, spaces, colons, etc.")
    async def bulkadd(self, interaction: discord.Interaction, codes: str):
        """Adds multiple TBs to the public database."""
        tb_codes = re.split(r"[,\s:]+", codes.strip())

        await interaction.response.send_message(f"Processing {len(tb_codes)} TB code(s)... this may take a while.", ephemeral=True)

        successful_codes = []
        failed_codes = []

        for code in tb_codes:
            if code.lower().startswith("tb"):
                await log_message(interaction.guild, bot, interaction.command.name,
                    f"{interaction.user.mention} ({interaction.user.name}) tried to use `bulkadd` but entered the public code instead of the private one: `{code}`."
                )
                failed_codes.append(code)
                continue

            headers = {
                "User-Agent": "GCDiscordBot/1.0 (+https://discord.gg/EKn8z23KkC)"
            }
            url = f"https://www.geocaching.com/track/details.aspx?tracker={code}"

            try:
                response = requests.get(url, headers=headers, timeout=(5, 10))
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                page_text = soup.get_text()
                match = re.search(r"Use\s+(\S+).*to reference this item", page_text)
                if match:
                    tb_code_line = match.group(0)
                    cleaned_text = re.sub(r"\b(?:Use|to|reference|this|item)\b", "", tb_code_line, flags=re.IGNORECASE).strip()
                    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
                else:
                    await log_message(interaction.guild, bot, interaction.command.name,
                        f"{interaction.user.mention} ({interaction.user.name}) used `bulkadd` but the TB code line was not found for code: `{code}`."
                    )
                    failed_codes.append(code)
                    continue 

                owner_label = soup.find("dt", string=lambda text: text and "Owner:" in text)
                if owner_label:
                    owner_name_tag = owner_label.find_next_sibling("dd")
                    if owner_name_tag:
                        owner_name = owner_name_tag.get_text(strip=True)
                        cleaned_owner_name = re.sub(r"\s*Send\sMessage\sto\sOwner.*", "", owner_name)


                        cursor1.execute("SELECT * FROM trackables WHERE code = ?", (code,))
                        existing_entry = cursor1.fetchone()
                        if existing_entry:
                            await log_message(interaction.guild, bot, interaction.command.name,
                                f"{interaction.user.mention} ({interaction.user.name}) attempted to bulkadd TB `{code}`, but it already exists in the database."
                            )
                            failed_codes.append(code)
                        else:
                            user_id = interaction.user.id
                            cursor1.execute("""
                                INSERT INTO trackables (code, gc_username, uploaded_time, user_id, tb_code) 
                                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
                            """, (code, cleaned_owner_name, user_id, cleaned_text))
                            conn1.commit()
                            await log_message(interaction.guild, bot, interaction.command.name,
                                f"{interaction.user.mention} ({interaction.user.name}) has shared TB `{code}` and it has been added to the database!"
                            )
                            successful_codes.append(code)
                    else:
                        await log_message(interaction.guild, bot, interaction.command.name,
                            f"{interaction.user.mention} ({interaction.user.name}) used `bulkadd`, but the owner name was not found. Code: `{code}`."
                        )
                        failed_codes.append(code)
                else:
                    await log_message(interaction.guild, bot, interaction.command.name,
                        f"{interaction.user.mention} ({interaction.user.name}) used `bulkadd`, but the owner label was not found. Code: `{code}`."
                    )
                    failed_codes.append(code)

            except Exception as e:
                await log_error(interaction.guild, bot, interaction.command.name,
                    f"{interaction.user.mention} ({interaction.user.name}) tried to bulkadd TB `{code}`: {e}"
                )
                failed_codes.append(code)

        successful_str = ", ".join(successful_codes) if successful_codes else "None"
        failed_str = ", ".join(failed_codes) if failed_codes else "None"

        await interaction.followup.send(
            f"Finished processing TB codes!\n"
            f"Successfully added: {len(successful_codes)} ({successful_str})\n"
            f"Failed to add: {len(failed_codes)} ({failed_str})\n"
            f"Thank you for your contribution towards the trackable database!",
            ephemeral=True
        )
            
    @bulkadd.error
    async def bulkadd_error(self, interaction: discord.Interaction, error, code):
        """Handles errors for the `bulkadd` command."""
        if isinstance(error, commands.MissingRequiredArgument):
            await interaction.response.send_message("Error: Missing required argument `codes`. Usage: `/tb bulkadd <codes>`")
        elif isinstance(error, commands.CommandInvokeError):
            await interaction.response.send_message(f"An unknown error occurred while executing the command. The Dev has been notified.")
            await log_error(interaction.guild, bot, interaction.command.name, 
                    f"User: {interaction.user.mention} ({interaction.user.name}) bulkadding a TB (`{code}`) to the database. Error: \n```\n{str(error)}\n```"
                )
        else:
            await interaction.response.send_message(f"An unknown error occurred. The Dev has been notified.")
            await log_error(interaction.guild, bot, interaction.command.name, 
                    f"User: {interaction.user.mention} ({interaction.user.name}) bulkadding a TB (`{code}`) to the database. Error: \n```\n{str(error)}\n```"
                )
      
# TB FORCEADD      
    @app_commands.command()
    @is_dev()
    @app_commands.describe(code="The PRIVATE code of the TB you want to add")
    async def forceadd(self, interaction: discord.Interaction, code: str):
        """Smash crash forces a TB into the public database."""
        if code.lower().startswith("tb"):
            await interaction.response.send_message(f"Please try again with the private code (this can be found on the TB itself) as the code, instead of `{code}`. If you believe this to be an error, please contact the Dev.")
            await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to use `tb forceadd` but entered the public code instead of the private one: `{code}`.")
        else:
            headers = {
                "User-Agent": "GCDiscordBot/1.0 (+https://discord.gg/EKn8z23KkC)"
            }

            url = f"https://www.geocaching.com/track/details.aspx?tracker={code}"

            try:
                response = requests.get(url, headers=headers, timeout=(5, 10))
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                page_text = soup.get_text()
                match = re.search(r"Use\s+(\S+).*to reference this item", page_text)
                if match:
                    tb_code_line = match.group(0)
                    cleaned_text = re.sub(r"\b(?:Use|to|reference|this|item)\b", "", tb_code_line, flags=re.IGNORECASE).strip()
                    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
                else:
                    await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) used `tb forceadd` but the public TB code was not found.")
                    cleaned_text = "Not Found"

                owner_label = soup.find("dt", string=lambda text: text and "Owner:" in text)
                if owner_label:
                    owner_name_tag = owner_label.find_next_sibling("dd")
                    if owner_name_tag:
                        owner_name = owner_name_tag.get_text(strip=True)

                        cleaned_owner_name = re.sub(r"\s*Send\sMessage\sto\sOwner.*", "", owner_name)

                        if cleaned_owner_name:
                            cursor1.execute("SELECT * FROM trackables WHERE code = ?", (code,))
                            existing_entry = cursor1.fetchone()
                            if existing_entry:
                                await interaction.response.send_message(f"This TB code `{code}` is already in the database.")
                            else:
                                user_id = interaction.user.id
                                cursor1.execute("""
                                    INSERT INTO trackables (code, gc_username, uploaded_time, user_id, tb_code) 
                                    VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
                                """, (code, cleaned_owner_name, user_id, cleaned_text))
                                conn1.commit()
                                await interaction.response.send_message(f"This TB has been forcibly added to the public database - thanks for sharing!")
                                await log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) has shared TB `{code}` and it has been forcibly added to the database!")
                        else:
                            await interaction.response.send_message(f"It appears that the owner name does not exist. The Dev has been notified.")
                            await log_error(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) was using `tb forceadd`: It appears that the `cleaned_owner_name` variable does not exist.")
                    else:
                        await interaction.response.send_message("The owner name not found. The Dev has been notified.")
                        await log_error(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) used `tb forceadd`, but the owner name was not found in the expected <dd> tag. Code: {code}")
                else:
                    await interaction.response.send_message("The owner label was not found. The Dev has been notified.")
                    await log_error(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) used `tb forceadd`, but the owner label was not found in the expected <dt> tag. Code: {code}")

            except Exception as e:
                await log_error(interaction.guild, bot, interaction.command.name,
                    f"{interaction.user.mention} ({interaction.user.name}) tried to forceadd TB `{code}`: {e}"
                )
            
    @forceadd.error
    async def forceadd_error(self, interaction: discord.Interaction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            code = interaction.data.get("options")[0]["value"] if interaction.data.get("options") else "Unknown"
        else:
            await interaction.response.send_message(
                "An unexpected error occurred. The Dev has been notified.", ephemeral=True
            )
            await log_error(interaction.guild, bot, interaction.command.name,
                f"{interaction.user.mention} ({interaction.user.name}) tried to forceadd TB `{code}`: {error}"
            )
            
# TB PURGE
    @app_commands.command()
    @is_dev()
    @app_commands.describe(username="The username of the owner of the TBs you want to remove")
    async def purge(self, interaction: discord.Interaction, username: str):
        """Removes all TBs associated with the given gc_username."""
        try:
            cursor1.execute("SELECT COUNT(*) FROM trackables WHERE gc_username = ?", (username,))
            count = cursor1.fetchone()[0]

            if count > 0:
                cursor1.execute("DELETE FROM trackables WHERE gc_username = ?", (username,))
                conn1.commit()

                await interaction.response.send_message(
                    f"Successfully purged {count} TB(s) associated with the username `{username}`."
                )
                await master_log_message(bot, interaction.command.name,
                    f"{interaction.user.mention} ({interaction.user.name}) purged {count} TB(s) associated with the username `{username}`."
                )
            else:
                await interaction.response.send_message(
                    f"No TBs were found associated with the username `{username}`."
                )
                await master_log_message(bot, interaction.command.name,
                    f"{interaction.user.mention} ({interaction.user.name}) attempted to purge TBs for `{username}`, but none were found."
                )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while attempting to purge TBs. The Dev has been alerted."
            )
            await log_error(interaction.guild, bot, interaction.command.name,
                f"{interaction.user.mention} ({interaction.user.name}) tried to purge TBs for `{username}`. Error: `{e}`"
            )
            
    @purge.error
    async def purge_error(self, interaction: discord.Interaction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            username = interaction.data.get("options")[0]["value"] if interaction.data.get("options") else "Unknown"
        else:
            await interaction.response.send_message(
                "An unexpected error occurred. The Dev has been notified.", ephemeral=True
            )
            await log_error(interaction.guild, bot, interaction.command.name,
                            f"{interaction.user.mention} ({interaction.user.name}) tried to purge TBs for `{username}`. Error: `{error}`"
            )
      
# TB REMOVE      
    @app_commands.command()
    @app_commands.describe(code="The PRIVATE code of the TB you want to remove")
    async def remove(self, interaction: discord.Interaction, code: str):
        """Removes a TB from the public database."""
        try:
            cursor.execute("SELECT gc_username FROM trackables WHERE code = ?", (code,))
            existing_entry = cursor.fetchone()

            if existing_entry:
                gc_username = existing_entry[0]
                if gc_username == interaction.user.display_name:
                    cursor1.execute("DELETE FROM trackables WHERE code = ?", (code,))
                    conn1.commit()
                    await interaction.response.send_message(f"The TB with code `{code}` has been removed from the database.")
                    await bot.get_channel(1322311043493531669).send(f"{interaction.user.mention} ({interaction.user.name}) removed TB `{code}` from the database.")
                else:
                    await interaction.response.send_message(f"You do not own this TB, so cannot delete it. If you believe this is a mistake, or have a reason for this to be deleted, please contact an Administrator.")
                    await bot.get_channel(1322311043493531669).send(f"{interaction.user.mention} ({interaction.user.name}) tried to remove TB {code} from the database but does not own it.")
            else:
                await interaction.response.send_message(f"No TB with the code `{code}` was found in the database.")
                await bot.get_channel(1322311043493531669).send(f"{interaction.user.mention} ({interaction.user.name}) tried to remove TB `{code}` from the database but it wasnt there.")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while trying to remove the TB. Please ask an Administrator to check the logs.")
            await bot.get_channel(1322311043493531669).send(f"An error occurred while {interaction.user.mention} ({interaction.user.name}) tried to remove TB `{code}`: {e}")
            
# TB FORCEREMOVE
    @app_commands.command()
    @is_dev()
    @app_commands.describe(code="The PRIVATE code of the TB you want to remove")
    async def forceremove(self, interaction: discord.Interaction, code: str):
        """Smash crash forces removal a TB from the public database."""
        try:
            cursor1.execute("SELECT * FROM trackables WHERE code = ?", (code,))
            existing_entry = cursor1.fetchone()

            if existing_entry:
                cursor1.execute("DELETE FROM trackables WHERE code = ?", (code,))
                conn1.commit()
                await interaction.response.send_message(f"The TB with code `{code}` has been forcibly removed from the database.")
                await bot.get_channel(1322311043493531669).send(f"{interaction.user.mention} ({interaction.user.name}) forcibly removed TB `{code}` from the database.")
            else:
                await interaction.response.send_message(f"No TB with the code `{code}` was found in the database.")
                await bot.get_channel(1322311043493531669).send(f"{interaction.user.mention} ({interaction.user.name}) tried to forcibly remove TB `{code}` from the database but it wasn't there.")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while trying to remove the TB. Please ask an Administrator to check the logs.")
            await bot.get_channel(1322311043493531669).send(f"An error occurred while {interaction.user.mention} ({interaction.user.name}) tried to forcibly remove TB `{code}`: {e}")
            
    @forceremove.error
    async def forceremove_error(self, interaction: discord.Interaction, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            code = interaction.data.get("options")[0]["value"] if interaction.data.get("options") else "Unknown"
            await interaction.response.send_message(
                "You do not have the required permissions to use this command.", ephemeral=True
            )
            await bot.get_channel(1322311043493531669).send(f"{interaction.user.mention} ({interaction.user.name}) tried to forcibly remove a TB ({code}) but didn't have permissions.")
        else:
            await interaction.response.send_message(
                "An unexpected error occurred. Please contact an administrator.", ephemeral=True
            )
            
# TB VIEW
    @app_commands.command()
    async def view(self, interaction: discord.Interaction):
        """Shows the public TB database."""
        cursor1.execute("SELECT * FROM trackables")
        trackables = cursor1.fetchall()
        
        items_per_page = 5
        pages = [trackables[i:i + items_per_page] for i in range(0, len(trackables), items_per_page)]
        
        page_number = 0
        embed = discord.Embed(title="Public TB Database", colour=0xad7e66)
        
        for entry in pages[page_number]:
            tb_code = entry[3]  
            code = entry[4]   
            cleaned_owner_name = entry[1] 
            added_at_time = entry[2]  
            
            added_at_dt = datetime.strptime(added_at_time, "%Y-%m-%d %H:%M:%S")
            added_at_unix = int(added_at_dt.timestamp())

            discord_timestamp = f"<t:{added_at_unix}>"
            
            embed.add_field(
                name=f"{tb_code} - {cleaned_owner_name}",
                value=f"**CODE**: {code}\n**OWNER**: {cleaned_owner_name}\n**ADDED**: {discord_timestamp}",
                inline=False
            )

        message = await interaction.response.send_message(embed=embed)

        if len(pages) > 1: 
            await message.add_reaction("⏮️") 
            await message.add_reaction("◀️")  
            await message.add_reaction("▶️") 
            await message.add_reaction("⏭️") 

        def check(reaction, user):
            return user == interaction.user and reaction.message.id == message.id and str(reaction.emoji) in ["⏮️", "◀️", "▶️", "⏭️"]

        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)

                await message.remove_reaction(reaction, user)

                if reaction.emoji == "⏮️":  # First page
                    page_number = 0
                elif reaction.emoji == "◀️":  # Previous page
                    if page_number > 0:
                        page_number -= 1
                elif reaction.emoji == "▶️":  # Next page
                    if page_number < len(pages) - 1:
                        page_number += 1
                elif reaction.emoji == "⏭️":  # Last page
                    page_number = len(pages) - 1

                embed = discord.Embed(title="Public TB Database", colour=0xad7e66)
                for entry in pages[page_number]:
                    code = entry[0]
                    cleaned_owner_name = entry[1]
                    added_at_time = entry[2]  
                    
                    added_at_dt = datetime.strptime(added_at_time, "%Y-%m-%d %H:%M:%S")
                    added_at_unix = int(added_at_dt.timestamp())

                    discord_timestamp = f"<t:{added_at_unix}>"
                    embed.add_field(
                        name=f"{tb_code} - {cleaned_owner_name}",
                        value=f"**CODE**: {code}\n**OWNER**: {cleaned_owner_name}\n**ADDED**: {discord_timestamp}",
                        inline=False
                    )

                await message.edit(embed=embed)

            except asyncio.TimeoutError:
                await message.clear_reactions()
                break
    
# TB BULKVIEW
    @app_commands.command()
    async def bulkview(self, interaction: discord.Interaction):
        """Sends all codes in the public TB database to your DMs."""
        try:
            cursor1.execute("SELECT code FROM trackables")
            trackables = cursor1.fetchall()

            if not trackables:
                await interaction.response.send_message("The database is, for some reason, empty.", ephemeral=True)
                return

            codes = ", ".join([entry[0] for entry in trackables])

            try:
                await interaction.user.send(codes)
                await bot.get_channel(1322311043493531669).send(f"{interaction.user.mention} ({interaction.user.name}) used /tb bulkview successfully")
                await interaction.response.send_message("The TB codes have been sent to your DMs.", ephemeral=True)
            except discord.Forbidden:
                await bot.get_channel(1322311043493531669).send(f"{interaction.user.mention} ({interaction.user.name}) used /tb bulkview but had their DMs disabled.")
                await interaction.response.send_message(
                    "I couldn't send you a DM. Please make sure your DMs are open and try again.",
                    ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while retrieving the TB codes. Please ask an Administrator to check the logs.",
                ephemeral=True
            )
            await bot.get_channel(1322311043493531669).send(
                f"An error occurred while {interaction.user.mention} ({interaction.user.name}) used `bulkview`: {e}"
            )
    
tb_commands = TBDatabase(name="tb", description="Public TB Database commands.")
bot.tree.add_command(tb_commands)
    
class Geocaching(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
    
# FTF
    @app_commands.command()
    async def ftf(self, interaction: discord.Interaction):
        """Shows how to get your FTFs recognised on PGC."""
        embed = discord.Embed(title="How to get your FTFs recognised on /statbar (Project-GC)",
                      description="There are multiple ways for Project-GC to detect your FTFs. Either you tag your logs with one of these tags: `{*FTF*}`, `{FTF}`, or `[FTF]`. Alternatively you can add an FTF bookmark list under Settings (<https://project-gc.com/User/Settings/>) that will be checked once per day. Please understand that FTF isn't anything offical and not everyone tags their FTFs. Therefore this list won't be 100% accurate.",
                      colour=0xad7e66)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
# STATBAR
    @app_commands.command()
    @app_commands.describe(
    user="The user the statbar is for (Default = You)",
    labcaches="Whether labcaches are included in your total finds (Default = True)"
    )
    async def statbar(self, interaction: discord.Interaction, user: discord.Member = None, labcaches: bool = None):
        """Sends a statbar image."""
        if user == None:
            user = interaction.user
        now = datetime.now()
        intYear = now.year
        intMonth = now.month
        intDay = now.day
        quotetimeusa = f"{intYear}/{intMonth:02d}/{intDay:02d}"
        if labcaches == False:
            await interaction.response.send_message(f"https://cdn2.project-gc.com/statbar.php?quote=discord.gg/EKn8z23KkC+-+{quotetimeusa}&user={user.display_name}")
        else:
            await interaction.response.send_message(f"https://cdn2.project-gc.com/statbar.php?quote=discord.gg/EKn8z23KkC+-+{quotetimeusa}&includeLabcaches&user={user.display_name}")
        
# BADGEBAR
    @app_commands.command()
    @app_commands.describe(
    user="The user the badgebar is for (Default = You)",
    )
    async def badgebar(self, interaction: discord.Interaction, user: discord.Member = None):
        """Sends a badgebar image."""
        if user == None:
            user = interaction.user
        await interaction.response.send_message(f"https://cdn2.project-gc.com/BadgeBar/{user.display_name}.png")
    
# BADGEINFO
class BadgeInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

        self.badge_embed = discord.Embed(title="What do the badges mean?",
                      description="Badges in the BadgeGen system have eight quality levels, from Bronze to Diamond, representing the user’s achievements. After reaching Diamond, users can unlock \"loops\" (additional levels) and \"Addons\" (extra mini-badges). Addons are often challenging, rewarding experienced Geocachers with special achievements, such as completing a calendar or attending specific events. Some badges also have specific loops and addon requirements, making them harder to achieve. \n\n**Full details on each badge can be found [here](https://project-gc.com/w/BadgeGen).**",
                      colour=0xad7e66)
        self.belt_embed = discord.Embed(title="What do the belts mean?",
                      description="**The Belt system is based on points, which are awarded based on various criteria. The sum of all points determines the user's overall belt level. There are 36 possible belts.**\n\nIf the user has fewer than 30 points, they will receive the White belt.\nAt 30 points, a Yellow belt will be awarded.\nEvery ten/twelve points after that will give the user an extra stripe on their belt.\nAfter 220 points, 12 points are required per level\nAfter 4 stripes, the user will be awarded a new colour belt.\nWith the exception of the black belt.\nAt 400 points, the Golden Black Belt (the highest ranking) is awarded.\n\n**Points are awarded based on the following conditions**:\n1 point per 100 caches found.\n2 points per event hosted, maximum of 30 points.\n0.5 points per difficulty/terrain combination found in excess of 40 combinations.\n10 points for completing the Difficulty/Terrain matrix.\n20 points for either finding caches in 15 distinct states or 5 distinct countries. 40 points are not awarded if both conditions are satisfied.\n10 points per 50 caches found on day with most finds, maximum of 40 points.\n0.5 points per 7 consecutive days with finds in largest streak. 10 point bonus at 366 days.\n0.1 points per favorite point on owned caches.\n2 points per distinct cache type on day with most distinct types found.\n2 points per distinct cache type hidden.\n2 points per distinct cache size hidden.\n0.5 points per FTF, maximum of 30 points.\n1 point per 5/5 Difficulty/Terrain cache found, maximum 5 points.\n1 point per gemstone badge (excluding country badges). [1]\n2 points for every year since the user's first cache find.\n0.08 points per calendar day cached on. No points awarded if distinct days is less than 100. The year is irrelevant.\n0.05 points per Trackable moved/discovered (maximum 25 points).\n0.1 points per photo uploaded to found logs (maximum 25 points).\n\n**For more info, [click here](<https://project-gc.com/w/BadgeGen_Belts>).**",
                      colour=0xad7e66)

    @discord.ui.button(label="Badge", style=discord.ButtonStyle.primary)
    async def badge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the Badge button click."""
        await interaction.response.edit_message(embed=self.badge_embed, view=BadgeInfoView())

    @discord.ui.button(label="Belt", style=discord.ButtonStyle.success)
    async def belt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the Belt button click."""
        await interaction.response.edit_message(embed=self.belt_embed, view=BadgeInfoView())

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
    
# HELP
bot.remove_command('help') 
@bot.hybrid_command()
async def help(ctx):
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

# VERIFY
conn = sqlite3.connect("verifications.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    gc_username TEXT NOT NULL,
    message_id INTEGER
)
""")
conn.commit()

class Verification(app_commands.Group):
    """Commands for the verification system."""

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensures commands in this group only run in a specific guild."""
        if interaction.guild and interaction.guild.id == 1321978962078994495:
            return True 
        await interaction.response.send_message("This command is not available in this server.", ephemeral=True)
        return False

    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Shows all of the verification commands."""
        embed = discord.Embed(title="Verification Commands",
                            colour=0xad7e66)

        embed.add_field(name="Everyone:",
                        value="</verify verify:1327423499089874956> - Verify your Geocaching profile.\n</verify muggle:1327423499089874956> - Assign yourself the Muggle role.\n</verify bypass:1327423499089874956> - You do not want to show your nickname. Verify via this.",
                        inline=False)
        embed.add_field(name="Staff Only:",
                        value="</verify approve:1327423499089874956> - Approve a verification request.\n</verify deny:1327423499089874956> - Deny a verification request.\n</verify unverified:1327423499089874956> - Sends a list of unverified members.",
                        inline=False)
        
        await interaction.response.send_message(embed=embed)

# VERIFY VERIFY
    @app_commands.command(name="verify", description="Verify your Geocaching profile.")
    @app_commands.describe(gc_username="The username of your Geocaching account")
    async def verify(self, interaction: discord.Interaction, gc_username: str):
        if 1322037585559818313 not in [role.id for role in interaction.user.roles]:
            headers = {
                "User-Agent": "GCDiscordBot/1.0 (+https://discord.gg/EKn8z23KkC)"
            }
            url = f"https://www.geocaching.com/p/?u={gc_username}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                error_message = soup.find(string="Error 404: DNF")

                if error_message:
                    await interaction.response.send_message("The username you entered does not exist.")
                    await bot.get_channel(1322311043493531669).send(
                        f"{interaction.user.mention} ({interaction.user.name}) used /verify but the profile name they entered ({gc_username}) doesn't exist."
                    )
                else:
                    message = await bot.get_channel(1326976150014001335).send(
                        f"{interaction.user.mention} has requested verification for username: {gc_username}. Verification ID: will be provided shortly."
                    )

                    cursor.execute(
                        "INSERT INTO verifications (user_id, gc_username, message_id) VALUES (?, ?, ?)",
                        (interaction.user.id, gc_username, message.id)
                    )
                    conn.commit()

                    verification_id = cursor.lastrowid
                    await message.edit(content=f"{interaction.user.mention} has requested verification for username: {gc_username}. Verification ID: {verification_id}.")
                    await interaction.response.send_message(
                        "Your request has been submitted for review. Your verification ID is `{}`. A member of staff will review it soon.".format(verification_id),
                        ephemeral=True
                    )
            else:
                await bot.get_channel(1322311043493531669).send(
                    f"{interaction.user.mention} ({interaction.user.name}) used /verify <{gc_username}> and encountered an error: Failed to fetch the page. HTTP status code: {response.status_code}. It could mean the profile doesn't exist, or it could be something else."
                )
                await interaction.response.send_message(
                    f"The username you entered does not exist, or there was an error. Please re-verify with the correct username, or contact an Admin.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already verified. If your nickname is NOT your Geocaching username, please contact Staff.", ephemeral=True)
            await bot.get_channel(1322311043493531669).send(f"{interaction.user.mention} tried to use /verify {gc_username} but they're already verified.")

# VERIFY APPROVE
    @app_commands.command(name="approve", description="Approve a verification request.")
    @app_commands.describe(verification_id="The ID of the verification request to approve.")
    @is_moderator()
    async def approve(self, interaction: discord.Interaction, verification_id: int):
        cursor.execute("SELECT user_id, gc_username, message_id FROM verifications WHERE id = ?", (verification_id,))
        row = cursor.fetchone()

        if row:
            user_id, gc_username, message_id = row
            guild = interaction.guild
            member = guild.get_member(user_id)
            role = guild.get_role(1322037585559818313)

            if member:
                await member.add_roles(role)
                await member.edit(nick=gc_username)

                await member.send(
                    f"Congratulations, {gc_username} - You have been verified! Your nickname has been updated, and you now have access to the rest of the server."
                )

                await bot.get_channel(1322311043493531669).send(
                    f"{member.mention} has been verified by {interaction.user.mention} ({interaction.user.name}) with username {gc_username}."
                )

                try:
                    channel = bot.get_channel(1326976150014001335)
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                except Exception as e:
                    await bot.get_channel(1322311043493531669).send(f"Error deleting message: {e}")

                cursor.execute("DELETE FROM verifications WHERE id = ?", (verification_id,))
                conn.commit()
                await interaction.response.send_message(f"Verification ID {verification_id} with username {gc_username} has been approved.", ephemeral=True)
            else:
                await interaction.response.send_message("The user is no longer in the server.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid verification ID.", ephemeral=True)

# VERIFY DENY
    @app_commands.command(name="deny", description="Deny a verification request.")
    @app_commands.describe(verification_id="The ID of the verification request to deny.", reason="The reason for denial.")
    @is_moderator()
    async def deny(self, interaction: discord.Interaction, verification_id: int, reason: str):
        cursor.execute("SELECT user_id, gc_username, message_id FROM verifications WHERE id = ?", (verification_id,))
        row = cursor.fetchone()

        if row:
            user_id, gc_username, message_id = row
            member = interaction.guild.get_member(user_id)

            if member:
                await member.send(
                    f"Your verification request has been denied for the following reason:\n\n{reason}"
                )

                await bot.get_channel(1322311043493531669).send(
                    f"{member.mention}'s verification request with username {gc_username} has been denied by {interaction.user.mention} ({interaction.user.name}). Reason: {reason}"
                )

                try:
                    channel = bot.get_channel(1326976150014001335)
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                except Exception as e:
                    await bot.get_channel(1322311043493531669).send(f"Error deleting message: {e}")

                cursor.execute("DELETE FROM verifications WHERE id = ?", (verification_id,))
                conn.commit()
                await interaction.response.send_message(f"Verification ID {verification_id} has been denied.", ephemeral=True)
            else:
                await interaction.response.send_message("The user is no longer in the server.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid verification ID.", ephemeral=True)
            
# VERIFY MUGGLE
    @app_commands.command(name="muggle", description="Assign yourself the Muggle role.")
    async def muggle(self, interaction: discord.Interaction):
        if 1322037585559818313 not in [role.id for role in interaction.user.roles]:
            role = interaction.guild.get_role(1322960898725515295)
            if role:
                await interaction.user.add_roles(role)
                await interaction.response.send_message("You have been assigned the Muggle role.", ephemeral=True)
                await bot.get_channel(1322311043493531669).send(
                    f"{interaction.user.mention} has used /muggle and was assigned the Muggle role."
                )
            else:
                await interaction.response.send_message("Muggle role not found. Please contact an admin.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already verified and cannot assign yourself the Muggle role.", ephemeral=True)
            
# VERIFY BYPASS
    @bot.tree.command(name="bypass", description="You do not want to show your nickname. Verify via this.")
    async def quickverify(self, interaction: discord.Interaction):
        if 1322037585559818313 not in [role.id for role in interaction.user.roles]:
            role = interaction.guild.get_role(1322037585559818313)
            if role:
                await interaction.user.add_roles(role)
                await interaction.user.edit(nick=interaction.user.display_name)
                await interaction.response.send_message("You have been verified. We highly suggest you use a nickname to verify since otherwise you cannot use commands like /badgebar, /statbar and more.", ephemeral=True)
                await bot.get_channel(1322311043493531669).send(
                    f"{interaction.user.mention} has been verified without a username."
                )
            else:
                await interaction.response.send_message("Verification role not found. Please contact an admin.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already verified.", ephemeral=True)

# UNVERIFIED
    @app_commands.command()
    @is_moderator()
    async def unverified(self, interaction: discord.Interaction):
        """Sends a list of unverified members."""
        role_id_to_check = 1322037585559818313 
        missing_role_users = []

        for member in interaction.guild.members:
            if role_id_to_check not in [role.id for role in member.roles]: 
                missing_role_users.append(member)

        embed = discord.Embed(
            title="Unverified Users",
            colour=0xad7e66
        )
        
        for user in missing_role_users:
            embed.add_field(name=user.name, value=user.mention, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

verify_commands = Verification(name="verify", description="Verification system commands.")
bot.tree.add_command(verify_commands)

# TB / GC RECOGNITION
def get_cache_basic_info(geocache_codes=[], tb_codes=[]):
    final_message = []
    geocaching = pycaching.login(
        "cbhelectronicsofficial@gmail.com", "TrackerIsALil'Cutie"
    )
    for code in geocache_codes:
        try:
            cache = geocaching.get_cache(code)
            cache.load_quick()

            name = cache.name
            size = cache.size
            fps = cache.favorites
            difficulty = cache.difficulty
            terrain = cache.terrain
            author = cache.author
            pmo = cache.pm_only
            cache_type = cache.type
            state = cache.state

            emoji_name = f"{cache_type.name if cache_type.name != 'lost_and_found_event' else 'community_celebration'}{'-disabled' if (not state) else ''}"

            with open("name-icon.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                emoji_text = data.get(emoji_name, {}).get("emoji", None)

            final_message.append(f"""{'<:Premium:1322012392619769876>' if pmo else ''}{emoji_text} [{code}](<https://coord.info/{code}>) - {name} | {author}
:light_blue_heart: {fps} | :mag_right: D{difficulty} - T{terrain} :mountain_snow: | <:tub:1327698135710957609> {size.value.capitalize()}""")

        except Exception as e:
            final_message.append(f"<:DNF:1322013334291091589> **That Geocache doesn't exist!**")

    for trackable in tb_codes:
        try:
            tb = geocaching.get_trackable(trackable)
            tb.load()

            name = tb.name
            owner = tb.owner

            final_message.append(
                f"""<:TravelBug:1323074400613961769> [{trackable}](<https://coord.info/{trackable}>) - {name} | {owner}"""
            )

        except Exception as e:
            final_message.append(f"<:DNF:1322013334291091589> **That Trackable doesn't exist!**")

    final_message = "\n\n".join(final_message)
    return final_message

gcblacklist = ["GC", "GCHQ"]
tbblacklist = ["TB", "TBF", "TBH", "TBS"]

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    clean_content = re.sub(r'[^A-Za-z0-9\s]', '', message.content)

    matches = re.findall(r'\bGC\w*\b', clean_content, re.IGNORECASE)
    match = re.findall(r'\bTB\w*\b', clean_content, re.IGNORECASE)

    gc_codes = [item.upper() for item in matches]
    tb_codes = [item.upper() for item in match]

    if any(code in gcblacklist for code in gc_codes):
        return 
    if any(code in tbblacklist for code in tb_codes):
        return  

    if matches or match:
        finalmessage = get_cache_basic_info(gc_codes, tb_codes)
        await message.channel.send(finalmessage)
    else:
        return
    
    await bot.process_commands(message)

# FOXFIL
@bot.tree.command()
@is_perm_mod()
async def foxfil(interaction: discord.Interaction):
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
        
operators = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv
}

eightball_answers = [
    "Yes.",
    "No.",
    "Maybe.",
    "I don't know.",
    "Definitely.",
    "Absolutely not.",
    "Could be.",
    "Probably.",
    "I'm not sure."
]

funny_eightball_answers = [
    "woof.",
    "rawr.",
    "potato.",
    "uwu :3.",
    "GIB FOOD.",
    "i will send you to the basement.",
    "dinoshark has gf.",
    "D5/T5 nano on a cliff.",
    "i am superior.",
    "you know what else is massive <:devious:1341566707206197340> - Buckeye",
    ":Blobfish:",  
    "i love wet logs - said nobody ever",  
    "I dont care about answering your question, BUT do you also use multi million dollar satellites to find tupperware in the woods?",  
    "im in your walls, i know everything",  
    "free shavacado",  
    "1000 ammo can power trail",  
    "if you want a random persons license plate number contact @sharkanddino or @NightFlyer33",  
    "I dId NoT fInD tHe GeOcAcHe BuT i MaRkEd FoUnD bEcAuSe I aM lAzY",  
    "sigma"
]

class ImageSearchView(discord.ui.View):
    """View with buttons to navigate image search results."""
    def __init__(self, images, query, timeout: float = 50.0):
        super().__init__(timeout=timeout)
        self.images = images
        self.index = 0
        self.query = query
        self.msg = None
        self.update_buttons()

    async def on_timeout(self):
        """Disable all buttons when the view times out."""
        for button in self.children:
            button.disabled = True  
        if self.msg:
            await self.msg.edit(view=self)

    def update_buttons(self):
        """Update the state of navigation buttons."""
        for button in self.children:
            if button.custom_id == "first":
                button.disabled = self.index == 0
            elif button.custom_id == "previous":
                button.disabled = self.index == 0
            elif button.custom_id == "next":
                button.disabled = self.index >= len(self.images) - 1
            elif button.custom_id == "last":
                button.disabled = self.index >= len(self.images) - 1

    async def update_message(self, interaction: discord.Interaction):
        """Updates the embed with the new image result."""
        embed = discord.Embed(colour=0xad7e66)
        embed.set_footer(text=f"Image {self.index + 1} / 15 | {self.query} | Tracker",
        icon_url="https://i.imgur.com/kNe7FRh.png")
        embed.set_image(url=self.images[self.index])
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:first:1338154194640699442>", style=discord.ButtonStyle.primary, custom_id="first", disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the first image."""
        self.index = 0
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:previous:1338154278589825114>", style=discord.ButtonStyle.primary, custom_id="previous", disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the previous image."""
        if self.index > 0:
            self.index -= 1
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:next:1338154251121332246>", style=discord.ButtonStyle.primary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the next image."""
        if self.index < len(self.images) - 1:
            self.index += 1
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:last:1338154217923416105>", style=discord.ButtonStyle.primary, custom_id="last")
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the last image."""
        self.index = len(self.images) - 1
        await self.update_message(interaction)
        
    @discord.ui.button(label="🔢", style=discord.ButtonStyle.primary)
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to a specified image."""
        
        class JumpModal(discord.ui.Modal, title="Jump to Page"):
            page_input = discord.ui.TextInput(
                label="Enter a page number 1-15",
                style=discord.TextStyle.short,
                required=True,
                min_length=1,
                max_length=2,
                placeholder="1-15"
            )

            async def on_submit(modal_self, modal_interaction: discord.Interaction):
                """Handles the submission of the page number."""
                try:
                    page = int(modal_self.page_input.value)
                    if 1 <= page <= 15:
                        self.index = page - 1
                        await self.update_message(modal_interaction)
                    else:
                        await modal_interaction.response.send_message("Invalid page number! Enter 1-15.", ephemeral=True)
                except ValueError:
                    await modal_interaction.response.send_message("Please enter a valid number.", ephemeral=True)

        await interaction.response.send_modal(JumpModal())
        
gis = GoogleImagesSearch(GOOGLE_API_KEY, GOOGLE_CX_ID)
    
def google_search(query):
    service = build("customsearch", "v1", developerKey=GOOGLE_NORMAL_API_KEY)
    res = service.cse().list(q=query, cx=GOOGLE_NORMAL_SEARCH_ID).execute()
    return res.get('items', [])

class GoogleSearchView(discord.ui.View):
    def __init__(self, results, query):
        super().__init__(timeout=300)
        self.results = results
        self.query = query
        self.index = 0
        self.update_buttons()

    def update_buttons(self):
        """Update button states based on current index."""
        self.first.disabled = self.index == 0
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index == len(self.results) - 1
        self.last.disabled = self.index == len(self.results) - 1

    async def update_message(self, interaction: discord.Interaction):
        """Update the embed message and buttons."""
        result = self.results[self.index]
        embed = discord.Embed(
            title=result['title'],
            url=result['link'],
            description=result.get('snippet', ''),
            color=0xad7e66,
        )
        embed.set_footer(text=f"Result {self.index + 1} / {len(self.results)} | {self.query} | Tracker", 
                         icon_url="https://i.imgur.com/kNe7FRh.png")
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:first:1338154194640699442>", style=discord.ButtonStyle.primary, disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to first result."""
        self.index = 0
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:previous:1338154278589825114>", style=discord.ButtonStyle.primary, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous result."""
        self.index = max(0, self.index - 1)
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:next:1338154251121332246>", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next result."""
        self.index = min(len(self.results) - 1, self.index + 1)
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:last:1338154217923416105>", style=discord.ButtonStyle.primary)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to last result."""
        self.index = len(self.results) - 1
        await self.update_message(interaction)

    @discord.ui.button(label="🔢", style=discord.ButtonStyle.primary)
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Jump to a specified result."""
        class JumpModal(discord.ui.Modal, title="Jump to Page"):
            page_input = discord.ui.TextInput(
                label="Enter a page number",
                style=discord.TextStyle.short,
                required=True,
                min_length=1,
                max_length=2,
                placeholder=f"1-{len(self.results)}"
            )

            async def on_submit(modal_self, modal_interaction: discord.Interaction):
                try:
                    page = int(modal_self.page_input.value)
                    if 1 <= page <= len(self.results):
                        self.index = page - 1
                        await self.update_message(modal_interaction)
                    else:
                        await modal_interaction.response.send_message("Invalid page number!", ephemeral=True)
                except ValueError:
                    await modal_interaction.response.send_message("Please enter a valid number.", ephemeral=True)

        await interaction.response.send_modal(JumpModal())
    
class Fun(app_commands.Group):
    """Fun Commands!"""
    
# HELP
    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Shows all of the Fun commands."""
        embed = discord.Embed(title="Fun Commands",
                      colour=0xad7e66)

        embed.add_field(name="",
                value="/fun 8ball <question> <potato_mode> - Asks the magic 8ball a question\n/fun avatar <user> - Shows the avatar of a user\n/fun cat - Sends a random Cat image\n/fun coinflip - Flips a coin\n/fun define <word> - Sends the definition of a word\n/fun dog - Sends a random Dog image\n/fun google <query> - Search Google for web results\n/fun image <query> - Search Google for image results\n/fun math <expression> - Solves a math equation\n/fun roll <maxroll> - Rolls a random number\n/fun servericon - Send the server's icon\n/fun serverinfo - Shows some generic server info\n/fun userinfo <user> - Shows some generic user info\n/fun help - Shows all of the Fun commands",
                inline=False)
        embed.set_footer(text="Help | Tracker",
                         icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)
    
# ROLL
    @app_commands.command()
    @app_commands.describe(num="The maximum number you can roll.")
    async def roll(self, interaction: discord.Interaction, num: int):
        """Rolls a random number."""
        rollnum = random.randint(1, num)
        rng = discord.Embed(
            title=f"{interaction.user.mention} ({interaction.user.name}) rolled a {rollnum} (max = {num})",
            colour=0xad7e66)
        rng.set_footer(text="Roll | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=rng)
        
# COINFLIP
    @app_commands.command()
    async def coinflip(self, interaction: discord.Interaction):
        """Flips a coin."""
        await interaction.response.defer()
        determine_flip = [1, 0]
        flipping = discord.Embed(title="A coin has been flipped...",
                                 colour=0xad7e66)
        flipping.set_image(url="https://i.imgur.com/nULLx1x.gif")
        flipping.set_footer(text="Coinflip | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        msg = await interaction.followup.send(embed=flipping, content=None)
        await asyncio.sleep(3)
        if random.choice(determine_flip) == 1:
            heads = discord.Embed(title="The coin landed on heads!",
                                  colour=0xad7e66)
            heads.set_image(url="https://i.imgur.com/h1Os447.png")
            heads.set_footer(text="Coinflip | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
            await interaction.followup.edit_message(message_id=msg.id, embed=heads)
        else:
            tails = discord.Embed(title="The coin landed on tails!",
                                  colour=0xad7e66)
            tails.set_image(url="https://i.imgur.com/EiBLhPX.png")
            tails.set_footer(text="Coinflip | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
            await interaction.followup.edit_message(message_id=msg.id, embed=tails)
        
# MATH
    @app_commands.command()
    @app_commands.describe(expression="The math equation you want to solve.")
    async def math(self, interaction: discord.Interaction, expression: str):
        """Solves a math equation."""
        match = re.match(r"(\d+(\.\d+)?)([+\-*/])(\d+(\.\d+)?)", expression)
        if match:
            left, _, operator, right, _ = match.groups()
            left, right = float(left), float(right)
            if operator in operators:
                try:
                    result = operators[operator](left, right)
                    embed = discord.Embed(title=f"{left} {operator} {right}  = {result}", colour=0xad7e66)

                    embed.set_footer(text="Math | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
                    await interaction.response.send_message(embed=embed)
                except ZeroDivisionError:
                    embed = discord.Embed(title="<:denied:1336100920039313448> | Error! Division by zero is not allowed.", colour=0xad7e66)

                    embed.set_footer(text="Math | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
                    await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title="<:denied:1336100920039313448> | Error! Invalid symbol - please use one of the following: +, -, *, /", colour=0xad7e66)

                embed.set_footer(text="Math | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
                await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="<:denied:1336100920039313448> | Error! Invalid expression - please use the format: number symbol number (e.g., 1+1)", colour=0xad7e66)

            embed.set_footer(text="Math | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
            await interaction.response.send_message(embed=embed)

# 8ball
    @app_commands.command(name='8ball')
    @app_commands.describe(question="The question you would like to ask.", potato_mode="Whether you want to enable goof mode. Default = False.")
    async def eight_ball(self, interaction: discord.Interaction, *, question: str, potato_mode: bool = False):
        """Asks the magic 8ball a question."""
        if potato_mode == True:
            response = random.choice(funny_eightball_answers) 
            embed = discord.Embed(title=f"<:potato:1341804459977605130> {question}",
                        description=f"{response}", colour=0xad7e66)

            embed.set_footer(text="8ball | Tracker",
                    icon_url="https://i.imgur.com/J8jXkhj.png")
            await interaction.response.send_message(embed=embed)  
        else:
            response = random.choice(eightball_answers) 
            embed = discord.Embed(title=f"{question}",
                        description=f"{response}", colour=0xad7e66)

            embed.set_footer(text="8ball | Tracker",
                    icon_url="https://i.imgur.com/J8jXkhj.png")
            await interaction.response.send_message(embed=embed)  

# CAT
    @app_commands.command()
    async def cat(self, interaction: discord.Interaction):
        """Sends a random Cat image."""
        response = requests.get('https://api.thecatapi.com/v1/images/search')
        data = response.json()
        cat_image_url = data[0]['url']
        embed = discord.Embed(colour=0xad7e66)

        embed.set_image(url=f"{cat_image_url}")

        embed.set_footer(text="Cat | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)

# DOG
    @app_commands.command()
    async def dog(self, interaction: discord.Interaction):
        """Sends a random Dog image."""
        response = requests.get("https://random.dog/woof.json")
        data = response.json()
        dog_image_url = data["url"]
        embed = discord.Embed(colour=0xad7e66)

        embed.set_image(url=f"{dog_image_url}")

        embed.set_footer(text="Dog | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)

# GOOGLE
    @app_commands.command()
    @app_commands.describe(query="The query you want results for.")
    async def google(self, interaction: discord.Interaction, *, query: str):
        """Search Google for web results."""
        await interaction.response.defer()
        msg = await interaction.followup.send(f"<:search:1338134220718997625> | Searching for '{query}'. This may take a while. <:happy_tracker:1329914691656614042>")
        msgid = msg.id
        results = google_search(query)
        if not results:
            return await interaction.followup.edit_message(message_id=msgid, content=f"<:denied:1336100920039313448> | No images found for '{query}'.")

        view = GoogleSearchView(results, query)
        embed = discord.Embed(
            title=results[0]['title'],
            url=results[0]['link'],
            description=results[0].get('snippet', ''),
            color=0xad7e66,
        )
        embed.set_footer(text=f"Result 1 / {len(results)} | {query} | Tracker", icon_url="https://i.imgur.com/kNe7FRh.png")
        await interaction.followup.edit_message(message_id=msgid, embed=embed, view=view, content=None)

# GOOGLE IMAGE
    @app_commands.command()
    @app_commands.describe(query="The query you want results for.")
    async def image(self, interaction: discord.Interaction, *, query: str):
        """Search Google for image results."""
        
        await interaction.response.defer()
        
        msg = await interaction.followup.send(f"<:search:1338134220718997625> | Image searching for '{query}'. This may take a while. <:happy_tracker:1329914691656614042>")

        msgid = msg.id

        # Set search parameters
        search_params = {
            'q': query,
            'num': 15,  # Number of results to fetch
            'safe': 'high',  # Ensures that results are safe for work (SFW)
            'fileType': 'jpg|png',  # Only JPG and PNG images
        }

        gis.search(search_params=search_params)
        
        images = [result.url for result in gis.results()] if gis.results() else []

        if images:
            view = ImageSearchView(images, query, timeout=300)
            view.msg = msg
            embed = discord.Embed(colour=0xad7e66)
            embed.set_footer(text=f"Image 1 / 15 | {query} | Tracker",
                 icon_url="https://i.imgur.com/kNe7FRh.png")
            embed.set_image(url=images[0])
            await interaction.followup.edit_message(message_id=msgid, embed=embed, view=view, content=None)
        else:
            await interaction.followup.edit_message(message_id=msgid, content=f"<:denied:1336100920039313448> | No images found for '{query}'.")

# SERVERINFO
    @app_commands.command()
    async def serverinfo(self, interaction: discord.Interaction):
        """Shows some generic server info."""
        server = interaction.guild
        creation_time = int(server.created_at.timestamp()) 
        embed = discord.Embed(title=f"Server Information for {server.name}", colour=0xad7e66)
        embed.description = (
            f"**Server Name**: {server.name}\n"
            f"**Server ID**: `{server.id}`\n"
            f"**Owner**: {server.owner.mention}\n"
            f"**Member Count**: {server.member_count}\n"
            f"**Created At**: <t:{creation_time}:f>"
        )
        embed.set_thumbnail(url=server.icon.url)
        embed.set_footer(text="ServerInfo | Tracker",
            icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)

# AVATAR
    @app_commands.command()
    @app_commands.describe(member="The member who's avatar you want to view.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        """Shows the avatar of a user."""
        if member is None:
            member = interaction.user
        avatar_url = member.avatar.url if member.avatar else member.display_avatar.url
        embed = discord.Embed(title=f"{member.display_name}'s avatar:", colour=0xad7e66)

        embed.set_image(url=f"{avatar_url}")

        embed.set_footer(text="Avatar | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)

# SERVERICON
    @app_commands.command()
    async def servericon(self, interaction: discord.Interaction):
        """Send the server's icon."""
        server_icon = interaction.guild.icon.url 
        embed = discord.Embed(colour=0xad7e66)

        embed.set_image(url=f"{server_icon}")

        embed.set_footer(text="ServerIcon | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")
        await interaction.response.send_message(embed=embed)

# USERINFO
    @app_commands.command()
    @app_commands.describe(member="The user you want info for.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        """Shows some generic user info."""
        if member is None:
            member = interaction.user

        roles = sorted(member.roles[1:], key=lambda role: role.position, reverse=True)
        displayed_roles = roles[:10]
        total_roles_count = len(roles)
        remaining_roles_count = total_roles_count - len(displayed_roles)
        roles_str = ' • '.join([f"<@&{role.id}>" for role in displayed_roles])
        if remaining_roles_count > 0:
            roles_str += f"\n... {remaining_roles_count} More"

        admin_permission = "✅" if member.guild_permissions.administrator else "❌"

        booster_status = "✅" if member.premium_since else "❌"

        username = member.name
        display_name = member.display_name
        now = datetime.now(timezone.utc)
        created_at = f"<t:{int(member.created_at.timestamp())}:f> (<t:{int(member.created_at.timestamp())}:R>)"
        joined_at = f"<t:{int(member.joined_at.timestamp())}:f> (<t:{int((now - member.joined_at).total_seconds())}:R>)"

        embed = discord.Embed(title=display_name, colour=0xad7e66)
        embed.set_author(name=f"{username}", icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="ℹ️ User Info",
            value=(
                f"User ID: `{member.id}` ({member.mention})\n"
                f"Created: {created_at}\n"
                f"Joined: {joined_at}\n"
                f"Administrator: {admin_permission}\n"
                f"Booster: {booster_status}"
            ),
            inline=False
        )
        embed.add_field(
            name=f"<:mention:1340087267678752860> {total_roles_count} Roles",
            value=f"{roles_str}",
            inline=False
        )

        embed.set_footer(text="UserInfo | Tracker",
            icon_url="https://i.imgur.com/J8jXkhj.png")

        await interaction.response.send_message(embed=embed)

# DICTIONARY
    @app_commands.command()
    @app_commands.describe(word="The word you want a definiton for.")
    async def define(self, interaction: discord.Interaction, *, word: str):
        """Sends the definition of a word."""
        url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                meaning = data[0]['meanings'][0]
                definition = meaning['definitions'][0]['definition']
                example = meaning['definitions'][0].get('example', 'No example available.')
                part_of_speech = meaning['partOfSpeech']

                embed = discord.Embed(title=f'Definition of {word}', colour=0xad7e66)
                embed.add_field(name='Part of Speech', value=part_of_speech, inline=False)
                embed.add_field(name='Definition', value=definition, inline=False)
                embed.add_field(name='Example', value=example, inline=False)

                embed.set_footer(text="Define | Tracker",
                 icon_url="https://i.imgur.com/J8jXkhj.png")

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f'No definitions found for "{word}".')
        else:
            await interaction.response.send_message(f'Error: Could not retrieve definitions for "{word}".')

fun_commands = Fun(name="fun", description="Fun Commands.")
bot.tree.add_command(fun_commands)

@bot.tree.command()
async def pet(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer()
    user = user or interaction.user
    avatar_url = user.avatar.url if user.avatar else user.display_avatar.url
    api_url = f"https://api.obamabot.me/v2/image/petpet?image={avatar_url}"
    
    response = requests.get(api_url)
    if response.status_code != 200:
        await log_error(interaction.guild, bot, interaction.command.name, "Failed to generate petpet GIF. The API may be down.")
        return
    
    gif_url = response.json().get("url")
    if not gif_url:
        await log_error(interaction.guild, bot, interaction.command.name, "Failed to retrieve petpet GIF. API response was invalid.")
        return
    
    gif_response = requests.get(gif_url)
    if gif_response.status_code != 200:
        await log_error(interaction.guild, bot, interaction.command.name, "Failed to download the GIF.")
        return
    
    gif_image = Image.open(BytesIO(gif_response.content))
    frames = [
        frame.copy().resize((frame.width * 2, frame.height * 2), Image.Resampling.LANCZOS)
        for frame in ImageSequence.Iterator(gif_image)
    ]

    gif_bytes = BytesIO()
    frames[0].save(
        gif_bytes, format="GIF", save_all=True, append_images=frames[1:], loop=0, duration=gif_image.info["duration"]
    )
    gif_bytes.seek(0)

    file = discord.File(gif_bytes, filename="petpet_large.gif")
    await interaction.followup.send(f"{interaction.user.mention} pets {user.mention}! <:pet:1350528870830571621><a:heart:1350529555965677710>", file=file)

# PING
@bot.hybrid_command()
async def ping(ctx):
    """Sends the bot's latency."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! {latency}ms")
    
# STATUS  
@bot.tree.command()
@is_dev()
async def status(interaction: discord.Interaction, *, new_status: str):
    """⚙️ | Change the Bot's status."""
    try:
        await bot.change_presence(activity=discord.CustomActivity(name=new_status))
        await interaction.response.send_message(f'Status changed to: `{new_status}`', ephemeral=True)
        await master_log_message(interaction.guild, bot, interaction.command.name,f"{interaction.user.mention} ({interaction.user.name}) changed my status to `{new_status}`.")
    except commands.CheckFailure:
        pass
        
class DeleteEmbedView(View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="🗑️", style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

class ShopDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Writing Instruments", value="writing"),
            discord.SelectOption(label="Logbooks", value="logbooks"),
            discord.SelectOption(label="Containers", value="containers"),
        ]
        super().__init__(placeholder="Select a category", options=options)

    async def callback(self, interaction: discord.Interaction):
        embeds = {
            "writing": discord.Embed(title="Writing Instruments", description="""
__Pen Type__:
EZWrite [ID: **1**] {Uses: **10**} (Price: **G$5**)
GlideMaster [ID: **2**] {Uses: **30**} (Price: **G$15**)
CosmoScribe [ID: **3**] {Uses: **100**} (Price: **G$50**)

__Pen Colour__:
Red [ID: **.1**]\nGreen [ID: **.2**]\nBlue [ID: **.3**]\nBlack [ID: **.4**]\nPurple [ID: **.5**]

__Pencil Type__:
Regular Pencil [ID: **4**] {Uses: **5**} (Price: **G$3**)
Golf Pencil (goes inside a cache) [ID: **5**] {Uses: **10**} (Price: **G$5**)
Mechanical Pencil [ID: **6**] {Uses: **50**} (Price: **G$30**)
""", colour=0xad7e66),
            "logbooks": discord.Embed(title="Logbooks", description="Coming soon...", colour=0xad7e66),
            "containers": discord.Embed(title="Containers", description="Coming soon...", colour=0xad7e66)
        }
        await interaction.response.edit_message(embed=embeds[self.values[0]], view=self.view)

class PurchaseModal(Modal, title="Purchase Items"):
    selection = TextInput(
        label="Enter Item IDs",
        placeholder="E.g., 1.1,1.2,1.3",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Parse the input into a list of item IDs
        raw_input = self.selection.value.strip()
        item_ids = [item.strip() for item in raw_input.split(',') if item.strip()]  # Split by commas and strip whitespace

        total_price = 0
        purchased_items = []
        async with Session() as session:
            user_id = interaction.user.id
            balance = await get_balance(session, user_id)

            for item_id in item_ids:
                parts = item_id.split('.')
                main_item = MAIN_INVENTORY.get(parts[0], "Unknown Item")
                alt_item = ALT_INVENTORY.get(f".{parts[1]}", "") if len(parts) > 1 else ""
                item_name = f"{alt_item} {main_item}".strip()

                price = SHOP_PRICES.get(parts[0], 0)

                if main_item == "Unknown Item" or (parts[0] in ['4', '5', '6'] and '.' in item_id):
                    await interaction.response.send_message(
                        f"Invalid item ID: {item_id}. Please try again.", ephemeral=True
                    )
                    return

                if balance < total_price + price:
                    await interaction.response.send_message(
                        f"You don't have enough money to buy all items. Current balance: G${balance}.", ephemeral=True
                    )
                    return

                total_price += price
                purchased_items.append(item_id)

            # Deduct the total price and add items to inventory
            new_balance = balance - total_price
            await update_balance(session, user_id, new_balance)
            for item_id in purchased_items:
                await add_inv_item(session, user_id, item_id)

            # Prepare the response message
            purchased_names = ", ".join(
                f"{ALT_INVENTORY.get(f'.{item.split('.')[1]}', '')} {MAIN_INVENTORY.get(item.split('.')[0], 'Unknown Item')}".strip()
                if '.' in item else MAIN_INVENTORY.get(item, "Unknown Item")
                for item in purchased_items
            )
            await interaction.response.send_message(
                f"You bought **{purchased_names}**. Total cost: **G${total_price}**. New balance: **G${new_balance}**.",
                ephemeral=True
            )

class ShopView(View):
    def __init__(self):
        super().__init__()
        self.add_item(ShopDropdown())
        self.add_item(PurchaseButton())

class PurchaseButton(Button):
    def __init__(self):
        super().__init__(label="🛒 | Purchase", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PurchaseModal())

def increment_code(code):
    match = re.match(r"GX(\d+)([A-Z]*)", code)
    
    if not match:
        raise ValueError(f"Invalid code format: {code}")
    
    number_part = int(match.group(1))
    letter_part = match.group(2)

    if not letter_part:
        number_part += 1
        return f"GX{number_part}"

    else:
        letter_list = list(letter_part)
        last_letter = letter_list[-1]

        if last_letter == 'Z':
            letter_list[-1] = 'A'
            number_part += 1  
        else:
            letter_list[-1] = chr(ord(last_letter) + 1)

        new_letter_part = ''.join(letter_list)
        return f"GX{number_part}{new_letter_part}"
    
async def get_next_gc_code(session):
    existing_codes = set(await get_all_hide_ids(session)) 
    next_code = "GX1"

    while next_code in existing_codes:
        next_code = increment_code(next_code)
    
    return next_code

def base36_encode(number: int) -> str:
    """Convert an integer to base-36 (0-9, A-Z) encoding."""
    base36_chars = string.digits + string.ascii_uppercase
    result = ""
    while number:
        number, remainder = divmod(number, 36)
        result = base36_chars[remainder] + result
    return result or "0"
        
        
LOCATION_COORDS = {
    "Harrowsbrook": (51.512, -0.132),
    "Everfield": (40.712, -74.006),
    "Larkspur Crossing": (34.052, -118.243),
    "Brunswick Harbor": (29.760, -95.369),
    "Alderpoint": (37.774, -122.419),
    "Frostbrook Ridge": (45.523, -122.676),
    "Blackrock Desert": (40.977, -119.055),
    "Echo Lake Caverns": (39.739, -104.990),
    "Storm Island": (47.606, -122.332),
    "Dry Hollow Basin": (36.169, -115.139),
    "Mosswood Swamp": (30.267, -97.743),
    "Silverfall Bluff": (25.761, -80.191),
    "Frozen Hollow": (39.952, -75.165),
    "Oldport Ruins": (33.749, -84.388),
    "Whistler’s Canyon": (32.776, -96.797),
}

SHOP_PRICES = {
    "1": 5,   # EZWrite Pen
    "2": 15,  # GlideMaster Pen
    "3": 50,  # CosmoScribe Pen
    "4": 3,   # Regular Pencil
    "5": 5,   # Golf Pencil
    "6": 30,  # Mechanical Pencil
}

MAIN_INVENTORY = {
    "1": "EZWrite Pen",   
    "2": "GlideMaster Pen",  
    "3": "CosmoScribe Pen", 
    "4": "Regular Pencil",   
    "5": "Golf Pencil",  
    "6": "Mechanical Pencil",
}

ALT_INVENTORY = {
    ".1": "Red",   
    ".2": "Green",  
    ".3": "Blue", 
    ".4": "Black",   
    ".5": "Purple",  
}

class HideConfigData:
    def __init__(self):
        self.name = None
        self.location = None
        self.description = None
        self.difficulty = None
        self.terrain = None
        self.lat = None
        self.lon = None
        self.size = None

class InputModal(Modal):
    def __init__(self, title: str, field_name: str, hide_data: HideConfigData):
        super().__init__(title=title)
        self.field_name = field_name
        self.hide_data = hide_data
        self.input_field = TextInput(label=f"Enter {field_name}", placeholder="Type here", required=True)
        self.add_item(self.input_field)

    async def on_submit(self, interaction: discord.Interaction):
        value = self.input_field.value
        setattr(self.hide_data, self.field_name, value)
        logging.debug(f"Set {self.field_name} to {value}")
        embed = HideConfigureSelect.create_embed(self.hide_data)
        await interaction.response.edit_message(embed=embed)

class DifficultySelect(Select):
    def __init__(self, hide_data: HideConfigData):
        self.hide_data = hide_data
        options = [
            discord.SelectOption(label=str(value), value=str(value))
            for value in [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
        ]
        super().__init__(placeholder="Select difficulty (1-5)", options=options)

    async def callback(self, interaction: discord.Interaction):
        self.hide_data.difficulty = self.values[0]
        await interaction.response.edit_message(content=f"Set difficulty to {self.hide_data.difficulty}/5", view=None)


class TerrainSelect(Select):
    def __init__(self, hide_data: HideConfigData):
        self.hide_data = hide_data
        options = [
            discord.SelectOption(label=str(value), value=str(value))
            for value in [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
        ]
        super().__init__(placeholder="Select terrain (1-5)", options=options)

    async def callback(self, interaction: discord.Interaction):
        self.hide_data.terrain = self.values[0]
        await interaction.response.edit_message(content=f"Set terrain to {self.hide_data.terrain}/5", view=None)
        
class SizeSelect(Select):
    def __init__(self, hide_data: HideConfigData):
        self.hide_data = hide_data
        options = [
            discord.SelectOption(label=str(value), value=str(value))
            for value in ["Micro", "Small", "Regular", "Large", "Extra-Large"]
        ]
        super().__init__(placeholder="Select size", options=options)

    async def callback(self, interaction: discord.Interaction):
        self.hide_data.size = self.values[0]
        await interaction.response.edit_message(content=f"Set size to {self.hide_data.size}", view=None)

class HideConfigureSelect(Select):
    def __init__(self, hide_data: HideConfigData):
        self.hide_data = hide_data
        options = [
            discord.SelectOption(label="Name", value="name"),
            discord.SelectOption(label="Location", value="location"),
            discord.SelectOption(label="Description", value="description"),
            discord.SelectOption(label="Difficulty", value="difficulty"),
            discord.SelectOption(label="Terrain", value="terrain"),
            discord.SelectOption(label="Size", value="size"),
            discord.SelectOption(label="Publish Hide", value="publish")
        ]
        super().__init__(placeholder="Select an option to configure...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] in ["name", "description"]:
            modal = InputModal(title=f"Enter {self.values[0]}", field_name=self.values[0], hide_data=self.hide_data)
            await interaction.response.send_modal(modal)
        elif self.values[0] == "location":
            await self.prompt_for_location(interaction)
        elif self.values[0] == "difficulty":
            view = View()
            view.add_item(DifficultySelect(self.hide_data))
            await interaction.response.send_message("Select a difficulty level:", view=view, ephemeral=True)
        elif self.values[0] == "terrain":
            view = View()
            view.add_item(TerrainSelect(self.hide_data))
            await interaction.response.send_message("Select a terrain level:", view=view, ephemeral=True)
        elif self.values[0] == "size":
            view = View()
            view.add_item(SizeSelect(self.hide_data))
            await interaction.response.send_message("Select a size level:", view=view, ephemeral=True)
        elif self.values[0] == "publish":
            await self.publish_hide(interaction)

    async def prompt_for_location(self, interaction: discord.Interaction):
        options = [discord.SelectOption(label=loc, value=loc) for loc in LOCATION_COORDS.keys()]
        select = Select(placeholder="Choose a location", options=options)

        async def select_callback(interaction: discord.Interaction):
            self.hide_data.location = select.values[0]
            self.hide_data.lat, self.hide_data.lon = LOCATION_COORDS[select.values[0]]
            await interaction.response.edit_message(content=f"Set hide location to {self.hide_data.location}", view=None)

        select.callback = select_callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message("Select a location:", view=view, ephemeral=True)

    async def publish_hide(self, interaction: discord.Interaction):
        if all([self.hide_data.name, self.hide_data.location, self.hide_data.description, self.hide_data.difficulty, self.hide_data.terrain, self.hide_data.lat, self.hide_data.lon, self.hide_data.size]):
            logging.debug("Publishing geocache...")

            async with Session() as session: 
                cache_id = await get_next_gc_code(session)  
                await add_hide(session, cache_id, interaction.user.id, self.hide_data.name, 
                                self.hide_data.lat, self.hide_data.lon, self.hide_data.description, 
                                self.hide_data.difficulty, self.hide_data.terrain, self.hide_data.size, self.hide_data.location)

            await interaction.response.send_message(f"Geocache published successfully! ID: `{cache_id}`")
        else:
            await interaction.response.send_message("Please configure all fields before publishing.", ephemeral=True)

    @staticmethod
    def create_embed(hide_data: HideConfigData):
        embed = Embed(title="Geocache Hide Configuration")
        embed.add_field(name="Name", value=hide_data.name or "Not set", inline=False)
        embed.add_field(name="Location", value=hide_data.location or "Not set", inline=False)
        embed.add_field(name="Latitude", value=str(hide_data.lat) if hide_data.lat else "Not set", inline=False)
        embed.add_field(name="Longitude", value=str(hide_data.lon) if hide_data.lon else "Not set", inline=False)
        embed.add_field(name="Description", value=hide_data.description or "Not set", inline=False)
        embed.add_field(name="Difficulty", value=hide_data.difficulty or "Not set", inline=False)
        embed.add_field(name="Terrain", value=hide_data.terrain or "Not set", inline=False)
        embed.add_field(name="Size", value=hide_data.size or "Not set", inline=False)
        return embed

class SetNameModal(Modal, title="Set Cacher Name"):
    selection = TextInput(label="Enter Cacher Name", placeholder="eg. BooZac (character limit: 15)")

    def __init__(self, original_message):
        super().__init__()
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        cacher_name = self.selection.value
        if len(cacher_name) > 15:
            await interaction.response.send_message("Cacher name exceeds 15 characters. Please try again.", ephemeral=True)
            return
        else:
            async with Session() as session:
                await add_user_to_db(session, user_id, cacher_name)
                await self.original_message.delete()
                await interaction.response.send_message(f"Your cacher name has been set to: `{cacher_name}`. Welcome to the game!", ephemeral=True)

class CacherNameView(View):
    def __init__(self, original_message):
        super().__init__()
        self.original_message = original_message

    @discord.ui.button(label="📛 | Set Name", style=discord.ButtonStyle.success)
    async def set_name_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetNameModal(self.original_message))

# GEOCACHING ECONOMY GAME
class Economy(app_commands.Group):
    """Geocaching Game Commands!"""
    
    @app_commands.command()
    async def balance(self, interaction: discord.Interaction):
        user = interaction.user
        user_id = user.id
        async with Session() as session:
            user_database_settings = await get_db_settings(session, user_id)
            if user_database_settings is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))            
                return
            else:
                balance = await get_balance(session, user_id)
                await interaction.response.send_message(f"{interaction.user.mention} ({interaction.user.name})'s balance is G${balance}.")
        
    @app_commands.command()
    async def finds(self, interaction: discord.Interaction):
        user = interaction.user
        user_id = user.id
        async with Session() as session:
            user_database_settings = await get_db_settings(session, user_id)
            if user_database_settings is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))            
                return
            else:
                finds = await get_finds(session, user_id)
                await interaction.response.send_message(f"{interaction.user.mention} ({interaction.user.name}) has {finds} finds.")

    @app_commands.command()
    @app_commands.choices(option=[
        app_commands.Choice(name="Rural Locations", value="1"),
        app_commands.Choice(name="City Locations", value="2")
    ])
    async def locations(self, interaction: discord.Interaction, option: app_commands.Choice[str]):
        view = DeleteEmbedView()
        if option.value == "1":
            embed = discord.Embed(
                title="Rural Geocaching Locations",
                description="Frostbrook Ridge – A remote, snow-covered mountain range in the far north, sparsely populated with only a few settlements. The frost here is intense, and the landscape is dominated by towering pines and frozen rivers.\n\nBlackrock Desert – A vast, dry expanse marked by jagged black rock formations and endless stretches of sandy dunes. The area is harsh, with scorching days and freezing nights, making it nearly impossible for anything to survive.\n\nEcho Lake Caverns – A series of limestone caves tucked deep within the forest, where the sound of water trickling through the walls creates an eerie, echoing effect. The caverns are home to rare species of bats and underground plants.\n\nStorm Island – A small, isolated island off the coast known for its unpredictable and frequent storms. Few fishermen dare to approach, and it remains largely uncharted by modern maps.\n\nDry Hollow Basin – An arid region with cracked earth and sparse vegetation, where ancient dry riverbeds tell stories of once-thriving communities now long abandoned. It’s an unforgiving place, where any trace of water is a rare find.\n\nMosswood Swamp – A damp, murky wetland full of thick moss and cypress trees. The air is heavy with the scent of decay, and it's said that the fog here often hides the movements of unseen creatures.\n\nSilverfall Bluff – A windswept plateau overlooking a wide river valley. The cliff faces here shimmer with silver-colored rock formations, and the wind blows relentlessly, making it a difficult place to traverse.\n\nFrozen Hollow – A remote tundra, where temperatures regularly plunge below freezing. The landscape is dotted with glaciers and ice-covered ruins of old settlements, making it an inhospitable but fascinating place for explorers.\n\nOldport Ruins – The remains of an ancient port city once bustling with trade. Now submerged under a shallow layer of water, only the tops of old stone buildings poke through the surface, a haunting reminder of its former glory.\n\nWhistler’s Canyon – A narrow, wind-carved canyon where the winds create strange, howling noises as they pass through. It’s known for its rugged terrain and its reputation as a dangerous spot for hikers and travelers.",
                colour=0xad7e66
            )

            embed.set_footer(text="This embed will self-destruct in 5 minutes. Click the 🗑️ icon to delete now.")

            await interaction.response.send_message(embed=embed, view=view)
            sent_message = await interaction.original_response()
            await asyncio.sleep(300)
            await sent_message.delete()
            
        else:
            embed = discord.Embed(title="Rural Geocaching Locations",
                      description="Harrowsbrook – A small industrial town nestled by the river, known for its aging factories and old brick buildings. The town has a gritty, blue-collar vibe, with a rich history tied to its ironworks and textile mills.\n\nEverfield – A city surrounded by sprawling farmland and endless green fields, where the pace of life is slow, and the community is tight-knit. Known for its annual agricultural fairs and harvest festivals.\n\nLarkspur Crossing – A vibrant market town that acts as a key transportation hub, with people coming from all around to trade goods. The town is built around a large central square where street vendors and performers gather.\n\nBrunswick Harbor – A busy coastal city known for its bustling harbor, where fishing boats and cargo ships dock daily. The city has a lively waterfront, with seafood restaurants and bars overlooking the docks.\n\nAlderpoint – A hilltop city known for its historic architecture, with winding cobblestone streets and a centuries-old cathedral at the city’s heart. It has a more refined, older charm, with an abundance of parks and cultural institutions.",
                      colour=0xa39343)
            embed.set_footer(text="This embed will self-destruct in 5 minutes. Click the 🗑️ icon to delete now.")
            await interaction.response.send_message(embed=embed, view=view)
            sent_message = await interaction.original_response()
            await asyncio.sleep(300)
            await sent_message.delete()

    @app_commands.command()
    async def hide(self, interaction: discord.Interaction):
        async with Session() as session:
            user_id = interaction.user.id
            user_database_settings = await get_db_settings(session, user_id)
            if user_database_settings is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))            
                return
            else:
                hide_data = HideConfigData()
                select = HideConfigureSelect(hide_data=hide_data)
                view = View()
                view.add_item(select)
                embed = HideConfigureSelect.create_embed(hide_data)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
    @app_commands.command()
    async def cache_info(self, interaction: discord.Interaction, cache_id: str):
        async with Session() as session:
            user_id = interaction.user.id
            user_database_settings = await get_db_settings(session, user_id)
            if user_database_settings is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))            
                return
            else:
                cacher_name_db = await get_db_settings(session, user_id)
                cacher_name = cacher_name_db.cacher_name
                hide = await get_hide_by_id(session, cache_id)

                if not hide:
                    await interaction.response.send_message("Cache not found.", ephemeral=True)
                    return

                timestamp = int(hide.hidden_at.timestamp())

                hidden_at_str = f"<t:{timestamp}:F> (<t:{timestamp}:R>)"

                location_str = f"{hide.location_lat:.6f}, {hide.location_lon:.6f} ({hide.location_name})"

                formatted_hider_mention = f"<@{str(hide.user_id)}>"

                embed = discord.Embed(title=f"Cache Info: {hide.name}", color=0xad7e66)
                embed.add_field(name="Cache ID", value=f"`{hide.id}`", inline=False)
                embed.add_field(name="Cache Owner", value=f"{cacher_name} ({formatted_hider_mention})", inline=False)
                embed.add_field(name="Location", value=location_str, inline=False)

                if hide.description:
                    embed.add_field(name="Description", value=hide.description, inline=False)

                embed.add_field(name="Difficulty", value=f"{hide.difficulty}/5", inline=True)
                embed.add_field(name="Terrain", value=f"{hide.terrain}/5", inline=True)
                embed.add_field(name="Size", value=f"{hide.size}", inline=True)
                embed.add_field(name="Hidden At", value=hidden_at_str, inline=False)

                await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def shop(self, interaction: discord.Interaction):
        """Browse the G$ shop."""
        async with Session() as session:
            user_id = interaction.user.id
            user_database_settings = await get_db_settings(session, user_id)
            if user_database_settings is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))            
                return
            else:
                embed = discord.Embed(title="G$ Shop", description="Select a category from the dropdown to browse items.", colour=0xad7e66)
                await interaction.response.send_message(embed=embed, view=ShopView())
                
    @app_commands.command()
    async def inventory(self, interaction: discord.Interaction):
        async with Session() as session:
            user_id = interaction.user.id
            user_database_settings = await get_db_settings(session, user_id)
            if user_database_settings is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))
                return
            else:
                inventory_items = await get_inventory(session, user_id)  # Fetch all inventory items
                if not inventory_items:
                    await interaction.response.send_message("Your inventory is empty.", ephemeral=True)
                    return

                # Count occurrences of each item
                item_counts = {}
                for item in inventory_items:
                    item = item.strip()  # Remove any leading/trailing whitespace
                    item_counts[item] = item_counts.get(item, 0) + 1

                embed = discord.Embed(
                    title=f"{interaction.user.display_name}'s Inventory:",
                    colour=0xad7e66
                )

                for item, count in item_counts.items():
                    # Split the item ID into main and optional color parts
                    parts = item.split('.')
                    main_item = MAIN_INVENTORY.get(parts[0], "Unknown Item")  # Get the main item
                    alt_item = ALT_INVENTORY.get(f".{parts[1]}", "") if len(parts) > 1 else ""  # Get the color if it exists
                    item_name = f"{alt_item} {main_item}".strip()  # Combine color and main item, if any
                    embed.add_field(
                        name=f"{count}x {item_name}",
                        value="", 
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)
        
eco_commands = Economy(name="game", description="Geocaching Game Commands.")
bot.tree.add_command(eco_commands)

class Game_Admin(app_commands.Group):
    """Geocaching Game Admin Commands!"""
    
    @app_commands.command()
    @is_dev()
    async def add_money(self, interaction: discord.Interaction, amount: str, user: discord.Member = None):
        user = user or interaction.user
        user_id = user.id
        try:
            amount = int(amount) 
        except ValueError:
            await interaction.response.send_message("Invalid amount! Please enter a number.", ephemeral=True)
            return
        async with Session() as session:
            balance = await get_balance(session, user_id)
            newbal = balance + amount
            await update_balance(session, user_id, newbal)

        await interaction.response.send_message(f"Added G${amount} to {user.mention} ({user.name})'s balance, which is now G${newbal}.")
        await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) added G${amount} to {user.mention} ({user.name})'s balance, which is now G${newbal}.")
        
eco_a_commands = Game_Admin(name="game_admin", description="Geocaching Game Admin Commands.")
bot.tree.add_command(eco_a_commands)

bot.run(TOKEN2)