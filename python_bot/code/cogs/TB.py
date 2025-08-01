import discord
import asyncio
from discord import app_commands
import sqlite3

from functions import *
import re
from bot import bot
from datetime import datetime
from functions import *
from bs4 import BeautifulSoup
from logger import log

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
    conn1.close()
    
class TBDatabase(app_commands.Group):
    """Commands for the public TB database."""
    
# TB HELP
    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Shows all of the public TB database commands."""
        embed = discord.Embed(title="Public TB Database",
                            colour=0xad7e66)

        embed.add_field(name="Everyone:",
                        value="/tb add <code> - Adds a TB to the public database.\n\n/tb bulkadd - Bulk adds TBs to the public database as long as they are separated.\n⮡   They MUST be separated via eg. space, comma etc.\n\n/tb remove - Removes a TB from the public database.\n⮡   You MUST contact the Dev to get it removed.\n\n/tb view - Shows the public TB database.\n⮡   Shows 5 codes in one embed. You must use the pagination (reactions) to move to the next page, if there is one.\n\n/tb bulkview - Sends all codes in the public TB database to your DMs.\n⮡   DMs you ALL codes in one message. They are separated by commas, so they are suitable for [logthemall](<https://www.logthemall.org/>) or the [PGC trackable tool](<https://project-gc.com/Tools/DiscoverTrackables>).",
                        inline=False)
        embed.add_field(name="Staff Only:",
                        value="/tb forceadd <code> - Smash crash forces a TB into the public database.\n⮡   Meant for the Dev to be able to add codes which users do not own but have permission to share.\n\n/tb forceremove <code> - Smash crash forces a TB out of the public database.\n⮡   Meant for the Dev to be able to remove codes which no longer exist, or violate the rules etc.\n\n/tb purge <name> - Smash crash forces all TBs owned by a specified user out of the public database.\n⮡   Meant for the Dev to be able to bulk remove codes faster, in case they were accidentally added etc.",
                        inline=False)
        
        await interaction.response.send_message(embed=embed)
    
# TB ADD
    @app_commands.command()
    @app_commands.describe(code="The PRIVATE code of the TB you want to add")
    async def add(self, interaction: discord.Interaction, code: str):
        """Adds a TB to the public database."""
        code = code.upper()
        code = code.upper()
        if code.lower().startswith("tb"):
            await interaction.response.send_message(f"Please try again with the private code (this can be found on the TB itself) as the code, instead of `{code}`. If you believe this to be an error, please contact staff.")
            await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to use `tb add` but entered the public code instead of the private one: `{code}`.")
            return

        try:
            tb = g_obj.get_trackable(code)
            try:
                tb.load()
            except:
                await interaction.response.send_message(f"The TB code you entered (`{code}`) was not valid or is not activated. Please try again with a valid, activated TB code.")
                await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) used `tb add` but the TB code was not valid or unactivated.")
                return

            cursor1.execute("SELECT * FROM trackables WHERE code = ?", (code,))
            existing_entry = cursor1.fetchone()
            if existing_entry:
                await interaction.response.send_message(f"This TB code (`{code}`) is already in the database.")
                return

            user_id = interaction.user.id
            cursor1.execute("""
                INSERT INTO trackables (code, gc_username, uploaded_time, user_id, tb_code) 
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
            """, (code, tb.owner, user_id, tb.tid))
            conn1.commit()
            await interaction.response.send_message(f"This TB (`{code}`) has been added to the public database - thanks for sharing!")
            await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) has shared TB `{code}` and it has been added to the database!")
            await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) has shared TB `{code}` and it has been added to the database!")

        except Exception as e:
            await interaction.response.send_message(f"An unknown error occured whilst processing code `{code}`. The Dev has been notified.")
            await log_error(interaction.guild, bot, interaction.command.name, 
                f"User: {interaction.user.mention} ({interaction.user.name}) adding TB `{code}` to the database. Error: \n```\n{str(e)}\n```"
            )
    
# TB BULKADD        
    @app_commands.command()
    @app_commands.describe(codes="The PRIVATE codes of the TBs you want to add, separated by commas, spaces, or colons")
    async def bulkadd(self, interaction: discord.Interaction, codes: str):
        """Adds multiple TBs to the public database."""
        tb_codes = [ code.upper() for code in re.split(r"[,\s:]+", codes.strip()) ]

        await interaction.response.send_message(f"Processing {len(tb_codes)} TB code(s)... this may take a while.", ephemeral=True)

        successful_codes = []
        failed_codes = []

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
                except:
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
            f"Thank you for your contribution(s) towards the trackable database!",
            ephemeral=True
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
                await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) purged {count} TB(s) associated with the username `{username}`.")
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
      
# TB REMOVE      
    @app_commands.command()
    async def remove(self, interaction: discord.Interaction):
        """Removes a TB from the public database."""
        await interaction.response.send_message(f"If you want a TB to be removed from the database, please contact the Developer `@not.cbh` (<@820297275448098817>).")
            
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
                await interaction.response.send_message(f"The TB with code `{code}` has been forcibly removed from the database.")
                await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) forcibly removed TB `{code}` from the database.")
                await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) forcibly removed TB `{code}` from the database.")
            else:
                await interaction.response.send_message(f"No TB with the code `{code}` was found in the database.")
                await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to forcibly remove TB `{code}` from the database but it wasn't there.")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while trying to remove the TB. The Dev has been notified.")
            await log_error(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) tried to forcibly remove TB `{code}`. Error: {e}")
            
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

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        if len(pages) > 1: 
            await message.add_reaction("⏮️") 
            await message.add_reaction("◀️")  
            await message.add_reaction("▶️") 
            await message.add_reaction("⏭️") 

        def check(reaction, user):
            return user == interaction.user and reaction.message.id == message.id and str(reaction.emoji) in ["⏮️", "◀️", "▶️", "⏭️"]

        while True:
            try:
                reaction, user = await interaction.client.wait_for("reaction_add", timeout=60.0, check=check)

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
                    code = entry[4]
                    cleaned_owner_name = entry[1]
                    added_at_time = entry[2]  
                    tb_code = entry[3]
                    
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