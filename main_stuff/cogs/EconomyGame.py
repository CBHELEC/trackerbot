import discord
from economy import *
from gamefunctions import *
from functions import *
from discord import app_commands
import asyncio
import re
from bot import bot
from discord.ui import View

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
                fp = await get_fav_points_owned(session, user_id)
                hides = await get_hides(session, user_id)
                finds = await get_finds(session, user_id)
                tb_d = await get_trackables_discovered(session, user_id)
                tb_o = await get_trackables_owned(session, user_id)
                name = await get_cacher_name(session, user_id)
                embed = discord.Embed(title=f"{name}'s Balances:",
                      colour=0xad7e66)

                embed.add_field(name=f"G$: {balance}",
                                value="",
                                inline=False)
                embed.add_field(name=f"FP: {fp}",
                                value="",
                                inline=False)
                embed.add_field(name=f"Hides: {hides}",
                                value="",
                                inline=False)
                embed.add_field(name=f"Finds: {finds}",
                                value="",
                                inline=False)
                embed.add_field(name=f"TB Discovered: {tb_d}",
                                value="",
                                inline=False)
                embed.add_field(name=f"TB Owned: {tb_o}",
                                value="",
                                inline=False)
                await interaction.response.send_message(embed=embed)
        
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
                await interaction.response.send_message(embed=embed, view=ShopView(interaction))
                
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
                inventory_items = await get_inventory(session, user_id)  
                if not inventory_items:
                    await interaction.response.send_message("Your inventory is empty.", ephemeral=True)
                    return

                item_counts = {}
                for item in inventory_items:
                    item = item.strip()
                    item_counts[item] = item_counts.get(item, 0) + 1

                embed = discord.Embed(
                    title=f"{interaction.user.display_name}'s Inventory:",
                    colour=0xad7e66
                )

                for item, count in item_counts.items():
                    parts = re.findall(r'\d+|\.\d+|[A-Za-z]', item)  # Parse the item ID into components
                    main_item = MAIN_INVENTORY.get(parts[0], "Unknown Item")  # Get the main item name
                    alt_items = [ALT_INVENTORY.get(part, "") for part in parts[1:]]  # Get all alternate attributes
                    alt_items = [alt for alt in alt_items if alt]  # Remove empty attributes

                    # Format the item name
                    item_name = f"{' '.join(alt_items)} {main_item}".strip()
                    if "Log (Plain Paper)" in alt_items:
                        item_name = item_name.replace("Log (Plain Paper)", "").strip() + " w/ Log"

                    embed.add_field(
                        name=f"{count}x {item_name}",
                        value="",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)
        
    @app_commands.command()
    @app_commands.choices(fp_status=[
        app_commands.Choice(name="Do NOT give FP", value=0),
        app_commands.Choice(name="Give FP", value=1)
    ])
    async def find(self, interaction: discord.Interaction, cache_id: str, log_content: str, fp_status: app_commands.Choice[int]):
        """
        Find a cache and log it.
        
        Args:
            cache_id (str): The ID of the cache to find.
            log_content (str): Optional log content for the find.
        """
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

            success = await find(session, user_id, cache_id, log_content, fp_status.value)
            if success:
                if fp_status.value == 1:
                    fp_bal = await get_db_settings(session, user_id)
                    fp_bal1 = fp_bal.fav_points_owned
                    final_bal = fp_bal1 - 1
                    await update_fav_points_owned(session, user_id, final_bal)
                hide = await get_hide_by_id(session, cache_id)
                co_name_id = hide.user_id
                cache_name = hide.name
                co_info = await get_db_settings(session, co_name_id)
                co_name = co_info.cacher_name
                fp_status = "✅" if fp_status.value == 1 else "❌"
                embed = discord.Embed(title="Cache successfully logged!",
                      description=f"Cache Name: {cache_name} (ID: {cache_id})\nOwner: {co_name}\nLog: {log_content}\nFP: {fp_status}",
                      colour=0x8e8948)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"This cache doesn't exist, or you have already found it.", ephemeral=True)
        
    @app_commands.command()
    async def cache_finds(self, interaction: discord.Interaction, cache_id: str):
        """
        Retrieve all finds for a specific cache and display them in an embed.
        
        Args:
            cache_id (str): The ID of the cache to retrieve finds for.
        """
        async with Session() as session:
            user_id = interaction.user.id
            # Check if the cache exists
            hide = await get_hide_by_id(session, cache_id)
            if not hide:
                await interaction.response.send_message(f"Cache `{cache_id}` not found.", ephemeral=True)
                return

            # Retrieve all finds for the cache using the new function
            finds = await get_finds_for_cache(session, cache_id)

            if not finds:
                await interaction.response.send_message(f"No finds have been logged for cache `{cache_id}` yet.", ephemeral=True)
                return

            cacher_name_db = await get_db_settings(session, user_id)
            cacher_name = cacher_name_db.cacher_name

            # Create the embed
            embed = discord.Embed(
                title=f"Finds for Cache: {hide.name}",
                description=f"Cache ID: `{cache_id}`\nTotal Finds: **{len(finds)}**",
                colour=0xad7e66
            )
            embed.add_field(name="Location", value=f"{hide.location_name} ({hide.location_lat:.6f}, {hide.location_lon:.6f})", inline=False)

            # Add each find to the embed
            for find in finds:
                log_content = find.log_content if find.log_content else "No log content provided."
                fp_status = "✅" if find.fp_status == 1 else "❌"
                embed.add_field(
                    name=f"Finder: {cacher_name}",
                    value=f"**Log:** {log_content}\n**FP:** {fp_status}",
                    inline=False
                )

            # Send the embed
            await interaction.response.send_message(embed=embed)
        
eco_commands = Economy(name="game", description="Geocaching Game Commands.")

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
        
    @add_money.error
    async def add_money_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(embed=YOUCANTDOTHIS, ephemeral=True)
        else:
            raise error        
    
eco_a_commands = Game_Admin(name="game_admin", description="Geocaching Game Admin Commands.")

async def setup(bot):
    bot.tree.add_command(eco_commands)
    bot.tree.add_command(eco_a_commands)