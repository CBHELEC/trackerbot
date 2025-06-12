import aiofiles
import random
import string
import asyncio
import discord
import sqlite3
import sys 
import os 
import importlib.util
from functions import *
from datetime import datetime
from discord import app_commands, Role, Interaction, Embed, ButtonStyle
from discord.ui import View, Button
from database import *
from discord.app_commands import Transform, Transformer
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

class PaginatorView(View):
    def __init__(self, embeds, author_id):
        super().__init__(timeout=300)
        self.embeds = embeds
        self.current_page = 0
        self.author_id = author_id
        self.message = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.author_id

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def on_button_click(self, interaction: Interaction, button_id: str):
        if button_id == "first":
            self.current_page = 0
        elif button_id == "prev":
            self.current_page = (self.current_page - 1) % len(self.embeds)
        elif button_id == "next":
            self.current_page = (self.current_page + 1) % len(self.embeds)
        elif button_id == "last":
            self.current_page = len(self.embeds) - 1

        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(emoji="⏮️", style=ButtonStyle.secondary, custom_id="first")
    async def first(self, interaction: Interaction, button: Button):
        await self.on_button_click(interaction, "first")

    @discord.ui.button(emoji="◀️", style=ButtonStyle.secondary, custom_id="prev")
    async def prev(self, interaction: Interaction, button: Button):
        await self.on_button_click(interaction, "prev")

    @discord.ui.button(emoji="▶️", style=ButtonStyle.secondary, custom_id="next")
    async def next(self, interaction: Interaction, button: Button):
        await self.on_button_click(interaction, "next")

    @discord.ui.button(emoji="⏭️", style=ButtonStyle.secondary, custom_id="last")
    async def last(self, interaction: Interaction, button: Button):
        await self.on_button_click(interaction, "last")

class Debug(app_commands.Group):
    """Debug Developer commands."""
    
    def __init__(self, bot):
        super().__init__(name="debug", description="Developer Debug Commands.")
        self.bot = bot

        self.conn2 = sqlite3.connect(DATA_DIR / 'votes.db')
        self.c = self.conn2.cursor()
        self.c.execute(''' 
            CREATE TABLE IF NOT EXISTS dbl_votes ( 
                user_id TEXT PRIMARY KEY, 
                voted_at TEXT, 
                vote_streak INTEGER DEFAULT 1, 
                reminded INTEGER DEFAULT 0,
                total_votes INTEGER DEFAULT 1
            ) 
        ''')
        self.conn2.commit()
        self.c.execute(''' 
            CREATE TABLE IF NOT EXISTS moneh ( 
                user_id TEXT PRIMARY KEY, 
                moneh INTEGER
            ) 
        ''')
        self.conn2.commit()
        
# DEBUG SETPERM  
    @app_commands.command()
    @is_dev()
    @app_commands.describe(roles='The roles to add', server_id='The server to add them for')
    async def setperm(self, interaction: discord.Interaction, roles: Transform[List[Role], RoleTransformer], server_id: str = None):
        """Force add roles to the permission roles."""
        guild_id = server_id if server_id else interaction.guild.id
        settings = get_guild_settings(guild_id)

        existing_roles = set(settings.perm_role_ids.split(",")) if settings.perm_role_ids else set()
        new_roles = {str(role.id) for role in roles}
        updated_roles = existing_roles.union(new_roles)

        update_guild_settings(guild_id, perm_role_ids=",".join(updated_roles))
        await interaction.response.send_message(f"⚙️🔧✅ Force added permission roles: {', '.join(role.mention for role in roles)} for server {guild_id}")
        await log(interaction, f"⚙️🔧✅ Force added permission roles: {', '.join(role.mention for role in roles)} for server {guild_id}")
    
# DEBUG SETTINGS
    @app_commands.command()
    @is_dev()
    @app_commands.describe(server_id='The server to view the settings for')
    async def settings(self, interaction: discord.Interaction, server_id: str = None):
        """Forcibly fetch and display the guild settings."""
        guild_id = server_id if server_id else interaction.guild.id
        settings = get_guild_settings(guild_id)

        embed = discord.Embed(title=f"⚙️🔧Guild Settings for {guild_id}", color=0xad7e66)
        
        perm_roles = settings.perm_role_ids.split(",") if settings.perm_role_ids else []

        embed.add_field(
            name="Perm Roles",
            value=", ".join(f"<@&{role_id}>" for role_id in sorted(set(perm_roles))) if perm_roles else "None",
            inline=False
        )
        embed.add_field(name="Skullboard Enabled", value="Yes" if settings.skullboard_status else "No", inline=False)
        embed.add_field(name="Skullboard Channel", value=f"<#{settings.skullboard_channel_id}>" if settings.skullboard_channel_id else "Not set", inline=False)

        await interaction.response.send_message(embed=embed)
        await log(interaction, f"Debug Viewed settings for guild {guild_id}")

# DEBUG REMOVEPERM
    @app_commands.command()
    @is_dev()
    @app_commands.describe(roles="The roles to remove from permission roles.", server_id='The server to remove the roles from')
    async def removeperm(self, interaction: discord.Interaction, roles: Transform[List[Role], RoleTransformer], server_id: str = None):
        """Force remove roles from the permission roles."""
        guild_id = server_id if server_id else interaction.guild.id
        settings = get_guild_settings(guild_id)

        existing_roles = set(settings.perm_role_ids.split(",")) if settings.perm_role_ids else set()
        roles_to_remove = {str(role.id) for role in roles}
        updated_roles = existing_roles - roles_to_remove

        update_guild_settings(guild_id, perm_role_ids=",".join(updated_roles))
        await interaction.response.send_message(f"⚙️🔧✅ Removed permission roles: {', '.join(role.mention for role in roles)} for server {server_id}")
        await log(interaction, f"⚙️🔧✅ Removed permission roles: {', '.join(role.mention for role in roles)} for server {server_id}")

# DEBUG SETSKULLBOARD
    @app_commands.command()
    @app_commands.choices(status=[
        app_commands.Choice(name="Enable ", value="1"),
        app_commands.Choice(name="Disable", value="2")
    ])
    @is_dev()
    @app_commands.describe(channel="The channel to send skullboard messages to if enabled.")
    @app_commands.describe(status="Enable or disable the skullboard feature.")
    @app_commands.describe(server_id='The server to change settings for')
    async def setskullboard(self, interaction: discord.Interaction, status: app_commands.Choice[str], channel: discord.TextChannel = None, server_id: str = None):
        """Enable or disable the skullboard feature."""
        if status.value == "1" and not channel:
            await ctx.reply("❌ You must specify a channel when enabling Skullboard!", ephemeral=True)
            return

        server_id = server_id if server_id else interaction.guild.id

        skullboard_status = True if status.value == "1" else False

        update_guild_settings(server_id, skullboard_status=skullboard_status, skullboard_channel_id=channel.id if status.value == "1" else None)
        
        if status.value == "1":
            await interaction.response.send_message(f"✅ Skullboard enabled in {channel.mention} for {server_id}")
            await log(interaction, f"✅ Debug Skullboard enabled in {channel.mention} for {server_id}")
        else:
            await interaction.response.send_message(f"✅ Skullboard disabled for {server_id}")
            await log(interaction, f"✅ Debug Skullboard disabled for {server_id}")
   
# DEBUG GUILDS 
    @app_commands.command()
    @is_dev()
    async def guilds(self, interaction: discord.Interaction):
        """Sends paginated list of all guilds the bot is in."""
        guilds = interaction.client.guilds
        total_members = sum(g.member_count or 0 for g in guilds)

        embeds = []

        summary = Embed(title="Bot Summary", color=0xad7e66)
        summary.add_field(name="Total Guilds", value=len(guilds))
        summary.add_field(name="Total Members", value=total_members)
        summary.set_footer(text="Page 1")
        embeds.append(summary)

        for i, guild in enumerate(guilds, start=2):
            embed = Embed(title=guild.name, color=0xad7e66)
            embed.add_field(name="Guild ID", value=guild.id)
            embed.add_field(name="Members", value=guild.member_count or "Unknown")
            embed.add_field(name="Owner", value=str(guild.owner) if guild.owner else "Unknown")
            embed.set_footer(text=f"Page {i}")
            embeds.append(embed)

        view = PaginatorView(embeds, interaction.user.id)
        await interaction.response.send_message(embed=embeds[0], view=view)
        view.message = await interaction.original_response()

# DEBUG LEAVE_SERVER    
    @app_commands.command(name="leave_server", description="Force the bot to leave a server by ID (requires confirmation).")
    @is_dev()
    @app_commands.describe(guild_id='The guild to leave')
    async def leave_server(self, interaction: discord.Interaction, guild_id: str):
        bot = interaction.client

        guild = bot.get_guild(int(guild_id))
        if guild is None:
            return await interaction.response.send_message("❌ I'm not in a server with that ID.", ephemeral=True)

        confirm_code = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=10))
        await interaction.response.send_message(
            f"To confirm leaving **{guild.name}**, type this code below within 2 minutes:\n\n`{confirm_code}`",
            ephemeral=False
        )

        def message_check(msg: discord.Message):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id

        try:
            msg = await bot.wait_for("message", timeout=120.0, check=message_check)
            if msg.content.strip() != confirm_code:
                return await interaction.followup.send("❌ Incorrect confirmation code. Aborting.", ephemeral=True)

            try:
                await msg.delete()
            except discord.Forbidden:
                pass 

        except asyncio.TimeoutError:
            return await interaction.followup.send("❌ Timeout. No confirmation received.", ephemeral=True)

        orig = await interaction.original_response()
        confirm_msg = await orig.edit(
            content=f"Are you **sure** you want me to leave **{guild.name}**?\nReact with ✅ to confirm or ❌ to cancel."
        )
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        def reaction_check(reaction, user):
            return (
                user.id == interaction.user.id and
                reaction.message.id == confirm_msg.id and
                str(reaction.emoji) in ["✅", "❌"]
            )

        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=reaction_check)
            if str(reaction.emoji) == "✅":
                await confirm_msg.delete()
                leaving = await interaction.followup.send(f"✅ Leaving **{guild.name}**...", ephemeral=True)
                await guild.leave()
                await leaving.edit(content=f"🚪✅ | Successfully left **{guild.name}**")
                await log(interaction, f"I was forced to debug leave {guild.name} ({guild.id})")
            else:
                await interaction.followup.send("❌ Cancelled. Staying in the server.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("⌛ No reaction received. Aborting.", ephemeral=True)

# DEBUG GET_LOGS
    @app_commands.command(name="get_logs", description="Get logs for a user ID, guild ID, or a date (dd-mm-yyyy)")
    @is_dev()
    @app_commands.describe(
        user_id="User ID to search logs for",
        guild_id="Guild ID to search logs for",
        date="Date to search logs (format: dd-mm-yyyy)"
    )
    async def get_logs(self, interaction: discord.Interaction, user_id: str = None, guild_id: str = None, date: str = None):
        await interaction.response.defer(thinking=True)
        path = "logs/bot.log"

        try:
            async with aiofiles.open(path, mode='r') as f:
                lines = await f.readlines()
        except FileNotFoundError:
            await interaction.followup.send("Log file not found.")
            return

        results = []

        if date:
            results = [line for line in lines if line.startswith(f"[{date}")]
        elif user_id:
            results = [line for line in lines if f"USER: {user_id}" in line][-25:]
        elif guild_id:
            results = [line for line in lines if f"GUILD: {guild_id}" in line][-25:]
        else:
            results = lines[-25:]

        if not results:
            await interaction.followup.send("No matching log entries found.")
            return

        chunks = []
        chunk = ""
        for line in results:
            if len(chunk) + len(line) > 1900:
                chunks.append(chunk)
                chunk = ""
            chunk += line
        if chunk:
            chunks.append(chunk)

        for i, chunk in enumerate(chunks):
            await interaction.followup.send(f"```\n{chunk}\n```" if i == 0 else f"```{chunk}```")

# DEBUG ADDVOTECRATE
    @app_commands.command()
    @app_commands.describe(
        amount="Amount of votes crate to add",
        user="User to add the votes crate to",
        user_id="User ID to add the votes crate to (if not using @user)"
    )
    @is_dev()
    async def addvotecrate(self, interaction: discord.Interaction, amount: int, user: discord.Member = None, user_id: str = None):
        """Add votes crate to a user."""
        if not user_id and not user:
            await interaction.response.send_message("❌ User not found.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0.", ephemeral=True)
            return

        try:
            user_id = user_id if user_id else str(user.id)
            user = user if user else await self.bot.fetch_user(user_id)
            self.c.execute('SELECT moneh FROM moneh WHERE user_id = ?', (user_id,))
            row1 = self.c.fetchone()
            if row1:
                moneh = row1[0]
            else:
                moneh = 0
            new_moneh = moneh + amount
            self.c.execute(
                "INSERT INTO moneh (user_id, moneh) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET moneh = excluded.moneh",
                (str(user_id), new_moneh)
            )
            self.conn2.commit()
            await interaction.response.send_message(f"✅ Added {amount} votes crate to {user.mention}.", ephemeral=True)

        except sqlite3.Error as e:
            await interaction.response.send_message(f"❌ Database error: {e}", ephemeral=True)

# DEBUG EVAL
    @app_commands.command(name="eval", description="Evaluate Python code.")
    @is_dev()
    @app_commands.describe(code="The Python code to evaluate.")
    async def eval(self, interaction: discord.Interaction, code: str):
        """Evaluate Python code."""
        await interaction.response.defer(thinking=True, ephemeral=True)
        env = {
            "bot": self.bot,
            "discord": discord,
            "interaction": interaction,
            "self": self,
            "asyncio": asyncio,
            "random": random,
            "datetime": datetime,
        }
        # Dynamically add all subdirectories to sys.path
        base_dir = Path(__file__).parent.parent.resolve()
        for root, dirs, files in os.walk(base_dir):
            if "__pycache__" in root:
                continue
            if root not in sys.path:
                sys.path.append(root)
        # Import all .py files as modules and add their globals to env
        for file in base_dir.rglob("*.py"):
            if file.is_file() and not file.name.startswith("__"):
                try:
                    spec = importlib.util.spec_from_file_location(file.stem, file)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    for k, v in vars(mod).items():
                        if not k.startswith("__"):
                            env[k] = v
                except Exception:
                    pass  # Ignore import errors for now
        code = code.strip("` ")
        if code.startswith("py\n"):
            code = code[3:]
        # Async eval wrapper
        body = f"async def _eval_fn():\n    try:\n        return {code}\n    except Exception as e:\n        return e"
        try:
            exec(body, env)
            result = await env["_eval_fn"]()
        except Exception as e:
            result = e
        # Redact sensitive info
        result_str = str(result)
        for secret in (getattr(self.bot, "token", None),):
            if secret:
                result_str = result_str.replace(secret, "[REDACTED]")
        # Truncate if too long
        if len(result_str) > 1900:
            result_str = result_str[:1900] + "..."
        await interaction.followup.send(f"```py\n{result_str}\n```", ephemeral=True)

async def setup(bot):
    bot.tree.add_command(Debug(bot))