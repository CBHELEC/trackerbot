import discord
import asyncio
import sqlite3
import re
from discord import app_commands
from discord.ui import View, Button
from functions import *
from bot import bot
from datetime import datetime
from logger import log
from discord.app_commands import CheckFailure

conn1 = sqlite3.connect(DATA_DIR / "trackables.db")
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

    cursor1.execute("PRAGMA table_info(trackables)")
    columns = [column[1] for column in cursor1.fetchall()]
    
    if "code" not in columns:
        cursor1.execute("""
        DROP TABLE IF EXISTS trackables;
        """)
        cursor1.execute("""
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
                cursor1.execute("""ALTER TABLE trackables ADD COLUMN user_id INTEGER NOT NULL""")
            elif column == "username":
                cursor1.execute("""ALTER TABLE trackables ADD COLUMN gc_username TEXT NOT NULL""")
            elif column == "code":
                cursor1.execute("""ALTER TABLE trackables ADD COLUMN code TEXT PRIMARY_KEY NOT NULL""")
            elif column == "uploaded_time":
                cursor1.execute("""ALTER TABLE trackables ADD COLUMN uploaded_time TIMESTAMP CURRENT_TIMESTAMP""")
            elif column == "tb_code":
                cursor1.execute("""ALTER TABLE trackables ADD COLUMN tb_code TEXT NOT NULL""")

    conn1.commit()

class TBRemoveConfirmView(View):
    def __init__(self, code: str, user_id: int):
        super().__init__(timeout=60)
        self.code = code
        self.user_id = user_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return

        try:
            cursor1.execute("DELETE FROM trackables WHERE code = ?", (self.code,))
            conn1.commit()
            await interaction.response.edit_message(content=f"TB `{self.code}` has been removed from the database.", view=None)
            await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) has removed TB `{self.code}` from the database.")
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"An error occurred while trying to remove the TB. The Dev has been notified.", ephemeral=True)
            else:
                await interaction.followup.send(f"An error occurred while trying to remove the TB. The Dev has been notified.", ephemeral=True)
            await log_error(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to remove TB `{self.code}`. Error: {e}")

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return

        await interaction.response.edit_message(content="Removal cancelled.", view=None)
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

class TBOwnershipConfirmView(View):
    def __init__(self, user_id: int, callback, codes: list = None, single_code: str = None):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.callback = callback
        self.codes = codes
        self.single_code = single_code

    @discord.ui.button(label="I own this/these TB(s)", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return
        
        await interaction.response.edit_message(content="Confirmation received! Processing...", view=None)
        await self.callback(interaction)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return

        await interaction.response.edit_message(content="Addition cancelled.", view=None)
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

class TBDatabase(app_commands.Group):
    """Commands for the public TB database."""
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """User Blacklist Check."""
        users = os.getenv("TB_BLACKLIST").split(",")
        if str(interaction.user.id) in users:
            raise CheckFailure("TB_BLACKLIST")
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if isinstance(error, CheckFailure) and str(error) == "TB_BLACKLIST":
            devid = os.getenv("DEV_USER_ID")
            msg = f"You have been blacklisted from using the TB database commands. To discuss this, please DM <@{devid}>."
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return
        raise error

# TB HELP
    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Shows all of the public TB database commands."""
        embed = discord.Embed(title="Public TB Database",
                            colour=0xad7e66)

        embed.add_field(name="Everyone:",
                        value="/tb add <code> - Adds a TB to the public database.\n\n/tb bulkadd - Bulk adds TBs to the public database as long as they are separated.\n⮡   They MUST be separated via eg. space, comma etc.\n\n/tb remove - Removes a TB from the public database.\n⮡   You MUST contact the Dev to get it removed.\n\n/tb view - Shows the public TB database.\n⮡   Shows 5 codes in one embed. You must use the pagination buttons to move to the next page, if there is one.\n\n/tb bulkview - Sends all codes in the public TB database to your DMs.\n⮡   DMs you ALL codes in one message. They are separated by commas, so they are suitable for [logthemall](<https://www.logthemall.org/>) or the [PGC trackable tool](<https://project-gc.com/Tools/DiscoverTrackables>).",
                        inline=False)
        embed.add_field(name="Staff Only:",
                        value="/tb forceremove <code> - Smash crash forces a TB out of the public database.\n⮡   Meant for the Dev to be able to remove codes which no longer exist, or violate the rules etc.\n\n/tb purge <username|user> - Smash crash forces all TBs owned by a specified Geocaching username or added by a Discord user out of the public database.\n⮡   Meant for the Dev to be able to bulk remove codes faster, in case they were accidentally added etc.",
                        inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
# TB ADD
    @app_commands.command()
    @app_commands.describe(code="The PRIVATE code of the TB you want to add")
    async def add(self, interaction: discord.Interaction, code: str):
        """Adds a TB to the public database."""
        code = code.upper()
        if code.lower().startswith("tb"):
            await interaction.response.send_message(f"Please try again with the private code (this can be found on the TB itself) as the code, instead of `{code}`. If you believe this to be an error, please contact the Developer @not.cbh (<@820297275448098817>).", ephemeral=True)
            await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to use `tb add` but entered the public code instead of the private one: `{code}`.")
            return

        async def confirm_callback(intx: discord.Interaction):
            try:
                tb = g_obj.get_trackable(code)
                try:
                    tb.load()
                except Exception:
                    await intx.followup.send(f"The TB code you entered (`{code}`) was not valid or is not activated. Please try again with a valid, activated TB code.", ephemeral=True)
                    await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) used `tb add` but the TB code was not valid or unactivated.")
                    return

                cursor1.execute("SELECT * FROM trackables WHERE code = ?", (code,))
                existing_entry = cursor1.fetchone()
                if existing_entry:
                    await intx.followup.send(f"This TB code (`{code}`) is already in the database.", ephemeral=True)
                    return

                user_id = interaction.user.id
                cursor1.execute("""
                    INSERT INTO trackables (code, gc_username, uploaded_time, user_id, tb_code) 
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
                """, (code, tb.owner, user_id, tb.tid))
                conn1.commit()
                await intx.followup.send(f"This TB (`{code}`) has been added to the public database - thanks for sharing!\nOwner Name: {tb.owner}. If this is NOT you, please immediately </tb remove:1370815537151606925> it. Failure to do so could lead to blacklists or suspensions.", ephemeral=True)
                await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) has shared TB `{code}` and it has been added to the database!")
                await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) has shared TB `{code}` and it has been added to the database!")

            except Exception as e:
                await intx.followup.send(f"An unknown error occured whilst processing code `{code}`. The Dev has been notified.", ephemeral=True)
                await log_error(interaction.guild, bot, interaction.command.name, 
                    f"User: {interaction.user.mention} ({interaction.user.name}) adding TB `{code}` to the database. Error: \n```\n{str(e)}\n```"
                )

        view = TBOwnershipConfirmView(user_id=interaction.user.id, callback=confirm_callback, single_code=code)
        await interaction.response.send_message(f"Please confirm that you own the TB with code `{code}` before it is added to the public database.", view=view, ephemeral=True)
        view.message = await interaction.original_response()
    
# TB BULKADD        
    @app_commands.command()
    @app_commands.describe(codes="The PRIVATE codes of the TBs you want to add, separated by commas, spaces, or colons")
    async def bulkadd(self, interaction: discord.Interaction, codes: str):
        """Adds multiple TBs to the public database."""
        tb_codes = list(dict.fromkeys([code.upper().strip() for code in re.split(r"[,\s:]+", codes.strip()) if code.strip()]))

        if not tb_codes:
            await interaction.response.send_message("No valid TB codes found. Please provide at least one code separated by commas, spaces, or colons.", ephemeral=True)
            return

        async def bulk_confirm_callback(intx: discord.Interaction):
            await intx.followup.send(f"Processing {len(tb_codes)} TB code(s)... this may take a while. \n**Please keep this message open!**", ephemeral=True)

            successful_codes = []
            failed_codes = []
            added_owners = set()

            for code in tb_codes:
                if code.lower().startswith("tb"):
                    await master_log_message(interaction.guild, bot, interaction.command.name,
                        f"{interaction.user.mention} ({interaction.user.name}) tried to use `bulkadd` but entered the public code instead of the private one: `{code}`."
                    )
                    failed_codes.append(code)
                    continue

                try:
                    tb = g_obj.get_trackable(code)
                    try:
                        tb.load()
                    except Exception:
                        await master_log_message(interaction.guild, bot, interaction.command.name,
                            f"{interaction.user.mention} ({interaction.user.name}) used `bulkadd` but the TB code was invalid or unactivated for code: `{code}`."
                        )
                        failed_codes.append(code)
                        continue 

                    cursor1.execute("SELECT * FROM trackables WHERE code = ?", (code,))
                    existing_entry = cursor1.fetchone()
                    if existing_entry:
                        await master_log_message(interaction.guild, bot, interaction.command.name,
                            f"{interaction.user.mention} ({interaction.user.name}) attempted to bulkadd TB `{code}`, but it already exists in the database."
                        )
                        failed_codes.append(code)
                        continue

                    user_id = interaction.user.id
                    cursor1.execute("""
                        INSERT INTO trackables (code, gc_username, uploaded_time, user_id, tb_code) 
                        VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
                    """, (code, tb.owner, user_id, tb.tid))
                    conn1.commit()
                    await master_log_message(interaction.guild, bot, interaction.command.name,
                        f"{interaction.user.mention} ({interaction.user.name}) has shared TB `{code}` and it has been added to the database!"
                    )
                    await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) has shared TB `{code}` and it has been added to the database!")
                    successful_codes.append(code)
                    added_owners.add(tb.owner)

                except Exception as e:
                    await log_error(interaction.guild, bot, interaction.command.name,
                        f"{interaction.user.mention} ({interaction.user.name}) tried to bulkadd TB `{code}`: {e}"
                    )
                    failed_codes.append(code)

            max_codes_display = 20
            if len(successful_codes) > max_codes_display:
                successful_str = ", ".join(successful_codes[:max_codes_display]) + f" ... and {len(successful_codes) - max_codes_display} more"
            else:
                successful_str = ", ".join(successful_codes) if successful_codes else "None"
                
            if len(failed_codes) > max_codes_display:
                failed_str = ", ".join(failed_codes[:max_codes_display]) + f" ... and {len(failed_codes) - max_codes_display} more"
            else:
                failed_str = ", ".join(failed_codes) if failed_codes else "None"

            results_msg = (
                f"Finished processing TB codes!\n"
                f"Successfully added: {len(successful_codes)} ({successful_str})\n"
                f"Failed to add: {len(failed_codes)} ({failed_str})\n"
            )
            
            if added_owners:
                results_msg += f"**Owners of Added TBs:** {', '.join(added_owners)}\n"
            
            results_msg += (
                f"\nThank you for your contribution(s) towards the trackable database!\n\n"
                f"*If any of these are NOT you, please immediately </tb remove:1370815537151606925> the relevant TB. Failure to do so could lead to blacklists or suspensions.*"
            )

            await intx.followup.send(results_msg, ephemeral=True)

        view = TBOwnershipConfirmView(user_id=interaction.user.id, callback=bulk_confirm_callback, codes=tb_codes)
        await interaction.response.send_message(f"Please confirm that you own all {len(tb_codes)} TB(s) before they are added to the public database.", view=view, ephemeral=True)
        view.message = await interaction.original_response()

# TB PURGE
    @app_commands.command()
    @is_dev()
    @app_commands.describe(
        username="The Geocaching username of the owner of the TBs you want to remove",
        user="The Discord user who added the TBs you want to remove"
    )
    async def purge(self, interaction: discord.Interaction, username: str = None, user: discord.User = None):
        """Removes all TBs associated with the given gc_username or Discord user ID."""
        if not username and not user:
            await interaction.response.send_message(
                "Please provide either a `username` (Geocaching username) or `user` (Discord user) to purge TBs.",
                ephemeral=True
            )
            return
        
        if username and user:
            await interaction.response.send_message(
                "Please provide only one: either `username` (Geocaching username) or `user` (Discord user), not both.",
                ephemeral=True
            )
            return
        
        try:
            if user:
                user_id = user.id
                cursor1.execute("SELECT COUNT(*) FROM trackables WHERE user_id = ?", (user_id,))
                count = cursor1.fetchone()[0]

                if count > 0:
                    cursor1.execute("DELETE FROM trackables WHERE user_id = ?", (user_id,))
                    conn1.commit()

                    await interaction.response.send_message(
                        f"Successfully purged {count} TB(s) added by {user.mention} ({user.name}).", ephemeral=True
                    )
                    await master_log_message(interaction.guild, bot, interaction.command.name,
                        f"{interaction.user.mention} ({interaction.user.name}) purged {count} TB(s) added by {user.mention} ({user.name}, ID: {user_id})."
                    )
                    await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) purged {count} TB(s) added by {user.mention} ({user.name}, ID: {user_id}).")
                else:
                    await interaction.response.send_message(
                        f"No TBs were found added by {user.mention} ({user.name}).", ephemeral=True
                    )
                    await master_log_message(interaction.guild, bot, interaction.command.name,
                        f"{interaction.user.mention} ({interaction.user.name}) attempted to purge TBs for {user.mention} ({user.name}, ID: {user_id}), but none were found."
                    )
            else:
                cursor1.execute("SELECT COUNT(*) FROM trackables WHERE gc_username = ?", (username,))
                count = cursor1.fetchone()[0]

                if count > 0:
                    cursor1.execute("DELETE FROM trackables WHERE gc_username = ?", (username,))
                    conn1.commit()

                    await interaction.response.send_message(
                        f"Successfully purged {count} TB(s) associated with the username `{username}`.", ephemeral=True
                    )
                    await master_log_message(interaction.guild, bot, interaction.command.name,
                        f"{interaction.user.mention} ({interaction.user.name}) purged {count} TB(s) associated with the username `{username}`."
                    )
                    await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) purged {count} TB(s) associated with the username `{username}`.")
                else:
                    await interaction.response.send_message(
                        f"No TBs were found associated with the username `{username}`.", ephemeral=True
                    )
                    await master_log_message(interaction.guild, bot, interaction.command.name,
                        f"{interaction.user.mention} ({interaction.user.name}) attempted to purge TBs for `{username}`, but none were found."
                    )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred while attempting to purge TBs. The Dev has been alerted.", ephemeral=True
            )
            await log_error(interaction.guild, bot, interaction.command.name,
                f"{interaction.user.mention} ({interaction.user.name}) tried to purge TBs. Error: `{e}`"
            )
      
# TB REMOVE      
    @app_commands.command()
    @app_commands.describe(private_code="The PRIVATE code of the TB you want to remove")
    async def remove(self, interaction: discord.Interaction, private_code: str):
        """Removes a TB from the public database."""
        try:
            cursor1.execute("SELECT * FROM trackables WHERE code = ?", (private_code,))
            existing_entry = cursor1.fetchone()

            if existing_entry:
                if existing_entry[0] == interaction.user.id:
                    await interaction.response.send_message(f"Are you sure you want to remove TB `{private_code}` from the database?", view=TBRemoveConfirmView(private_code, interaction.user.id), ephemeral=True)
                else:
                    await interaction.response.send_message(f"This command only lets you remove TBs that you have added yourself. Please DM the Developer `@not.cbh` (<@820297275448098817>) to remove this if it is yours.", ephemeral=True)
            else:
                await interaction.response.send_message(f"The TB with code `{private_code}` was not found in the database.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"An error occurred while trying to find the TB. The Dev has been notified.", ephemeral=True)
            await log_error(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to remove TB `{private_code}`. Error: {e}")
            return
            
# TB FORCEREMOVE
    @app_commands.command()
    @is_dev()
    @app_commands.describe(code="The PRIVATE code of the TB you want to remove")
    async def forceremove(self, interaction: discord.Interaction, code: str):
        """Smash crash forces removal of a TB from the public database."""
        try:
            cursor1.execute("SELECT * FROM trackables WHERE code = ?", (code,))
            existing_entry = cursor1.fetchone()

            if existing_entry:
                cursor1.execute("DELETE FROM trackables WHERE code = ?", (code,))
                conn1.commit()
                await interaction.response.send_message(f"The TB with code `{code}` has been forcibly removed from the database.", ephemeral=True)
                await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) forcibly removed TB `{code}` from the database.")
                await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) forcibly removed TB `{code}` from the database.")
            else:
                await interaction.response.send_message(f"No TB with the code `{code}` was found in the database.", ephemeral=True)
                await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to forcibly remove TB `{code}` from the database but it wasn't there.")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while trying to remove the TB. The Dev has been notified.", ephemeral=True)
            await log_error(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to forcibly remove TB `{code}`. Error: {e}")
            
# TB VIEW
    @app_commands.command()
    async def view(self, interaction: discord.Interaction):
        """Shows the public TB database."""
        try:
            cursor1.execute("SELECT * FROM trackables")
            trackables = cursor1.fetchall()
        except Exception as e:
            await interaction.response.send_message(
                "An error occurred while retrieving the TB database. Please try again later.",
                ephemeral=True
            )
            await log_error(interaction.guild, bot, interaction.command.name,
                f"{interaction.user.mention} ({interaction.user.name}) used `view`. Error: {e}"
            )
            return
        
        items_per_page = 5
        pages = [trackables[i:i + items_per_page] for i in range(0, len(trackables), items_per_page)]
        
        if not pages:
            await interaction.response.send_message("The database is empty.", ephemeral=True)
            return
        
        def create_embed(page_num):
            embed = discord.Embed(title="Public TB Database", colour=0xad7e66)
            embed.set_footer(text=f"Page {page_num + 1} of {len(pages)}")
            
            for entry in pages[page_num]:
                try:
                    tb_code = entry[3]  
                    code = entry[4]   
                    cleaned_owner_name = entry[1] 
                    added_at_time = entry[2]  
                    
                    try:
                        added_at_dt = datetime.strptime(added_at_time, "%Y-%m-%d %H:%M:%S")
                        added_at_unix = int(added_at_dt.timestamp())
                        discord_timestamp = f"<t:{added_at_unix}>"
                    except (ValueError, TypeError):
                        discord_timestamp = added_at_time  
                    
                    embed.add_field(
                        name=f"{tb_code} - {cleaned_owner_name}",
                        value=f"**CODE**: {code}\n**OWNER**: {cleaned_owner_name}\n**ADDED**: {discord_timestamp}",
                        inline=False
                    )
                except (IndexError, TypeError):
                    continue
            
            return embed
        
        class PaginationView(View):
            def __init__(self, pages, user_id):
                super().__init__(timeout=60.0)
                self.pages = pages
                self.page_number = 0
                self.user_id = user_id
                self.update_buttons()
            
            def update_buttons(self):
                self.first_page.disabled = self.page_number == 0
                self.prev_page.disabled = self.page_number == 0
                self.next_page.disabled = self.page_number >= len(self.pages) - 1
                self.last_page.disabled = self.page_number >= len(self.pages) - 1
            
            @discord.ui.button(label="⏮️ First", style=discord.ButtonStyle.secondary, row=0)
            async def first_page(self, interaction: discord.Interaction, button: Button):
                if interaction.user.id != self.user_id:
                    await interaction.response.send_message("This pagination is not for you!", ephemeral=True)
                    return
                
                self.page_number = 0
                self.update_buttons()
                embed = create_embed(self.page_number)
                await interaction.response.edit_message(embed=embed, view=self)
            
            @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
            async def prev_page(self, interaction: discord.Interaction, button: Button):
                if interaction.user.id != self.user_id:
                    await interaction.response.send_message("This pagination is not for you!", ephemeral=True)
                    return
                
                if self.page_number > 0:
                    self.page_number -= 1
                    self.update_buttons()
                    embed = create_embed(self.page_number)
                    await interaction.response.edit_message(embed=embed, view=self)
            
            @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary, row=0)
            async def next_page(self, interaction: discord.Interaction, button: Button):
                if interaction.user.id != self.user_id:
                    await interaction.response.send_message("This pagination is not for you!", ephemeral=True)
                    return
                
                if self.page_number < len(self.pages) - 1:
                    self.page_number += 1
                    self.update_buttons()
                    embed = create_embed(self.page_number)
                    await interaction.response.edit_message(embed=embed, view=self)
            
            @discord.ui.button(label="Last ⏭️", style=discord.ButtonStyle.secondary, row=0)
            async def last_page(self, interaction: discord.Interaction, button: Button):
                if interaction.user.id != self.user_id:
                    await interaction.response.send_message("This pagination is not for you!", ephemeral=True)
                    return
                
                self.page_number = len(self.pages) - 1
                self.update_buttons()
                embed = create_embed(self.page_number)
                await interaction.response.edit_message(embed=embed, view=self)
            
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit(view=self)
                except:
                    pass
        
        embed = create_embed(0)
        
        if len(pages) > 1:
            view = PaginationView(pages, interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            view.message = await interaction.original_response()
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

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

            codes = [entry[0] for entry in trackables]
            chunks = []
            current_chunk = ""

            for code in codes:
                if len(current_chunk) + len(code) + 2 > 2000: 
                    chunks.append(current_chunk.rstrip(", "))
                    current_chunk = ""
                current_chunk += f"{code}, "

            if current_chunk:
                chunks.append(current_chunk.rstrip(", "))
                
            try:
                for chunk in chunks:
                    await interaction.user.send(chunk)
                await interaction.response.send_message("The TB codes have been sent to your DMs.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "I couldn't send you a DM. Please make sure your DMs are open and try again.",
                    ephemeral=True
                )

        except Exception as e:
            await interaction.response.send_message(
                "An error occurred while retrieving the TB codes. Please ask an Administrator to check the logs.",
                ephemeral=True
            )
            await log_error(
                interaction.guild, bot, interaction.command.name,
                f"{interaction.user.mention} ({interaction.user.name}) used `bulkview`. Error: {e}"
            )

tb_commands = TBDatabase(name="tb", description="Public TB Database commands.")

async def setup(bot):
    bot.tree.add_command(tb_commands)