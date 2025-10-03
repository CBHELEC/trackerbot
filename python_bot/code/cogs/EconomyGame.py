import asyncio
import re
import discord
from logger import log
from collections import defaultdict
from economy import *
from gamefunctions import *
from functions import *
from discord import app_commands
from datetime import datetime, timedelta
from discord.ui import View, Button, Modal, TextInput

class Economy(app_commands.Group):
    """Discaching Game Commands!"""
    
    @app_commands.command()
    async def balance(self, interaction: discord.Interaction):
        user = interaction.user
        user_id = user.id
        async with Session() as session:
            user_database_settings = await get_db_settings(session, user_id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))            
                return
            else:
                embed = discord.Embed(title=f"{await get_cacher_name(session, user_id)}'s Balances:",
                      colour=0xad7e66)

                embed.add_field(name=f"G$: {await get_balance(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"FP: {await get_fav_points_owned(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"Hides: {await get_hides(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"Finds: {await get_finds(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"TB Discovered: {await get_trackables_discovered(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"TB Owned: {await get_cacher_name(session, user_id)}",
                                value="",
                                inline=False)
                await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.choices(option=[
        app_commands.Choice(name="Rural Locations", value="1"),
        app_commands.Choice(name="City Locations", value="2")
    ])
    async def locations(self, interaction: discord.Interaction, option: app_commands.Choice[str]):
        if option.value == "1":
            embed = discord.Embed(
                title="Rural Geocaching Locations",
                description="Frostbrook Ridge – A remote, snow-covered mountain range in the far north, sparsely populated with only a few settlements. The frost here is intense, and the landscape is dominated by towering pines and frozen rivers.\n\nBlackrock Desert – A vast, dry expanse marked by jagged black rock formations and endless stretches of sandy dunes. The area is harsh, with scorching days and freezing nights, making it nearly impossible for anything to survive.\n\nEcho Lake Caverns – A series of limestone caves tucked deep within the forest, where the sound of water trickling through the walls creates an eerie, echoing effect. The caverns are home to rare species of bats and underground plants.\n\nStorm Island – A small, isolated island off the coast known for its unpredictable and frequent storms. Few fishermen dare to approach, and it remains largely uncharted by modern maps.\n\nDry Hollow Basin – An arid region with cracked earth and sparse vegetation, where ancient dry riverbeds tell stories of once-thriving communities now long abandoned. It’s an unforgiving place, where any trace of water is a rare find.\n\nMosswood Swamp – A damp, murky wetland full of thick moss and cypress trees. The air is heavy with the scent of decay, and it's said that the fog here often hides the movements of unseen creatures.\n\nSilverfall Bluff – A windswept plateau overlooking a wide river valley. The cliff faces here shimmer with silver-coloured rock formations, and the wind blows relentlessly, making it a difficult place to traverse.\n\nFrozen Hollow – A remote tundra, where temperatures regularly plunge below freezing. The landscape is dotted with glaciers and ice-covered ruins of old settlements, making it an inhospitable but fascinating place for explorers.\n\nOldport Ruins – The remains of an ancient port city once bustling with trade. Now submerged under a shallow layer of water, only the tops of old stone buildings poke through the surface, a haunting reminder of its former glory.\n\nWhistler’s Canyon – A narrow, wind-carved canyon where the winds create strange, howling noises as they pass through. It’s known for its rugged terrain and its reputation as a dangerous spot for hikers and travelers.",
                colour=0xad7e66)

            embed.set_footer(text="This embed will self-destruct in 5 minutes. Click the 🗑️ icon to delete now.")

            await interaction.response.send_message(embed=embed, view=DeleteEmbedView())
            sent_message = await interaction.original_response()
            await asyncio.sleep(300)
            await sent_message.delete()
            
        else:
            embed = discord.Embed(title="Rural Geocaching Locations",
                      description="Harrowsbrook – A small industrial town nestled by the river, known for its aging factories and old brick buildings. The town has a gritty, blue-collar vibe, with a rich history tied to its ironworks and textile mills.\n\nEverfield – A city surrounded by sprawling farmland and endless green fields, where the pace of life is slow, and the community is tight-knit. Known for its annual agricultural fairs and harvest festivals.\n\nLarkspur Crossing – A vibrant market town that acts as a key transportation hub, with people coming from all around to trade goods. The town is built around a large central square where street vendors and performers gather.\n\nBrunswick Harbor – A busy coastal city known for its bustling harbor, where fishing boats and cargo ships dock daily. The city has a lively waterfront, with seafood restaurants and bars overlooking the docks.\n\nAlderpoint – A hilltop city known for its historic architecture, with winding cobblestone streets and a centuries-old cathedral at the city’s heart. It has a more refined, older charm, with an abundance of parks and cultural institutions.",
                      colour=0xad7e66)
            embed.set_footer(text="This embed will self-destruct in 5 minutes. Click the 🗑️ icon to delete now.")
            await interaction.response.send_message(embed=embed, view=DeleteEmbedView())
            sent_message = await interaction.original_response()
            await asyncio.sleep(300)
            await sent_message.delete()
            
    @app_commands.command()
    async def hide(self, interaction: discord.Interaction):
        """
        Create a geocache hide, allowing the user to select a container from their inventory.
        """
        await interaction.response.defer(ephemeral=True)
        async with Session() as session:
            user_id = interaction.user.id
            user_database_settings = await get_db_settings(session, user_id)

            # if user isnt registered
            if user_database_settings.cacher_name is None:
                await interaction.followup.send(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.followup.send("Please enter your cacher name below.", ephemeral=True)
                await original_message.edit(view=CacherNameView(original_message))
                return

            # if inventory empty
            inventory_items = await get_inventory(session, user_id)
            if not inventory_items:
                await interaction.followup.send(
                    "Your inventory is empty. You need a container to create a hide.",
                    ephemeral=True
                )
                return

            # inv has stuff but no containers
            containers = [item for item in inventory_items if item.split('.')[0] in SHOP_PRICES["containers"]]
            if not containers:
                await interaction.followup.send(
                    "You need a container in your inventory to create a hide.",
                    ephemeral=True
                )
                return

            hides = await get_hides_by_user(session, user_id)
            
            # user has unpublished hides
            unpublished_hides = [hide for hide in hides if hide.published == 0]
            if unpublished_hides:
                embed = discord.Embed(
                    title="Unpublished Hides",
                    description="It appears you have unpublished hides. Do you want to edit one of these or make a new hide?",
                    colour=0x00b0f4
                )
                for hide in unpublished_hides:
                    embed.add_field(name=f"{hide.id} - {hide.name}", value=" ", inline=False)
                async def on_edit(interaction, selected_hide):
                    hide_data = await load_hide_data_from_db(selected_hide.id)
                    if not hide_data:
                        await interaction.response.send_message("Could not load hide data.", ephemeral=True)
                        return
                    await uwu1.delete()
                    await start_hide_configuration(interaction, hide_data, hide_id=selected_hide.id)
                async def on_continue(interaction):
                    item_counts = defaultdict(int)
                    item_to_container = {}
                    for container in containers:
                        parts = re.findall(r'\d+|\.\d+|[A-Za-z]', container)
                        main_item = MAIN_INVENTORY.get(parts[0], "Unknown Item")
                        alt_items = [ALT_INVENTORY.get(part, "") for part in parts[1:]]
                        alt_items = [alt for alt in alt_items if alt]
                        item_name = f"{main_item} {' '.join(alt_items)}".strip()
                        if "Log" in item_name:
                            item_name = item_name.replace("Log", "w/ Log")
                        else:
                            item_name = f"{item_name} (NO LOG)"
                        item_counts[item_name] += 1
                        if item_name not in item_to_container:
                            item_to_container[item_name] = (item_name, container)
                    deduped_items = list(item_counts.items())[:25]
                    embed2 = discord.Embed(
                        title="Select a Container for Your Hide",
                        description="Below is a list of containers in your inventory. Enter the number corresponding to the container you want to use. No log means one from your inventory will be picked later.",
                        colour=0xad7e66
                    )
                    for idx, (item_name, count) in enumerate(deduped_items, start=1):
                        display = f"{count}x {item_name}" if count > 1 else item_name
                        embed2.add_field(name=f"{idx}. {display}", value='', inline=False)
                    original_message = await interaction.followup.send(embed=embed2, ephemeral=True)
                    view = ContainerSelectionView(deduped_items, item_to_container, user_id, original_message)
                    await uwu1.delete()
                    await original_message.edit(embed=embed2, view=view)
                permitted_user_id = interaction.user.id
                view = UnpublishedHidesView(unpublished_hides, on_edit, on_continue, permitted_user_id)
                uwu1 = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                return

            # user has no unpublished hides
            embed = discord.Embed(
                title="Select a Container for Your Hide",
                description="Below is a list of containers in your inventory. Enter the number corresponding to the container you want to use. No log means one from your inventory will be picked later.",
                colour=0xad7e66
            )
            
            item_counts = defaultdict(int)
            item_to_container = {}
            
            for container in containers:
                parts = re.findall(r'\d+|\.\d+|[A-Za-z]', container)
                main_item = MAIN_INVENTORY.get(parts[0], "Unknown Item")
                alt_items = [ALT_INVENTORY.get(part, "") for part in parts[1:]]
                alt_items = [alt for alt in alt_items if alt]

                item_name = f"{main_item} {' '.join(alt_items)}".strip()

                if "Log" in item_name:
                    item_name = item_name.replace("Log", "w/ Log")
                else:
                    item_name = f"{item_name} (NO LOG)"

                item_counts[item_name] += 1
                if item_name not in item_to_container:
                    item_to_container[item_name] = (item_name, container)

            deduped_items = list(item_counts.items())[:25]

            for idx, (item_name, count) in enumerate(deduped_items, start=1):
                display = f"{count}x {item_name}" if count > 1 else item_name
                embed.add_field(name=f"{idx}. {display}", value='', inline=False)

            original_message = await interaction.followup.send(embed=embed, ephemeral=True)

            view = ContainerSelectionView(deduped_items, item_to_container, user_id, original_message)
            await original_message.edit(embed=embed, view=view)
        
    @app_commands.command()
    async def cache_info(self, interaction: discord.Interaction, cache_id: str):
        async with Session() as session:
            user_id = interaction.user.id
            user_db_settings = await get_db_settings(session, user_id)
            if user_db_settings.cacher_name is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))            
                return
            else:
                cacher_name = await get_db_settings(session, user_id).cacher_name
                hide = await get_hide_by_id(session, cache_id)

                if not hide:
                    await interaction.response.send_message("Cache not found.", ephemeral=True)
                    return

                timestamp = int(hide.hidden_at.timestamp())

                hidden_at_str = f"<t:{timestamp}:F> (<t:{timestamp}:R>)"

                location_str = f"{hide.location_lat:.6f}, {hide.location_lon:.6f} ({hide.location_name})"

                formatted_hider_mention = f"<@{str(hide.user_id)}>"

                embed = discord.Embed(title=f"Cache Info: {hide.name}", colour=0xad7e66)
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
            user_db_settings = await get_db_settings(session, interaction.user.id)
            if user_db_settings.cacher_name is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))            
                return
            else:
                embed = discord.Embed(title="G$ Shop", description="Select a category from the dropdown to browse items.", colour=0xad7e66)
                await interaction.response.send_message(content=None, embed=embed)
                msg = await interaction.original_response()
                await interaction.edit_original_response(content=None, embed=embed, view=ShopView(interaction, msg))
                
    @app_commands.command()
    async def inventory(self, interaction: discord.Interaction):
        async with Session() as session:
            user_db_settings = await get_db_settings(session, interaction.user.id)
            if user_db_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=CacherNameView(original_message))
                return
            else:
                if not await get_inventory(session, interaction.user.id):
                    await interaction.response.send_message("Your inventory is empty.", ephemeral=True)
                    return

                item_counts = {}
                for item in await get_inventory(session, interaction.user.id):
                    item = item.strip()
                    item_counts[item] = item_counts.get(item, 0) + 1

                embed = discord.Embed(
                    title=f"{user_db_settings.cacher_name}'s Inventory:",
                    colour=0xad7e66
                )

                for item, count in item_counts.items():
                    parts = re.findall(r'\d+|\.\d+|[A-Za-z]', item)  # Parse the item ID into components
                    main_item = MAIN_INVENTORY.get(parts[0], "Unknown Item")  # Get the main item name
                    alt_items = [ALT_INVENTORY.get(part, "") for part in parts[1:]]  # Get all alternate attributes
                    alt_items = [alt for alt in alt_items if alt]  # Remove empty attributes

                    item_name = f"{' '.join(alt_items)} {main_item}".strip()
                    if "Log (Plain Paper)" in alt_items:
                        item_name = item_name.replace("Log (Plain Paper)", "").strip() + " w/ Log"
                        item_name = item_name.replace("  ", " ")

                    embed.add_field(
                        name=f"{count}x {item_name}",
                        value="",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed)

    ####################################################
    # THIS COMMAND WILL BE REDONE ONCE HIDE IS FINISHED.

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
            fp_status (app_commands.Choice[int]): Whether to give a favorite point (FP) or not.
        """
        async with Session() as session:
            user_id = interaction.user.id
            user_database_settings = await get_db_settings(session, user_id)
            if user_database_settings.cacher_name is None:
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
                      colour=0xad7e66)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"This cache doesn't exist, or you have already found it.", ephemeral=True)
        
    # THIS COMMAND WILL BE REDONE ONCE HIDE IS FINISHED.
    ####################################################
    
    ####################################################
    # THIS COMMAND MAY BE REDONE ONCE HIDE IS FINISHED.

    @app_commands.command()
    async def cache_finds(self, interaction: discord.Interaction, cache_id: str):
        """
        Retrieve all finds for a specific cache and display them in an embed.
        
        Args:
            cache_id (str): The ID of the cache to retrieve finds for.
        """
        async with Session() as session:
            user_id = interaction.user.id
            hide = await get_hide_by_id(session, cache_id)
            if not hide:
                await interaction.response.send_message(f"Cache `{cache_id}` not found.", ephemeral=True)
                return

            finds = await get_finds_for_cache(session, cache_id)

            if not finds:
                await interaction.response.send_message(f"No finds have been logged for cache `{cache_id}` yet.", ephemeral=True)
                return

            cacher_name_db = await get_db_settings(session, user_id)
            cacher_name = cacher_name_db.cacher_name

            embed = discord.Embed(
                title=f"Finds for Cache: {hide.name}",
                description=f"Cache ID: `{cache_id}`\nTotal Finds: **{len(finds)}**",
                colour=0xad7e66
            )
            embed.add_field(name="Location", value=f"{hide.location_name} ({hide.location_lat:.6f}, {hide.location_lon:.6f})", inline=False)

            for find in finds:
                log_content = find.log_content if find.log_content else "No log content provided."
                fp_status = "✅" if find.fp_status == 1 else "❌"
                embed.add_field(
                    name=f"Finder: {cacher_name}",
                    value=f"**Log:** {log_content}\n**FP:** {fp_status}",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
        
    # THIS COMMAND MAY BE REDONE ONCE HIDE IS FINISHED.
    ####################################################

    @app_commands.command()
    async def tb_activate(self, interaction: discord.Interaction, private_code: str):
        """Activate a trackable using its private code.
        
        Args:
            private_code (str): The private code of the trackable to activate.
        """
        user_id = interaction.user.id
        async with Session() as session:
            trackable = await activate_trackable(session, user_id, private_code)
            if trackable == "already_activated":
                await interaction.response.send_message(
                    "This trackable has already been activated.",
                    ephemeral=True
                )
            elif trackable:
                await interaction.response.send_message(
                    f"Trackable with public code `{trackable.public_code}` has been successfully activated!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Failed to activate trackable. Either it doesn't exist, or you don't own it.",
                    ephemeral=True
                )
                
    @app_commands.command()
    async def tb_view(self, interaction: discord.Interaction, public_code: str):
        """View info for a trackable.

        Args: 
            public_code (str): The public code of the trackable to view.
        """
        async with Session() as session:
            trackable = await get_trackable(public_code)

            if not trackable:
                await interaction.response.send_message(
                    f"Trackable with public code `{public_code}` not found.",
                    ephemeral=True
                )
                return

            activated_time_dt = datetime.strptime(trackable.activated_time.split('.')[0], "%Y-%m-%d %H:%M:%S") if trackable.activated_time else "N/A"
            unix_timestamp = int(activated_time_dt.timestamp()) if activated_time_dt != "N/A" else None

            discoveries = await get_trackable_discoveries(session, public_code)

            embed = discord.Embed(
                title=f"Trackable Details",
                colour=0xad7e66
            )
            embed.add_field(name="Public Code", value=trackable.public_code, inline=True)
            embed.add_field(name="Owner", value=await get_cacher_name(session, trackable.user_id), inline=True)
            embed.add_field(name="Activation Status", value="✅ Activated" if trackable.activated == 1 else "❌ Not Activated", inline=False)
            embed.add_field(name="Activation Date", value=f"<t:{unix_timestamp}:R>" if trackable.activated_time else "❌ Not Activated", inline=False)

            if discoveries:
                for discovery in discoveries:
                    cacher_name = await get_db_settings(session, discovery.user_id if discovery else None).cacher_name
                    discover_date = int(datetime.strptime(discovery.discover_date, "%Y-%m-%d %H:%M:%S").timestamp()) if discovery.discover_date else "N/A"
                    embed.add_field(
                        name=f"Discovered by {cacher_name}",
                        value=f"**Date:** {f'<t:{discover_date}:f> (<t:{discover_date}:R>)' if discover_date != 'N/A' else 'N/A'}\n**Log:** {discovery.discover_log or "No log provided."}",
                        inline=False
                    )
            else:
                embed.add_field(name="Discoveries", value="No discoveries yet.", inline=False)

            await interaction.response.send_message(embed=embed)
        
    @app_commands.command()
    async def tb_discover(self, interaction: discord.Interaction, private_code: str, log: str):
        """
        Discover a trackable using its private code.

        Args:
            private_code (str): The private code of the trackable to discover.
            log (str): The message to go with the discovery.
        """
        async with Session() as session:
            trackable = await get_trackable(session, private_code)

            if trackable:
                if trackable.user_id == interaction.user.id:
                    await interaction.response.send_message(
                        "You cannot discover your own trackable.",
                        ephemeral=True
                    )
                    return
            else:
                if not trackable:
                    await interaction.response.send_message(
                        f"Trackable with private code `{private_code}` not found.",
                        ephemeral=True
                    )
                    return

            if trackable.activated == 0:
                await interaction.response.send_message(
                    f"Trackable with private code `{private_code}` has not been activated yet.",
                    ephemeral=True
                )
                return

            existing_discovery = await get_trackable_discoveries(session, private_code).scalars().first()

            if existing_discovery:
                await interaction.response.send_message(
                    f"You have already discovered this trackable.",
                    ephemeral=True
                )
                return

            discover_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await add_tb_discovery(session, interaction.user.id, private_code, discover_date, log)
            tbdis = await get_trackables_discovered(session, interaction.user.id)
            await update_trackables_discovered(session, interaction.user.id, tbdis + 1)

            if existing_discovery:
                existing_discovery.discover_date = discover_date
                if log:
                    existing_discovery.discover_log = f"{existing_discovery.discover_log or ''}\n{interaction.user.display_name}: {log}".strip()

            await session.commit()

            if existing_discovery:
                if existing_discovery.discover_date:
                    thedatething = f"{int(datetime.strptime(existing_discovery.discover_date, '%Y-%m-%d %H:%M:%S').timestamp()):R>}" 
                else:
                    thedatething = "N/A"
            else:
                thedatething = "N/A"

            embed = discord.Embed(
                title="Trackable Discovered!",
                description=f"You successfully discovered the trackable with public code `{trackable.public_code}`.",
                colour=0xad7e66
            )
            embed.add_field(name="Discovery Log", value=log or "No log provided.", inline=False)
            embed.add_field(name="Previous Discovery Date", value=thedatething, inline=True)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command()
    async def daily(self, interaction: discord.Interaction):
        async with Session() as session:
            getlastclaim = await get_lastclaim(session, interaction.user.id)
            if getlastclaim:
                if getlastclaim.last_withdraw is not None:
                    last_withdraw_date = datetime.strptime(getlastclaim.last_withdraw, "%Y-%m-%d %H:%M:%S").date() 
                    current_date = datetime.now().date()  

                    if current_date > last_withdraw_date:
                        currentbalance = await get_balance(session, interaction.user.id)
                        newbalance = currentbalance + 25
                        await update_balance(session, interaction.user.id, newbalance)
                        await set_lastclaim(session, interaction.user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        await interaction.response.send_message(f"Daily Reward claimed! New Balance: G${newbalance}", ephemeral=True)
                    else:
                        next_reset = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                        reset_timestamp = int(next_reset.timestamp())
                        await interaction.response.send_message(f"You have already claimed your daily reward today. This resets in <t:{reset_timestamp}:R>.", ephemeral=True)
                else:
                    currentbalance = await get_balance(session, interaction.user.id)
                    newbalance = currentbalance + 25
                    await update_balance(session, interaction.user.id, newbalance)
                    await set_lastclaim(session, interaction.user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    await interaction.response.send_message(f"Daily Reward claimed! New Balance: G${newbalance}", ephemeral=True)
            else:
                currentbalance = await get_balance(session, interaction.user.id)
                newbalance = currentbalance + 25
                await update_balance(session, interaction.user.id, newbalance)
                await set_lastclaim(session, interaction.user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                await interaction.response.send_message(f"Daily Reward claimed! New Balance: G${newbalance}", ephemeral=True)
        
eco_commands = Economy(name="game", description="Geocaching Game Commands.")

class Game_Admin(app_commands.Group):
    """Geocaching Game Admin Commands!"""
    
    # TO DO: COMMAND WHERE ONLY SELECT A USER OR USER ID AND 
    # THEN BRINGS UP BUTTONED MENU OF ACTIONS FOR THUS USER. 
    # LIKELY DO LAST SINCE ITS AFTER ALL FUNCTIONS AND CURRENCY ETC ARE MADE

    # i ignored that because nuking people is fun

    @app_commands.command()
    @is_dev()
    async def userpanel(self, interaction: discord.Interaction, dc_user: discord.Member = None, user_id: str = None, cacher_name: str = None):
        """
        Open an Admin panel for the specified member.
        
        Args:
            dc_user (discord.Member): The user to manage. 
            user_id (str): The ID of the user to manage. 
            cacher_name (str): The cacher name of the user to manage.
        """
        if not (dc_user or user_id or cacher_name): # If no fields entered
            await interaction.response.send_message("You must provide either a user, user ID, or cacher name.", ephemeral=True)
            return

        async with Session() as session:
            #if cacher_name:
            #   cacher_name_info = await get_cacher_info(session, cacher_name)
           #    cacher_name_user_id = cacher_name_info.user_id
          #  user = dc_user if dc_user else self.bot.get_user(int(user_id)) if user_id else self.bot.get_user(cacher_name_user_id) if cacher_name else None # Establish User Variable
           # user_id = user.id # Establish User ID Variable
            #if not user: # If User Var could not be established
             #   await interaction.response.send_message(f"USER VARIABLE NOT ESTABLISHED.", ephemeral=True)

            if dc_user: # If user field was used
                cacher_data = await get_db_settings(session, dc_user.id)
                user_id = dc_user.id
                user = dc_user
            elif user_id: # If user wasnt, was user id?
                cacher_data = await get_db_settings(session, int(user_id))
                user = self.bot.get_user(int(user_id))
            elif cacher_name: # Rip, they didnt work, so maybe cacher_name works?
                cacher_data = await get_cacher_info(session, cacher_name)
                user = self.bot.get_user(cacher_data.user_id) 
                user_id = user.id            
                if not cacher_data:
                    await interaction.response.send_message(f"No user found with cacher name `{cacher_name}`.", ephemeral=True)
                    return
            else:
                await interaction.response.send_message("No user found with the provided details.", ephemeral=True)
                return
            
            embed = discord.Embed(title=f"Game Admin Panel for {cacher_data.cacher_name}",
                      description=f"ID: {user_id} | <@{user_id}> | {user.name}\nStarted on {cacher_data.time_started} (make timestamp)",
                      colour=0xfb3737)
            embed.add_field(name="Balance",
                            value="G$"+str(cacher_data.balance),
                            inline=True)
            embed.add_field(name="Hides",
                            value=cacher_data.hides,
                            inline=True)
            embed.add_field(name="Finds",
                            value=cacher_data.finds,
                            inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        original_response = await interaction.original_response()
        await original_response.edit(embed=embed, view=UserManagerView(interaction.user, user, original_response))










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
 #       await master_log_message(interaction.guild, bot, interaction.command.name, f"{interaction.user.mention} ({interaction.user.name}) added G${amount} to {user.mention} ({user.name})'s balance, which is now G${newbal}.")    
        await log(interaction, f"{interaction.user.mention} ({interaction.user.name}) added G${amount} to {user.mention} ({user.name})'s balance, which is now G${newbal}.")

eco_a_commands = Game_Admin(name="game_admin", description="Geocaching Game Admin Commands.")

class UnpublishedHideEditModal(Modal, title="Edit Unpublished Hide"):
    def __init__(self, unpublished_hides, on_submit_callback):
        super().__init__()
        self.unpublished_hides = unpublished_hides
        self.on_submit_callback = on_submit_callback
        self.code_input = TextInput(label="Enter Hide Code", placeholder="e.g. GX1", required=True, max_length=10)
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        code = self.code_input.value.strip()
        # Find the hide with this code
        selected_hide = next((h for h in self.unpublished_hides if h.id.lower() == code.lower()), None)
        if not selected_hide:
            await interaction.response.send_message(f"No unpublished hide with code `{code}` found.", ephemeral=True)
            return
        await self.on_submit_callback(interaction, selected_hide)

class UnpublishedHidesView(View):
    def __init__(self, unpublished_hides, on_edit, on_continue, permitted_user_id, timeout=300):
        super().__init__(timeout=timeout)
        self.unpublished_hides = unpublished_hides
        self.on_edit = on_edit
        self.on_continue = on_continue
        self.permitted_user_id = permitted_user_id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        # Try to edit the message if possible
        try:
            # If the view was attached to a message, edit it to disable the buttons
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.permitted_user_id:
            await interaction.response.send_message(embed=YOUCANTUSETHIS, ephemeral=True)
            return
        modal = UnpublishedHideEditModal(self.unpublished_hides, self.on_edit)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.secondary)
    async def continue_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.permitted_user_id:
            await interaction.response.send_message(embed=YOUCANTUSETHIS, ephemeral=True)
            return
        await interaction.response.defer()  # Acknowledge the interaction to prevent 'interaction failed'
        await self.on_continue(interaction)

async def setup(bot):
    bot.tree.add_command(eco_commands)
    bot.tree.add_command(eco_a_commands)