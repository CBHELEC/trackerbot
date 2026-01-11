import discord
import requests
from discord import app_commands
from functions import static_var, logs
from urllib.parse import quote
from bs4 import BeautifulSoup
from verifydb import *
from database import *

class Verification(app_commands.Group):
    """Commands for the verification system."""

    def __init__(self, bot):
        super().__init__(name="verify", description="Verification system commands.")
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensures commands in this group only run when verification is enabled."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return False
            
        guildsettings = get_guild_settings(interaction.guild.id)
        verification_enabled = bool(guildsettings.verification_status) if hasattr(guildsettings, 'verification_status') and guildsettings.verification_status is not None else False
        
        if not verification_enabled:
            await interaction.response.send_message(
                "Verification is currently disabled for this server. Please ask an administrator to enable it in the dashboard.",
                ephemeral=True
            )
            return False
        
        return True

    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Shows all of the verification commands."""
        embed = discord.Embed(title="Verification Commands",
                            colour=0xad7e66)

        embed.add_field(name="Everyone:",
                        value="</verify verify:1327423499089874956> - Verify your Geocaching profile.\n</verify muggle:1327423499089874956> - Assign yourself the Muggle role.\n</verify bypass:1327423499089874956> - You do not want to show your nickname. Verify via this.",
                        inline=False)
        embed.add_field(name="Staff Only:",
                        value="</verify approve:1327423499089874956> - Approve a verification request.\n</verify deny:1327423499089874956> - Deny a verification request.\n</verify unverified:1327423499089874956> - Sends a list of unverified members.\n</verify manual:1327423499089874956> - Manually verify a user.",
                        inline=False)

        await interaction.response.send_message(embed=embed)

    # VERIFY START
    @app_commands.command(name="start", description="Verify your Geocaching profile.")
    @app_commands.describe(gc_username="The username of your Geocaching account")
    async def start(self, interaction: discord.Interaction, gc_username: str):
        guildsettings = get_guild_settings(interaction.guild.id)
        
        if await has_pending_verification(interaction.guild.id, interaction.user.id):
            await interaction.response.send_message(
                "You already have a pending verification request. Please wait for it to be reviewed by staff, or contact a moderator if you need to update it.",
                ephemeral=True
            )
            return

        already_verified = guildsettings.verify_verified_role_id in [role.id for role in interaction.user.roles]
        
        differentname = False
        existing_record = None
        try:
            existing_record = await find_gc_username(interaction.user.id, exclude_guild_id=interaction.guild.id)
        except Exception as e:
            pass
        
        if existing_record and not already_verified:
            if gc_username.lower() != existing_record.lower():
                differentname = True
            else:
                fasttrack_enabled = bool(guildsettings.verify_fasttrack_status)
                if fasttrack_enabled:
                    await interaction.response.defer(thinking=True, ephemeral=True)
                    
                    guild = interaction.guild
                    member = guild.get_member(interaction.user.id)
                    if member is None:
                        try:
                            member = await guild.fetch_member(interaction.user.id)
                        except (discord.NotFound, discord.HTTPException):
                            member = interaction.user
                    
                    role = guild.get_role(guildsettings.verify_verified_role_id)
                    if not role:
                        await interaction.followup.send("Verification role not found. Please contact a server Administrator.", ephemeral=True)
                        return
                    
                    try:
                        bot_member = await guild.fetch_member(self.bot.user.id)
                    except (discord.NotFound, discord.HTTPException):
                        await interaction.followup.send("Bot member not found. Please contact a server Administrator.", ephemeral=True)
                        return
                    
                    bot_perms = bot_member.guild_permissions
                    if not bot_perms.manage_roles:
                        await interaction.followup.send(
                            "❌ The bot does not have the 'Manage Roles' permission. Please grant this permission to the bot and try again.",
                            ephemeral=True
                        )
                        return
                    
                    if not bot_perms.manage_nicknames:
                        await interaction.followup.send(
                            "❌ The bot does not have the 'Manage Nicknames' permission. Please grant this permission to the bot and try again.",
                            ephemeral=True
                        )
                        return
                    
                    bot_top_role = bot_member.top_role
                    if role >= bot_top_role:
                        await interaction.followup.send(
                            f"❌ The verification role ({role.mention}) is higher than or equal to the bot's highest role ({bot_top_role.mention}). "
                            "Please move the bot's role above the verification role in the server's role hierarchy.",
                            ephemeral=True
                        )
                        return
                    
                    if role.managed:
                        await interaction.followup.send(
                            f"❌ The verification role ({role.mention}) is managed by an integration and cannot be assigned by the bot. "
                            "Please use a different role that is not managed.",
                            ephemeral=True
                        )
                        return
                    
                    if role == guild.default_role:
                        await interaction.followup.send(
                            "❌ Cannot use the @everyone role as a verification role. Please select a different role.",
                            ephemeral=True
                        )
                        return
                    
                    unverified_role = guild.get_role(guildsettings.verify_unverified_role_id)
                    
                    try:
                        if role not in member.roles:
                            await member.add_roles(role, reason=f"Fasttrack verification - previously verified on another server")
                        
                        if unverified_role and unverified_role in member.roles and unverified_role < bot_top_role:
                            await member.remove_roles(unverified_role, reason="User verified via fasttrack")
                        
                        await member.edit(nick=gc_username, reason="Fasttrack verification nickname update")
                        
                        verification_id = await add_verification(interaction.guild.id, interaction.user.id, 0, gc_username)
                        await update_verification_status(interaction.guild.id, verification_id, "approved")
                        
                        await interaction.followup.send(
                            f"✅ You have been automatically verified! Your username `{gc_username}` matched a previous verification on another server. "
                            "Your nickname has been updated and you now have access to the rest of the server.",
                            ephemeral=True
                        )
                        
                        channel = self.bot.get_channel(guildsettings.verify_channel_id)
                        if channel:
                            await channel.send(
                                f"{member.mention} used `/verify {gc_username}` and their username matched a previous verification, so they have been automatically verified via fasttrack.\n"
                                f"⛔ **NOTICE: To disable verification fasttracking, please get the Owner, or anyone with the Administrator or Manage Server permission to follow the steps [by clicking here](<https://docs.trackerbot.xyz/configuration/verification#disable-fasttrack>).**"
                            )
                        
                        try:
                            await member.send(
                                f"Congratulations, {gc_username} - You have been automatically verified via fasttrack! "
                                "Your username matched a previous verification on another server. Your nickname has been updated, and you now have access to the rest of the server."
                            )
                        except discord.Forbidden:
                            pass 
                            
                    except discord.Forbidden as e:
                        await interaction.followup.send(
                            f"❌ Missing Permissions: The bot cannot manage roles. Error: {str(e)}\n\n"
                            "Please ensure:\n"
                            "1. The bot has the 'Manage Roles' permission\n"
                            "2. The bot's role is above the verification role in the role hierarchy\n"
                            "3. The bot has the 'Manage Nicknames' permission",
                            ephemeral=True
                        )
                        return
                    except discord.HTTPException as e:
                        await interaction.followup.send(
                            f"❌ Error managing roles: {str(e)}. Please contact a server Administrator.",
                            ephemeral=True
                        )
                        return
                    except Exception as e:
                        await interaction.followup.send(
                            f"❌ An unexpected error occurred during fasttrack verification: {str(e)}. Please contact a server Administrator.",
                            ephemeral=True
                        )
                        return
                    
                    return  

        if guildsettings.verify_verified_role_id not in [role.id for role in interaction.user.roles]:
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
                    channel = self.bot.get_channel(guildsettings.verify_channel_id)
                    if channel:
                        await channel.send(
                            f"{interaction.user.mention} ({interaction.user.name}) used /verify but the profile name they entered ({gc_username}) doesn't exist."
                        )
                else:
                    messagetext = f"{interaction.user.mention} has requested verification for username: {gc_username}. Verification ID: will be provided shortly."
                    if differentname:
                        messagetext = messagetext + "\n⚠️ **WARNING: They have been verified on another server, but with a different username.**"
                    channel = self.bot.get_channel(guildsettings.verify_channel_id)
                    if not channel:
                        await interaction.response.send_message("Verification channel not found. Please contact an administrator.", ephemeral=True)
                        return
                    message = await channel.send(messagetext)

                    verification_id = await add_verification(interaction.guild.id, interaction.user.id, message.id, gc_username)

                    editmessagetext = f"{interaction.user.mention} has requested verification for username: {gc_username}. Verification ID: {verification_id}.\nProfile Link: <https://www.geocaching.com/p/?u={quote(gc_username)}>"
                    if differentname:
                        editmessagetext = editmessagetext + "\n⚠️ **WARNING: They have been verified on another server, but with a different username.**"
                    await message.edit(content=editmessagetext)
                    await interaction.response.send_message(
                        "Your request has been submitted for review. Your verification ID is `{}`. A member of staff will review it soon.".format(verification_id),
                        ephemeral=True
                    )
            else:
                channel = self.bot.get_channel(guildsettings.verify_channel_id)
                if channel:
                    await channel.send(
                        f"{interaction.user.mention} ({interaction.user.name}) used /verify <{gc_username}> and encountered an error: the profile may not exist, or it could be something else."
                    )
                await interaction.response.send_message(
                    f"The username you entered does not exist, or there was an error. Please re-verify with the correct username, or create a </misc suggest_report:1419276756874952828>.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already verified. If your nickname is NOT your Geocaching username, please contact the server's Staff.", ephemeral=True)
            channel = self.bot.get_channel(guildsettings.verify_channel_id)
            if channel:
                await channel.send(f"{interaction.user.mention} tried to use /verify {gc_username} but they're already verified.")

    # VERIFY APPROVE
    @app_commands.command(name="approve", description="Approve a verification request.")
    @app_commands.describe(verification_id="The ID of the verification request to approve.")
    async def approve(self, interaction: discord.Interaction, verification_id: int):
        guildsettings = get_guild_settings(interaction.guild.id)
        if isinstance(guildsettings.verify_admin_role_id, str):
            validroles = {int(role) for role in guildsettings.verify_admin_role_id.split(",") if role.strip()}
        elif isinstance(guildsettings.verify_admin_role_id, int):
            validroles = {guildsettings.verify_admin_role_id}
        else:
            validroles = set()
        has_permission = (
            any(role.id in validroles for role in interaction.user.roles) or
            interaction.user.guild_permissions.administrator or
            interaction.user.guild_permissions.manage_guild
        )
        if not has_permission:
            await interaction.response.send_message(embed=static_var.YOUCANTDOTHIS, ephemeral=True)
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        verification_instance = await fetch_verification(interaction.guild.id, verification_id)

        if verification_instance:
            message_id = verification_instance['message_id']
            gc_username = verification_instance['gc_username']
            guild = interaction.guild
            member = guild.get_member(verification_instance['user_id'])
            if member is None:
                try:
                    member = await guild.fetch_member(verification_instance['user_id'])
                except discord.NotFound:
                    await interaction.followup.send("User not found in server.", ephemeral=True)
                    return
                except discord.HTTPException as e:
                    member = guild.get_member(verification_instance['user_id'])
                    if member is None:
                        await interaction.followup.send(
                            f"Unable to fetch user information. This may be due to missing Members intent or network issues. "
                            f"Error: {str(e)}. Please ensure the bot has the Members intent enabled if you want to verify users who aren't in the cache.",
                            ephemeral=True
                        )
                        return
            
            if member is None:
                await interaction.followup.send("User not found in server.", ephemeral=True)
                return
            
            role = guild.get_role(guildsettings.verify_verified_role_id)
            if not role:
                await interaction.followup.send("Verification role not found. Please contact a server Administrator.", ephemeral=True)
                return
            
            try:
                bot_member = await guild.fetch_member(self.bot.user.id)
            except (discord.NotFound, discord.HTTPException):
                await interaction.followup.send("Bot member not found. Please contact a server Administrator.", ephemeral=True)
                return
            
            bot_perms = bot_member.guild_permissions
            if not bot_perms.manage_roles:
                await interaction.followup.send(
                    "❌ The bot does not have the 'Manage Roles' permission. Please grant this permission to the bot and try again.",
                    ephemeral=True
                )
                return
            
            if not bot_perms.manage_nicknames:
                await interaction.followup.send(
                    "❌ The bot does not have the 'Manage Nicknames' permission. Please grant this permission to the bot and try again.",
                    ephemeral=True
                )
                return
            
            bot_top_role = bot_member.top_role
            if role >= bot_top_role:
                await interaction.followup.send(
                    f"❌ The verification role ({role.mention}) is higher than or equal to the bot's highest role ({bot_top_role.mention}). "
                    "Please move the bot's role above the verification role in the server's role hierarchy.",
                    ephemeral=True
                )
                return
            
            if role.managed:
                await interaction.followup.send(
                    f"❌ The verification role ({role.mention}) is managed by an integration and cannot be assigned by the bot. "
                    "Please use a different role that is not managed.",
                    ephemeral=True
                )
                return
            
            if role == guild.default_role:
                await interaction.followup.send(
                    "❌ Cannot use the @everyone role as a verification role. Please select a different role.",
                    ephemeral=True
                )
                return
            
            if role in member.roles:
                unverified_role = guild.get_role(guildsettings.verify_unverified_role_id)
                try:
                    if unverified_role and unverified_role in member.roles and unverified_role < bot_top_role:
                        await member.remove_roles(unverified_role)
                    await member.edit(nick=gc_username)
                except discord.Forbidden as e:
                    await interaction.followup.send(
                        f"❌ Missing Permissions: {str(e)}",
                        ephemeral=True
                    )
                    return
                except discord.HTTPException as e:
                    await interaction.followup.send(
                        f"❌ Error: {str(e)}",
                        ephemeral=True
                    )
                    return
            else:
                unverified_role = guild.get_role(guildsettings.verify_unverified_role_id)
                
                try:
                    await member.add_roles(role, reason=f"Verification approved by {interaction.user}")
                    if unverified_role and unverified_role in member.roles and unverified_role < bot_top_role:
                        await member.remove_roles(unverified_role, reason="User verified")
                    await member.edit(nick=gc_username, reason="Verification nickname update")
                except discord.Forbidden as e:
                    error_details = []
                    error_details.append(f"**Error Code:** {e.code if hasattr(e, 'code') else 'Unknown'}")
                    error_details.append(f"**Error Message:** {str(e)}")
                    error_details.append(f"**Role:** {role.name} (ID: {role.id})")
                    error_details.append(f"**Role Managed:** {role.managed}")
                    error_details.append(f"**Bot Top Role:** {bot_top_role.name} (ID: {bot_top_role.id})")
                    error_details.append(f"**Bot Has Manage Roles:** {bot_perms.manage_roles}")
                    error_details.append(f"**Bot Has Manage Nicknames:** {bot_perms.manage_nicknames}")
                    error_details.append(f"**Role Hierarchy Check:** {role < bot_top_role}")
                    
                    await interaction.followup.send(
                        f"❌ **Missing Permissions Error**\n\n"
                        f"{chr(10).join(error_details)}\n\n"
                        "**Possible Solutions:**\n"
                        "1. Ensure the bot's role is **above** the verification role in Server Settings → Roles\n"
                        "2. Ensure the verification role is **not managed** by another bot/integration\n"
                        "3. Ensure the bot has 'Manage Roles' and 'Manage Nicknames' permissions\n"
                        "4. Try using a different role that is not managed",
                        ephemeral=True
                    )
                    return
                except discord.HTTPException as e:
                    await interaction.followup.send(
                        f"❌ Error managing roles: {str(e)}. Please contact a server Administrator.",
                        ephemeral=True
                    )
                    return

            try:
                await member.send(
                    f"Congratulations, {gc_username} - You have been verified! Your nickname has been updated, and you now have access to the rest of the server."
                )
            except discord.Forbidden:
                pass

            channel = self.bot.get_channel(guildsettings.verify_channel_id)
            if channel:
                await channel.send(
                    f"{member.mention} has been verified by {interaction.user.mention} ({interaction.user.name}) with username {gc_username}."
                )

            try:
                if channel:
                    message = await channel.fetch_message(message_id)
                    await message.delete()
            except Exception as e:
                await logs.log_error(guild, self.bot, "verify", f"Error deleting message: {e}")

            await update_verification_status(interaction.guild.id, verification_id, "approved")

            await interaction.followup.send(f"Verification ID {verification_id} with username {gc_username} has been approved.")
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
    async def deny(self, interaction: discord.Interaction, verification_id: int, reason: str):
        guildsettings = get_guild_settings(interaction.guild.id)
        if isinstance(guildsettings.verify_admin_role_id, str):
            validroles = {int(role) for role in guildsettings.verify_admin_role_id.split(",") if role.strip()}
        elif isinstance(guildsettings.verify_admin_role_id, int):
            validroles = {guildsettings.verify_admin_role_id}
        else:
            validroles = set()
        has_permission = (
            any(role.id in validroles for role in interaction.user.roles) or
            interaction.user.guild_permissions.administrator or
            interaction.user.guild_permissions.manage_guild
        )
        if not has_permission:
            await interaction.response.send_message(embed=static_var.YOUCANTDOTHIS, ephemeral=True)
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        verification_instance = await fetch_verification(interaction.guild.id, verification_id)

        if verification_instance:
            message_id = verification_instance['message_id']
            gc_username = verification_instance['gc_username']
            guild = interaction.guild
            member = guild.get_member(verification_instance['user_id'])
            if member is None:
                try:
                    member = await guild.fetch_member(verification_instance['user_id'])
                except discord.NotFound:
                    await interaction.followup.send("User not found in server.", ephemeral=True)
                    return
                except discord.HTTPException as e:
                    member = guild.get_member(verification_instance['user_id'])
                    if member is None:
                        await interaction.followup.send(
                            f"Unable to fetch user information. This may be due to missing Members intent or network issues. "
                            f"Error: {str(e)}. Please ensure the bot has the Members intent enabled if you want to verify users who aren't in the cache.",
                            ephemeral=True
                        )
                        return
            
            if member:
                try:
                    await member.send(
                        f"Your verification request has been denied for the following reason:\n\n{reason}"
                    )
                except discord.Forbidden:
                    pass

                channel = self.bot.get_channel(guildsettings.verify_channel_id)
                if channel:
                    await channel.send(
                        f"{member.mention}'s verification request with username {gc_username} has been denied by {interaction.user.mention} ({interaction.user.name}). Reason: {reason}"
                    )

                try:
                    if channel:
                        message = await channel.fetch_message(message_id)
                        await message.delete()
                except Exception as e:
                    await logs.log_error(interaction.guild, self.bot, "verify", f"Error deleting message: {e}")

                await update_verification_status(interaction.guild.id, verification_id, "denied")

                await interaction.followup.send(f"Verification ID {verification_id} has been denied.")
            else:
                await interaction.followup.send("The user is no longer in the server.")
        else:
            await interaction.followup.send("Invalid verification ID.")

    @deny.error
    async def deny_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return
        else:
            raise error 

    # VERIFY MUGGLE
    @app_commands.command(name="muggle", description="Assign yourself the Muggle role.")
    async def muggle(self, interaction: discord.Interaction):
        guildsettings = get_guild_settings(interaction.guild.id)
        if guildsettings.verify_verified_role_id not in [role.id for role in interaction.user.roles]:
            role = interaction.guild.get_role(guildsettings.verify_muggle_role_id)
            if role:
                await interaction.user.add_roles(role)
                verified_role = interaction.guild.get_role(guildsettings.verify_verified_role_id)
                if verified_role:
                    await interaction.user.remove_roles(verified_role)
                unverified_role = interaction.guild.get_role(guildsettings.verify_unverified_role_id)
                if unverified_role:
                    await interaction.user.remove_roles(unverified_role)
                await interaction.response.send_message("You have been assigned the Muggle role.", ephemeral=True)
                channel = self.bot.get_channel(guildsettings.verify_channel_id)
                if channel:
                    await channel.send(
                        f"{interaction.user.mention} has used /muggle and was assigned the Muggle role."
                    )
            else:
                await interaction.response.send_message("Muggle role not found. Please contact an Admin.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already verified and cannot assign yourself the Muggle role.", ephemeral=True)

    # VERIFY BYPASS
    @app_commands.command(name="bypass", description="You do not want to show your nickname. Verify via this.")
    async def quickverify(self, interaction: discord.Interaction):
        guildsettings = get_guild_settings(interaction.guild.id)
        if guildsettings.verify_verified_role_id not in [role.id for role in interaction.user.roles]:
            role = interaction.guild.get_role(guildsettings.verify_verified_role_id)
            if role:
                await interaction.user.add_roles(role)
                await interaction.user.edit(nick=f"{interaction.user.display_name} [VB]")
                await interaction.response.send_message("You have been verified. We highly suggest you use a nickname to verify since otherwise you cannot use commands like /badgebar, /statbar and more without entering fields manually.", ephemeral=True)
                channel = self.bot.get_channel(guildsettings.verify_channel_id)
                if channel:
                    await channel.send(
                        f"{interaction.user.mention} has been verified without a username."
                    )
            else:
                await interaction.response.send_message("Verification role not found. Please contact an admin.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already verified.", ephemeral=True)

    # UNVERIFIED
    @app_commands.command()
    async def unverified(self, interaction: discord.Interaction):
        """Fetch a list of unverified members."""
        embed = discord.Embed(
            title="Unverified Users",
            colour=0xad7e66,
            description="This command had to be removed due to various Discord Limitations.\nInstead, please go to Server Settings → Roles → Unverified and click 'Members' to see a list of unverified members."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @unverified.error
    async def unverified_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return
        else:
            raise error 

    # VERIFY MANUAL
    @app_commands.command()
    @app_commands.describe(user="The user to verify", gc_name="The Geocaching username of the user")
    async def manual(self, interaction: discord.Interaction, user: discord.Member, gc_name: str):
        """Manually verify a user."""
        guildsettings = get_guild_settings(interaction.guild.id)
        if isinstance(guildsettings.verify_admin_role_id, str):
            validroles = {int(role) for role in guildsettings.verify_admin_role_id.split(",") if role.strip()}
        elif isinstance(guildsettings.verify_admin_role_id, int):
            validroles = {guildsettings.verify_admin_role_id}
        else:
            validroles = set()
        has_permission = (
            any(role.id in validroles for role in interaction.user.roles) or
            interaction.user.guild_permissions.administrator or
            interaction.user.guild_permissions.manage_guild
        )
        if not has_permission:
            await interaction.response.send_message(embed=static_var.YOUCANTDOTHIS, ephemeral=True)
            return

        if guildsettings.verify_verified_role_id in [role.id for role in user.roles]:
            await interaction.response.send_message("That user already verified.", ephemeral=True)
        else:
            role1 = interaction.guild.get_role(guildsettings.verify_verified_role_id)
            if not role1:
                await interaction.response.send_message("Verification role not found. Please contact a server Administrator.", ephemeral=True)
                return
            
            try:
                bot_member = await interaction.guild.fetch_member(self.bot.user.id)
            except (discord.NotFound, discord.HTTPException):
                await interaction.response.send_message("Bot member not found. Please contact a server Administrator.", ephemeral=True)
                return
            
            bot_perms = bot_member.guild_permissions
            if not bot_perms.manage_roles:
                await interaction.response.send_message(
                    "❌ The bot does not have the 'Manage Roles' permission. Please grant this permission to the bot and try again.",
                    ephemeral=True
                )
                return
            
            if not bot_perms.manage_nicknames:
                await interaction.response.send_message(
                    "❌ The bot does not have the 'Manage Nicknames' permission. Please grant this permission to the bot and try again.",
                    ephemeral=True
                )
                return
            
            bot_top_role = bot_member.top_role
            if role1 >= bot_top_role:
                await interaction.response.send_message(
                    f"❌ The verification role ({role1.mention}) is higher than or equal to the bot's highest role ({bot_top_role.mention}). "
                    "Please move the bot's role above the verification role in the server's role hierarchy.",
                    ephemeral=True
                )
                return
            
            try:
                await user.add_roles(role1)
                await user.edit(nick=gc_name)
                await interaction.response.send_message(f"{user.mention} has been manually verified with username {gc_name}.")
                channel = self.bot.get_channel(guildsettings.verify_channel_id)
                if channel:
                    await channel.send(f"{interaction.user.mention} ({interaction.user.name}) has manually verified {user.mention} with username {gc_name}.")
            except discord.Forbidden as e:
                await interaction.response.send_message(
                    f"❌ Missing Permissions: The bot cannot manage roles. Error: {str(e)}\n\n"
                    "Please ensure:\n"
                    "1. The bot has the 'Manage Roles' permission\n"
                    "2. The bot's role is above the verification role in the role hierarchy\n"
                    "3. The bot has the 'Manage Nicknames' permission",
                    ephemeral=True
                )
            except discord.HTTPException as e:
                await interaction.response.send_message(
                    f"❌ Error managing roles: {str(e)}. Please contact a server Administrator.",
                    ephemeral=True
                )

    @manual.error
    async def manual_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            return
        else:
            raise error 

async def setup(bot):
    bot.tree.add_command(Verification(bot))
