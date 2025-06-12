from urllib.parse import quote
import discord
from discord import app_commands
from functions import *
import sqlite3
import requests
from bs4 import BeautifulSoup

# VERIFY
conn = sqlite3.connect(DATA_DIR / "verifications.db")
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

    def __init__(self, bot):
        super().__init__(name="verify", description="Verification system commands.")
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensures commands in this group only run in a specific guild."""
        if interaction.guild and interaction.guild.id == 1368978029056888943:
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
        if 1368979168972378262 not in [role.id for role in interaction.user.roles]:
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
                    await self.bot.get_channel(1368992082680610826).send(
                        f"{interaction.user.mention} ({interaction.user.name}) used /verify but the profile name they entered ({gc_username}) doesn't exist."
                    )
                else:
                    message = await self.bot.get_channel(1369366515853299712).send(
                        f"{interaction.user.mention} has requested verification for username: {gc_username}. Verification ID: will be provided shortly."
                    )

                    cursor.execute(
                        "INSERT INTO verifications (user_id, gc_username, message_id) VALUES (?, ?, ?)",
                        (interaction.user.id, gc_username, message.id)
                    )
                    conn.commit()

                    verification_id = cursor.lastrowid
                    await message.edit(content=f"{interaction.user.mention} has requested verification for username: {gc_username}. Verification ID: {verification_id}.\nProfile Link: https://www.geocaching.com/p/?u={quote(gc_username)}")
                    await interaction.response.send_message(
                        "Your request has been submitted for review. Your verification ID is `{}`. A member of staff will review it soon.".format(verification_id),
                        ephemeral=True
                    )
            else:
                await self.bot.get_channel(1368992082680610826).send(
                    f"{interaction.user.mention} ({interaction.user.name}) used /verify <{gc_username}> and encountered an error: Failed to fetch the page. HTTP status code: {response.status_code}. It could mean the profile doesn't exist, or it could be something else."
                )
                await interaction.response.send_message(
                    f"The username you entered does not exist, or there was an error. Please re-verify with the correct username, or contact an Admin.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already verified. If your nickname is NOT your Geocaching username, please contact Staff.", ephemeral=True)
            await self.bot.get_channel(1368992082680610826).send(f"{interaction.user.mention} tried to use /verify {gc_username} but they're already verified.")

    # VERIFY APPROVE
    @app_commands.command(name="approve", description="Approve a verification request.")
    @app_commands.describe(verification_id="The ID of the verification request to approve.")
    @is_moderator()
    async def approve(self, interaction: discord.Interaction, verification_id: int):
        await interaction.response.defer(thinking=True, ephemeral=True)
        cursor.execute("SELECT user_id, gc_username, message_id FROM verifications WHERE id = ?", (verification_id,))
        row = cursor.fetchone()

        if row:
            user_id, gc_username, message_id = row
            guild = interaction.guild
            member = guild.get_member(user_id)
            role = guild.get_role(1368979168972378262)

            if member:
                await member.add_roles(role)
                await member.remove_roles(guild.get_role(1373671098813517875))
                await member.edit(nick=gc_username)

                await member.send(
                    f"Congratulations, {gc_username} - You have been verified! Your nickname has been updated, and you now have access to the rest of the server."
                )

                await self.bot.get_channel(1368992082680610826).send(
                    f"{member.mention} has been verified by {interaction.user.mention} ({interaction.user.name}) with username {gc_username}."
                )

                try:
                    channel = self.bot.get_channel(1369366515853299712)
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                except Exception as e:
                    await log_error(guild, self.bot, "verify", f"Error deleting message: {e}")

                cursor.execute("DELETE FROM verifications WHERE id = ?", (verification_id,))
                conn.commit()
                await interaction.followup.send(f"Verification ID {verification_id} with username {gc_username} has been approved.")
            else:
                await interaction.followup.send("The user is no longer in the server.", ephemeral=True)
        else:
            await interaction.followup.send("Invalid verification ID.", ephemeral=True)

    @approve.error
    async def approve_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return
        else:
            raise error  

    # VERIFY DENY
    @app_commands.command(name="deny", description="Deny a verification request.")
    @app_commands.describe(verification_id="The ID of the verification request to deny.", reason="The reason for denial.")
    @is_moderator()
    async def deny(self, interaction: discord.Interaction, verification_id: int, reason: str):
        await interaction.response.defer(thinking=True)
        cursor.execute("SELECT user_id, gc_username, message_id FROM verifications WHERE id = ?", (verification_id,))
        row = cursor.fetchone()

        if row:
            user_id, gc_username, message_id = row
            member = interaction.guild.get_member(user_id)

            if member:
                await member.send(
                    f"Your verification request has been denied for the following reason:\n\n{reason}"
                )

                await self.bot.get_channel(1368992082680610826).send(
                    f"{member.mention}'s verification request with username {gc_username} has been denied by {interaction.user.mention} ({interaction.user.name}). Reason: {reason}"
                )

                try:
                    channel = self.bot.get_channel(1369366515853299712)
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                except Exception as e:
                    await log_error(interaction.guild, self.bot, "verify", f"Error deleting message: {e}")

                cursor.execute("DELETE FROM verifications WHERE id = ?", (verification_id,))
                conn.commit()
                await interaction.followup.send(f"Verification ID {verification_id} has been denied.", ephemeral=True)
            else:
                await interaction.followup.send("The user is no longer in the server.", ephemeral=True)
        else:
            await interaction.followup.send("Invalid verification ID.", ephemeral=True)

    @deny.error
    async def deny_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return
        else:
            raise error 

    # VERIFY MUGGLE
    @app_commands.command(name="muggle", description="Assign yourself the Muggle role.")
    async def muggle(self, interaction: discord.Interaction):
        if 1368979168972378262 not in [role.id for role in interaction.user.roles]:
            role = interaction.guild.get_role(1368999968215400478)
            if role:
                await interaction.user.add_roles(role)
                await interaction.user.remove_roles(interaction.guild.get_role(1368979168972378262))
                await interaction.user.remove_roles(interaction.guild.get_role(1373671098813517875))
                await interaction.response.send_message("You have been assigned the Muggle role.", ephemeral=True)
                await self.bot.get_channel(1368992082680610826).send(
                    f"{interaction.user.mention} has used /muggle and was assigned the Muggle role."
                )
            else:
                await interaction.response.send_message("Muggle role not found. Please contact an admin.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already verified and cannot assign yourself the Muggle role.", ephemeral=True)

    # VERIFY BYPASS
    @app_commands.command(name="bypass", description="You do not want to show your nickname. Verify via this.")
    async def quickverify(self, interaction: discord.Interaction):
        if 1368979168972378262 not in [role.id for role in interaction.user.roles]:
            role = interaction.guild.get_role(1368979168972378262)
            if role:
                await interaction.user.add_roles(role)
                await interaction.user.edit(nick=f"{interaction.user.display_name} [VB]")
                await interaction.response.send_message("You have been verified. We highly suggest you use a nickname to verify since otherwise you cannot use commands like /badgebar, /statbar and more without entering fields manually.", ephemeral=True)
                await self.bot.get_channel(1368992082680610826).send(
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
        role_id_to_check = 1368979168972378262 
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

    @unverified.error
    async def unverified_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return
        else:
            raise error 

    # VERIFY MANUAL
    @app_commands.command()
    @is_moderator()
    @app_commands.describe(user="The user to verify", gc_name="The Geocaching username of the user")
    async def manual(self, interaction: discord.Interaction, user: discord.Member, gc_name: str):
        """Manually verify a user."""
        if 1368979168972378262 in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("That user already verified.", ephemeral=True)
        else:
            role1 = interaction.guild.get_role(1368979168972378262)
            if role1:
                await user.add_roles(role1)
                await user.edit(nick=gc_name)
                await interaction.response.send_message(f"{user.mention} has been manually verified with username {gc_name}.")
                await self.bot.get_channel(1368992082680610826).send(f"{interaction.user.mention} ({interaction.user.name}) has manually verified {user.mention} with username {gc_name}.")
            else:
                await interaction.response.send_message("Verification role not found. Please contact an admin.", ephemeral=True)

    @manual.error
    async def manual_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return
        else:
            raise error 

async def setup(bot):
    bot.tree.add_command(Verification(bot))
