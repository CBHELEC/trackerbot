import discord
import re
import aiohttp
from discord import app_commands
from embedbuilder import BaseView
from functions import *
from bot import bot
from logger import log
from discord.app_commands import CheckFailure

class Message(app_commands.Group):
    DELETE_TIME_DELAY = 5
    def __init__(self, bot):
        super().__init__(name="message", description="Message Commands.")
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only let commands run if the Server Owner or Admin has enabled them."""
        setting = get_guild_settings(interaction.guild.id)
        fun_status = int(setting.message_set) if hasattr(setting, 'message_set') else 1
        if fun_status == 0:
            raise CheckFailure("M_COMMANDS_DISABLED_BY_ADMIN")
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if isinstance(error, CheckFailure) and str(error) == "M_COMMANDS_DISABLED_BY_ADMIN":
            msg = "This command set has been disabled by the Server Owner or an Admin. Please contact them for more info."
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return
        raise error

# SAY
    @app_commands.command()
    @is_perm_mod()
    @app_commands.describe(
    saying="What you want me to say",
    channel="Please ignore this"
    )
    async def say(self, interaction: discord.Interaction, saying: str, channel: discord.TextChannel = None):
        """Says what you wanted where you wanted."""
        speak_channel = channel or interaction.channel
        if "@everyone" not in saying or "@here" not in saying:
            try:
                await speak_channel.send(saying)
                await interaction.response.send_message(
                    f"Message sent.", ephemeral=True
                )
                await log(interaction, f"I said '{saying}' in {speak_channel.id}")
            except discord.Forbidden:
                no_chan = f"<#{speak_channel.id}>"
                await interaction.response.send_message(
                    f"I do not have permission to send messages in {no_chan}. Please notify an Administrator and try again.",
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
        elif ("@everyone" in saying and "@here" in saying) and interaction.user.guild_permissions.mention_everyone:
            try:
                await interaction.response.send_message(
                    f"Message sent.", ephemeral=True
                )
                await log(interaction, f"I said '{saying}' (HAS EVERYONE OR HERE PING) in {speak_channel.id}")
            except discord.Forbidden:
                no_chan = f"<#{speak_channel.id}>"
                await interaction.response.send_message(
                    f"I do not have permission to send messages in {no_chan}. Please notify an Administrator and try again.",
                    ephemeral=True,
                )
            except Exception as e:
                await log_error(interaction.guild, bot, interaction.command.name, 
                    f"User: {interaction.user.mention} ({interaction.user.name}) ({interaction.user.name}) in <#{interaction.channel.id}> ({interaction.channel.name}) saying `{saying}`. Error: \n```\n{str(e)}\n```"
                )
                await interaction.response.send_message(
                    "An unknown error occured. The Dev has been notified.",
                    ephemeral=True,
                )
        else:
            await interaction.response.send_message(f"Please do NOT put everyone or here pings in your message. If you should be allowed to, contact the server owner and try again.", ephemeral=True)  
        
# REPLY
    @app_commands.command()
    @is_perm_mod()
    @app_commands.describe(
    message_id="The message ID I will reply to",
    message="What I will reply with"
    )
    async def reply(self, interaction: discord.Interaction, message_id: str, message: str):
        """Replies to a specific message."""
        await interaction.response.defer(ephemeral=True)
        try:
            target_message = await interaction.channel.fetch_message(int(message_id))
            reply_content = message
            await target_message.reply(reply_content)
            await interaction.followup.send("I replied successfully.", ephemeral=True)
            await log(interaction, f"I replied to message {target_message.id} with '{reply_content}' in {interaction.channel.id}")
        except discord.NotFound:
            await interaction.followup.send("The specified message was not found.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                f"I do not have permission to send messages in <#{interaction.channel.id}>. Please notify an Administrator and try again.",
                ephemeral=True,
            )
        except Exception as e:
            await log_error(interaction.guild, bot, interaction.command.name, 
                f"User: {interaction.user.mention} ({interaction.user.name}) ({interaction.user.name}) in <#{interaction.channel.id}> ({interaction.channel.name}) replying with `{message}`. Error: \n```\n{str(e)}\n```"
            )
            await interaction.response.send_message(
                "An unknown error occured. The Dev has been notified.",
                ephemeral=True,
            )

# DELETE
    @app_commands.command()
    @is_perm_mod()
    @app_commands.describe(messageid="ID of the message to delete")
    async def delete(self, interaction: discord.Interaction, messageid: str):
        """Delete a specified message."""
        if messageid is None or messageid == "" or not (re.search(r"^\d{18,19}$", messageid)):
            await interaction.response.send_message("Invalid `/delete` Usage! messageID is invalid or blank!")
        origMessage = await interaction.channel.fetch_message(messageid)
        if origMessage.author != self.bot.user:
            await interaction.response.send_message("I can only delete my own messages.", f"{origMessage.jump_url} is owned by <@{origMessage.author.id}>.")
        if self.DELETE_TIME_DELAY > 0:
            await origMessage.delete(delay=self.DELETE_TIME_DELAY)
            await interaction.response.send_message(f"The message will be deleted in approximately {self.DELETE_TIME_DELAY} seconds.", ephemeral=True)
            await log(interaction, f"I deleted message {origMessage.id} (content: '{origMessage.content}') in {interaction.channel.id} after {self.DELETE_TIME_DELAY} seconds.")
        else:
            await origMessage.delete()
            await interaction.response.send_message(f"The message will be deleted shortly.", ephemeral=True)
            await log(interaction, f"I deleted message {origMessage.id} (content: '{origMessage.content}') in {interaction.channel.id} immediately.")
            
# REACT       
    @app_commands.command(name="react", description="React to a specified message.")
    @app_commands.describe(messageid="ID of the message to react to")
    @app_commands.describe(reaction="How do you want me to react?")
    @is_perm_mod()
    async def react(self, interaction: discord.Interaction, messageid: str, reaction: str):
        if not re.fullmatch(r"\d{18,19}", messageid):
            await interaction.response.send_message("Invalid `/react` Usage. Please get the correct messageID and try again.", ephemeral=True)
            return
        try:
            origMessage = await interaction.channel.fetch_message(int(messageid))
        except discord.NotFound:
            await interaction.response.send_message("Message not found! Check the messageID is correct.", ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.response.send_message(
                f"I do not have permission to send messages in <#{interaction.channel.id}>. Please notify an Administrator and try again.",
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
            await log(interaction, f"I reacted to message {origMessage.id} (content: '{origMessage.content}') with '{emoji}' in {interaction.channel.id}")
        except discord.HTTPException:
            await interaction.response.send_message("Failed to react! Please try again.", ephemeral=True)
            return   
            
# EDIT
    @app_commands.command(name="edit", description="Edit a specified message.")
    @is_perm_mod()
    @app_commands.describe(messageid="ID of the message to delete")
    @app_commands.describe(newmessage="New message content")
    async def edit(self, interaction: discord.Interaction, messageid: str, newmessage: str):
        if messageid is None or messageid == "" or not (re.search(r"^\d{18,19}$", messageid)):
            await interaction.response.send_message("Invalid `/edit` Usage! messageID is invalid or blank.")
        origMessage = await interaction.channel.fetch_message(messageid)
        if origMessage.author != self.bot.user:
            await interaction.response.send_message(f"I can only edit my own messages. {origMessage.jump_url} is owned by <@{origMessage.author.id}>.")
            return
        await origMessage.edit(content=newmessage)
        await interaction.response.send_message("I edited the message!", ephemeral=True) 
        await log(interaction, f"I edited message {origMessage.id} (content: '{origMessage.content}') in {interaction.channel.id} to '{newmessage}'")
            
# EMBEDBUILDER
    @app_commands.command()
    async def embedbuilder(self, interaction: discord.Interaction): 
        """Interactive embed builder."""
        view = BaseView(interaction, self.session)
        await interaction.response.send_message(view.content, view = view)
        message = await interaction.original_response()
        view.set_message(message)
        await view.wait()

async def setup(bot):
    bot.tree.add_command(Message(bot))
