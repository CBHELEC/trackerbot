import asyncio
import re
import discord
from collections import defaultdict, Counter
from game_functions.database import dbsetup, dbfunctions
from game_functions.general import gamefunctions, dicts
from game_functions.hide import hide_views
from game_functions.shop import prices
from game_functions.shop import views as shopviews
from game_functions.user_management import views
from game_functions.find import find_views
from game_functions.travel import travel_views
from game_functions.inventory import views as inventory_views
from game_functions.stickers import sticker_views, sticker_functions, sticker_config
from functions import static_var, checks
from discord import app_commands
from datetime import datetime, timedelta
from discord.ui import View, Button, Modal, TextInput
from discord.app_commands import CheckFailure

class ProfileView(View):
    """View for profile with buttons to view stickers and achievements."""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    async def on_timeout(self):
        """Disable all buttons when the view times out."""
        for child in self.children:
            child.disabled = True
    
    @discord.ui.button(label="📎 Stickers", style=discord.ButtonStyle.primary, row=1)
    async def stickers_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your profile!", ephemeral=True)
            return
        
        view = sticker_views.ProfileStickersView(self.user_id)
        embed = await view.get_stickers_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="🏆 Achievements", style=discord.ButtonStyle.primary, row=1)
    async def achievements_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your profile!", ephemeral=True)
            return
        
        view = sticker_views.ProfileAchievementsView(self.user_id)
        embed, files = await view.get_achievements_with_files()
        if files:
            await interaction.response.send_message(embed=embed, files=files, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class Economy(app_commands.Group):
    """Discaching Game Commands!"""
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Suspension Check."""
        async with dbsetup.Session() as session:
            usersetting = await dbfunctions.get_db_settings(session, interaction.user.id)
            if usersetting.suspended == 1:
                raise CheckFailure("USER_SUSPENDED")
        return True
    
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if isinstance(error, CheckFailure) and str(error) == "USER_SUSPENDED":
            async with dbsetup.Session() as session:
                usersetting = await dbfunctions.get_db_settings(session, interaction.user.id)
                embed = discord.Embed(title="<:denied:1336100920039313448> | Your account is suspended.",
                      description=f"You cannot use ANY Discaching commands while suspended.\nSuspension Reason: `{usersetting.suspension_reason}`.\nTo appeal your suspension, please [contact us](<https://trackerbot.xyz/contact>).",
                      colour=0xf40000)
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            return
        raise error

    @app_commands.command()
    async def balance(self, interaction: discord.Interaction):
        """View your current balances."""
        user = interaction.user
        user_id = user.id
        async with dbsetup.Session() as session:
            user_database_settings = await dbfunctions.get_db_settings(session, user_id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))            
                return
            else:
                embed = discord.Embed(title=f"{await dbfunctions.get_cacher_name(session, user_id)}'s Balances:",
                      colour=0xad7e66)

                embed.add_field(name=f"G$: {await dbfunctions.get_balance(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"FP: {await dbfunctions.get_fav_points_owned(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"Hides: {await dbfunctions.get_hides(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"Finds: {await dbfunctions.get_finds(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"TBs Discovered: {await dbfunctions.get_trackables_discovered(session, user_id)}",
                                value="",
                                inline=False)
                embed.add_field(name=f"TBs Owned: {await dbfunctions.get_trackables_owned(session, user_id)}",
                                value="",
                                inline=False)
                
                # Check for balance achievement
                balance = await dbfunctions.get_balance(session, user_id)
                await sticker_functions.check_and_award_achievement_sticker(
                    session, user_id, "balance", balance
                )
                
                await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.choices(option=[
        app_commands.Choice(name="Rural Locations", value="1"),
        app_commands.Choice(name="City Locations", value="2")
    ])
    async def locations(self, interaction: discord.Interaction, option: app_commands.Choice[str]):
        """Show the locations you can hide and find caches in."""
        if option.value == "1":
            embed = discord.Embed(
                title="Rural Geocaching Locations",
                description="Frostbrook Ridge – A remote, snow-covered mountain range in the far north, sparsely populated with only a few settlements. The frost here is intense, and the landscape is dominated by towering pines and frozen rivers.\n\nBlackrock Desert – A vast, dry expanse marked by jagged black rock formations and endless stretches of sandy dunes. The area is harsh, with scorching days and freezing nights, making it nearly impossible for anything to survive.\n\nEcho Lake Caverns – A series of limestone caves tucked deep within the forest, where the sound of water trickling through the walls creates an eerie, echoing effect. The caverns are home to rare species of bats and underground plants.\n\nStorm Island – A small, isolated island off the coast known for its unpredictable and frequent storms. Few fishermen dare to approach, and it remains largely uncharted by modern maps.\n\nDry Hollow Basin – An arid region with cracked earth and sparse vegetation, where ancient dry riverbeds tell stories of once-thriving communities now long abandoned. It’s an unforgiving place, where any trace of water is a rare find.\n\nMosswood Swamp – A damp, murky wetland full of thick moss and cypress trees. The air is heavy with the scent of decay, and it's said that the fog here often hides the movements of unseen creatures.\n\nSilverfall Bluff – A windswept plateau overlooking a wide river valley. The cliff faces here shimmer with silver-coloured rock formations, and the wind blows relentlessly, making it a difficult place to traverse.\n\nFrozen Hollow – A remote tundra, where temperatures regularly plunge below freezing. The landscape is dotted with glaciers and ice-covered ruins of old settlements, making it an inhospitable but fascinating place for explorers.\n\nOldport Ruins – The remains of an ancient port city once bustling with trade. Now submerged under a shallow layer of water, only the tops of old stone buildings poke through the surface, a haunting reminder of its former glory.\n\nWhistler’s Canyon – A narrow, wind-carved canyon where the winds create strange, howling noises as they pass through. It’s known for its rugged terrain and its reputation as a dangerous spot for hikers and travelers.",
                colour=0xad7e66)

            # embed.set_footer(text="This embed will self-destruct in 5 minutes. Click the 🗑️ icon to delete now.")

            # await interaction.response.send_message(embed=embed, view=gamefunctions.DeleteEmbedView())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            # sent_message = await interaction.original_response()
            # await asyncio.sleep(300)
            # await sent_message.delete()
            
        else:
            embed = discord.Embed(title="Rural Geocaching Locations",
                      description="Harrowsbrook – A small industrial town nestled by the river, known for its aging factories and old brick buildings. The town has a gritty, blue-collar vibe, with a rich history tied to its ironworks and textile mills.\n\nEverfield – A city surrounded by sprawling farmland and endless green fields, where the pace of life is slow, and the community is tight-knit. Known for its annual agricultural fairs and harvest festivals.\n\nLarkspur Crossing – A vibrant market town that acts as a key transportation hub, with people coming from all around to trade goods. The town is built around a large central square where street vendors and performers gather.\n\nBrunswick Harbor – A busy coastal city known for its bustling harbor, where fishing boats and cargo ships dock daily. The city has a lively waterfront, with seafood restaurants and bars overlooking the docks.\n\nAlderpoint – A hilltop city known for its historic architecture, with winding cobblestone streets and a centuries-old cathedral at the city’s heart. It has a more refined, older charm, with an abundance of parks and cultural institutions.",
                      colour=0xad7e66)
                      
            # embed.set_footer(text="This embed will self-destruct in 5 minutes. Click the 🗑️ icon to delete now.")

            # await interaction.response.send_message(embed=embed, view=gamefunctions.DeleteEmbedView())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            # sent_message = await interaction.original_response()
            # await asyncio.sleep(300)
            # await sent_message.delete()
            
    @app_commands.command()
    async def hide(self, interaction: discord.Interaction):
        """
        Hide your own cache.
        """
        await interaction.response.defer(ephemeral=True)
        async with dbsetup.Session() as session:
            user_id = interaction.user.id
            user_database_settings = await dbfunctions.get_db_settings(session, user_id)

            if user_database_settings.cacher_name is None:
                await interaction.followup.send(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.followup.send("Please enter your cacher name below.", ephemeral=True)
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return

            inventory_items = await dbfunctions.get_inventory(session, user_id)
            if not inventory_items:
                await interaction.followup.send(
                    "Your inventory is empty. You need a container to create a hide.",
                    ephemeral=True
                )
                return

            containers = [item for item in inventory_items if item.split('.')[0] in prices.SHOP_PRICES["containers"]]
            if not containers:
                await interaction.followup.send(
                    "You need a container in your inventory to create a hide.",
                    ephemeral=True
                )
                return

            hides = await dbfunctions.get_hides_by_user(session, user_id)
            
            unpublished_hides = [hide for hide in hides if hide.published == 0 and hide.review_status not in ["pending", "approved"]]
            if unpublished_hides:
                embed = discord.Embed(
                    title="Unpublished Hides",
                    description="It appears you have unpublished hides. Do you want to edit one of these or make a new hide?",
                    colour=0xAD6672
                )
                for hide in unpublished_hides:
                    embed.add_field(name=f"{hide.id} - {hide.name}", value=" ", inline=False)
                async def on_edit(interaction, selected_hide):
                    hide_data = await hide_views.load_hide_data_from_db(selected_hide.id)
                    if not hide_data:
                        await interaction.response.send_message("Could not load hide data.", ephemeral=True)
                        return
                    await uwu1.delete()
                    await hide_views.start_hide_configuration(interaction, hide_data, hide_id=selected_hide.id)
                async def on_continue(interaction):
                    item_counts = defaultdict(int)
                    item_to_container = {}
                    for container in containers:
                        first_container = container.split(',')[0] if ',' in container else container
                        parts = re.findall(r'\d+|\.\d+|[A-Za-z]', first_container)
                        if not parts:
                            continue
                        main_item = dicts.MAIN_INVENTORY.get(parts[0], "Unknown Item")
                        alt_items = [dicts.ALT_INVENTORY.get(part, "") for part in parts[1:]]
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
                    view = hide_views.ContainerSelectionView(deduped_items, item_to_container, user_id, original_message)
                    await uwu1.delete()
                    await original_message.edit(embed=embed2, view=view)
                permitted_user_id = interaction.user.id
                view = UnpublishedHidesView(unpublished_hides, on_edit, on_continue, permitted_user_id)
                uwu1 = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                return

            embed = discord.Embed(
                title="Select a Container for Your Hide",
                description="Below is a list of containers in your inventory. Enter the number corresponding to the container you want to use. No log means one from your inventory will be picked later.",
                colour=0xad7e66
            )
            
            item_counts = defaultdict(int)
            item_to_container = {}
            
            for container in containers:
                first_container = container.split(',')[0] if ',' in container else container
                parts = re.findall(r'\d+|\.\d+|[A-Za-z]', first_container)
                if not parts:
                    continue
                main_item = dicts.MAIN_INVENTORY.get(parts[0], "Unknown Item")
                alt_items = [dicts.ALT_INVENTORY.get(part, "") for part in parts[1:]]
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

            view = hide_views.ContainerSelectionView(deduped_items, item_to_container, user_id, original_message)
            await original_message.edit(embed=embed, view=view)
        
    @app_commands.command()
    async def cache_info(self, interaction: discord.Interaction, cache_id: str):
        """View information about a cache."""
        async with dbsetup.Session() as session:
            user_id = interaction.user.id
            user_db_settings = await dbfunctions.get_db_settings(session, user_id)
            if user_db_settings.cacher_name is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))            
                return
            else:
                cacher_db = await dbfunctions.get_db_settings(session, user_id)
                cacher_name = cacher_db.cacher_name
                hide = await dbfunctions.get_hide_by_id(session, cache_id)

                if not hide:
                    await interaction.response.send_message("Cache not found.", ephemeral=True)
                    return

                timestamp = int(hide.hidden_at.timestamp())

                hidden_at_str = f"<t:{timestamp}:F> (<t:{timestamp}:R>)"

                location_str = f"{hide.location_lat:.6f}, {hide.location_lon:.6f} ({hide.location_name})"

                formatted_hider_mention = f"<@{str(hide.user_id)}>"

                embed = discord.Embed(title=f"Cache Info: {hide.name}", colour=0xad7e66)
                embed.add_field(name="Cache ID", value=f"`{hide.id}`", inline=False)
                embed.add_field(name="Description", value=hide.description or "Not set", inline=False)
                embed.add_field(name="Cache Owner", value=f"{cacher_name} ({formatted_hider_mention})", inline=False)
                embed.add_field(name="Location", value=location_str, inline=False)

                embed.add_field(name="Difficulty", value=f"{hide.difficulty}/5", inline=True)
                embed.add_field(name="Terrain", value=f"{hide.terrain}/5", inline=True)
                embed.add_field(name="Size", value=f"{hide.size}", inline=True)
                embed.add_field(name="Hidden At", value=hidden_at_str, inline=False)

                await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def shop(self, interaction: discord.Interaction):
        """Browse the G$ shop."""
        async with dbsetup.Session() as session:
            user_db_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_db_settings.cacher_name is None:
                await interaction.response.send_message(f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.", ephemeral=True)
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))            
                return
            else:
                embed = discord.Embed(title="G$ Shop", description="Select a category from the dropdown to browse items.", colour=0xad7e66)
                await interaction.response.send_message(content=None, embed=embed)
                msg = await interaction.original_response()
                await interaction.edit_original_response(content=None, embed=embed, view=shopviews.ShopView(interaction, msg))
                
    @app_commands.command()
    async def inventory(self, interaction: discord.Interaction):
        """View what's in your inventory."""
        async with dbsetup.Session() as session:
            user_db_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_db_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return
            else:
                if not await dbfunctions.get_inventory(session, interaction.user.id):
                    await interaction.response.send_message("Your inventory is empty.", ephemeral=True)
                    return

                inventory_items = await dbfunctions.get_inventory_items_with_usage(session, interaction.user.id)
                
                item_data = {}
                for inv_item in inventory_items:
                    item_id = inv_item.item_id
                    if item_id not in item_data:
                        item_data[item_id] = {}
                    usage_key = inv_item.usage if inv_item.usage is not None else None
                    if usage_key not in item_data[item_id]:
                        item_data[item_id][usage_key] = 0
                    item_data[item_id][usage_key] += 1

                # Create initial embed with category selection message (like shop)
                embed = discord.Embed(
                    title=f"{user_db_settings.cacher_name}'s Inventory",
                    description="Select a category from the dropdown to view your items.",
                    colour=0xad7e66
                )

                await interaction.response.send_message(embed=embed)
                msg = await interaction.original_response()
                await interaction.edit_original_response(embed=embed, view=inventory_views.InventoryView(interaction, msg, item_data, user_db_settings.cacher_name))

    @app_commands.command()
    async def leaderboard(self, interaction: discord.Interaction):
        """View leaderboards for various game statistics."""
        from game_functions.leaderboard import views as leaderboard_views
        
        async with dbsetup.Session() as session:
            # Start with money leaderboard by default
            leaderboard_data = await leaderboard_views.get_leaderboard_data(session, "money", 10)
            embed = leaderboard_views.format_leaderboard_embed("money", leaderboard_data, interaction.client)
            
            await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            await interaction.edit_original_response(embed=embed, view=leaderboard_views.LeaderboardView(interaction, msg, interaction.client))

    @app_commands.command()
    async def profile(self, interaction: discord.Interaction):
        """View your detailed profile with stats, badges, and stickers."""
        from votefunctions import get_total, get_streak
        
        async with dbsetup.Session() as session:
            user_db_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_db_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return
            
            cacher_name = user_db_settings.cacher_name
            
            # Get all stats
            balance = await dbfunctions.get_balance(session, interaction.user.id)
            fav_points_owned = await dbfunctions.get_fav_points_owned(session, interaction.user.id)
            fav_points_received = await dbfunctions.get_fav_points_recieved(session, interaction.user.id)
            hides = await dbfunctions.get_hides(session, interaction.user.id)
            finds = await dbfunctions.get_finds(session, interaction.user.id)
            logs_received = await dbfunctions.get_logs_recieved(session, interaction.user.id)
            logs_created = await dbfunctions.get_logs_created(session, interaction.user.id)
            trackables_owned = await dbfunctions.get_trackables_owned(session, interaction.user.id)
            trackables_activated = await dbfunctions.get_trackables_activated(session, interaction.user.id)
            trackables_discovered = await dbfunctions.get_trackables_discovered(session, interaction.user.id)
            is_reviewer = user_db_settings.is_reviewer == 1
            
            # Get vote stats
            total_votes = await get_total(interaction.user.id)
            vote_streak = await get_streak(interaction.user.id)
            
            # Calculate time since started
            time_started_str = "Not set"
            if user_db_settings.time_started:
                time_started = user_db_settings.time_started
                time_started_str = f"<t:{int(time_started.timestamp())}:D>"
            
            # Create embed
            embed = discord.Embed(
                title=f"{cacher_name}'s Profile",
                colour=0xad7e66
            )
            
            # Basic Stats (not in balance)
            embed.add_field(
                name="📊 Basic Stats",
                value=f"**Finds:** {finds:,}\n**Hides:** {hides:,}\n**Balance:** G${balance:,}\n**Favorite Points:** {fav_points_owned:,}\n**FP Received:** {fav_points_received:,}",
                inline=True
            )
            
            # Logging Stats
            embed.add_field(
                name="📝 Logging Stats",
                value=f"**Logs Created:** {logs_created:,}\n**Logs Received:** {logs_received:,}",
                inline=True
            )
            
            # Trackable Stats
            embed.add_field(
                name="🪙 Trackable Stats",
                value=f"**Owned:** {trackables_owned:,}\n**Activated:** {trackables_activated:,}\n**Discovered:** {trackables_discovered:,}",
                inline=True
            )
            
            # Vote Stats
            embed.add_field(
                name="🗳️ Vote Stats",
                value=f"**Total Votes:** {total_votes:,}\n**Vote Streak:** {vote_streak:,}",
                inline=True
            )
            
            # Additional Info
            additional_info = []
            if is_reviewer:
                additional_info.append("👮 **Reviewer**")
            if additional_info:
                embed.add_field(
                    name="ℹ️ Additional Info",
                    value="\n".join(additional_info),
                    inline=False
                )
            
            # Footer with time started
            embed.set_footer(text=f"Started: {time_started_str}")
            
            # Create view with buttons
            view = ProfileView(interaction.user.id)
            
            await interaction.response.send_message(embed=embed, view=view)

    async def cache_id_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete function for cache IDs with distance sorting."""
        async with dbsetup.Session() as session:
            hides = await dbfunctions.get_published_hides(session)
            if not hides:
                return []
            
            user_location = await dbfunctions.get_user_location(session, interaction.user.id)
            user_lat = user_location.location_lat if user_location else None
            user_lon = user_location.location_lon if user_location else None
            
            cache_info_list = []
            for hide in hides:
                if not hide.location_lat or not hide.location_lon:
                    distance = float('inf')  
                elif user_lat and user_lon:
                    distance = gamefunctions.calculate_distance(
                        user_lat, user_lon,
                        hide.location_lat, hide.location_lon
                    )
                else:
                    distance = float('inf')  
                
                cache_info_list.append({
                    'id': hide.id,
                    'name': hide.name,
                    'distance': distance
                })
            
            cache_info_list.sort(key=lambda x: x['distance'])
            
            current_upper = current.upper().strip()
            
            if current_upper:
                filtered = [
                    cache for cache in cache_info_list
                    if current_upper in cache['id'].upper() or current_upper in cache['name'].upper()
                ]
            else:
                filtered = cache_info_list
            
            filtered = filtered[:25]
            
            choices = []
            for cache in filtered:
                if cache['distance'] == float('inf'):
                    distance_str = "No location"
                else:
                    distance_str = f"{cache['distance']:.2f}km away"
                
                name = f"{cache['id']} - {cache['name']} ({distance_str})"
                choices.append(app_commands.Choice(name=name, value=cache['id']))
            
            return choices
    
    @app_commands.command()
    @app_commands.describe(cache_id="The ID of the cache you want to travel to")
    @app_commands.autocomplete(cache_id=cache_id_autocomplete)
    async def travel(self, interaction: discord.Interaction, cache_id: str):
        """
        Travel to a cache location. You need a vehicle or ticket in your inventory.
        """
        async with dbsetup.Session() as session:
            user_id = interaction.user.id
            user_database_settings = await dbfunctions.get_db_settings(session, user_id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return
            
            cache_id = cache_id.strip().upper()
            
            hide = await dbfunctions.get_hide_by_id(session, cache_id)
            if not hide:
                await interaction.response.send_message(
                    f"Cache `{cache_id}` not found.",
                    ephemeral=True
                )
                return
            
            if not hide.location_lat or not hide.location_lon:
                await interaction.response.send_message(
                    f"Cache `{cache_id}` does not have valid coordinates.",
                    ephemeral=True
                )
                return
            
            user_location = await dbfunctions.get_user_location(session, user_id)
            
            if user_location.arrival_time and user_location.arrival_time > datetime.now():
                time_remaining = user_location.arrival_time - datetime.now()
                traveling_to = user_location.traveling_to_cache_id
                cache_id_display = traveling_to.split(":")[1] if traveling_to and traveling_to.startswith("PARTIAL:") else traveling_to
                await interaction.response.send_message(
                    f"You are already travelling to cache `{cache_id_display}`. "
                    f"Arrival in: {gamefunctions.format_timedelta(time_remaining)}",
                    ephemeral=True
                )
                return
            
            distance_km = gamefunctions.calculate_distance(
                user_location.location_lat,
                user_location.location_lon,
                hide.location_lat,
                hide.location_lon
            )
            
            inventory_items = await dbfunctions.get_inventory(session, user_id)
            inventory_items_with_usage = await dbfunctions.get_inventory_items_with_usage(session, user_id)
            available_vehicles = dbfunctions.get_all_vehicles_from_inventory(inventory_items)
            
            if not available_vehicles:
                await interaction.response.send_message(
                    "You don't have any vehicles or tickets in your inventory. Visit the shop to purchase one!",
                    ephemeral=True
                )
                return
            
            vehicle_remaining_distances = {}
            for inv_item in inventory_items_with_usage:
                vehicle_id = inv_item.item_id
                base_id = vehicle_id.split('.')[0] if '.' in vehicle_id else vehicle_id
                
                if base_id in dicts.VEHICLE_MAX_DISTANCES:
                    if base_id not in vehicle_remaining_distances:
                        max_dist = dicts.VEHICLE_MAX_DISTANCES.get(base_id, 100)
                        remaining = inv_item.usage if inv_item.usage is not None else max_dist
                        vehicle_remaining_distances[base_id] = remaining
            
            travel_data = {
                "user_id": user_id,
                "cache_id": cache_id,
                "hide": hide,
                "user_location": user_location,
                "inventory_items": inventory_items,
                "distance_km": distance_km,
                "vehicle_remaining_distances": vehicle_remaining_distances
            }
            
            if len(available_vehicles) > 1:
                embed = discord.Embed(
                    title="🚗 Select Vehicle",
                    description=f"Select a vehicle to travel to cache **{hide.name}** ({cache_id})",
                    colour=0xad7e66
                )
                embed.add_field(name="Current Location", value=f"({user_location.location_lat:.6f}, {user_location.location_lon:.6f})", inline=False)
                embed.add_field(name="Destination", value=f"({hide.location_lat:.6f}, {hide.location_lon:.6f})", inline=False)
                embed.add_field(name="Distance", value=f"{distance_km:.2f} km", inline=False)
                
                view = travel_views.VehicleSelectionView(travel_data, available_vehicles)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            else:
                vehicle_id, vehicle_name, speed_kmh, max_distance = available_vehicles[0]
                
                actual_travel_distance = min(distance_km, max_distance)
                reached_destination = distance_km <= max_distance
                remaining_distance = distance_km - actual_travel_distance if not reached_destination else 0
                
                if reached_destination:
                    destination_lat = hide.location_lat
                    destination_lon = hide.location_lon
                    traveling_to = cache_id
                else:
                    destination_lat, destination_lon = gamefunctions.calculate_point_along_route(
                        user_location.location_lat,
                        user_location.location_lon,
                        hide.location_lat,
                        hide.location_lon,
                        actual_travel_distance,
                        distance_km
                    )
                    traveling_to = cache_id  
                
                travel_time = gamefunctions.calculate_travel_time(actual_travel_distance, speed_kmh)
                arrival_time = datetime.now() + travel_time
                
                if reached_destination:
                    embed = discord.Embed(
                        title="🚗 Travel Confirmation",
                        description=f"Confirm travel to cache **{hide.name}** ({cache_id})?",
                        colour=0xad7e66
                    )
                else:
                    embed = discord.Embed(
                        title="🚗 Partial Travel Confirmation",
                        description=f"Confirm partial travel towards cache **{hide.name}** ({cache_id})?\n*You won't reach the destination with this vehicle.*",
                        colour=0xad7e66
                    )
                
                embed.add_field(name="Current Location", value=f"({user_location.location_lat:.6f}, {user_location.location_lon:.6f})", inline=False)
                if reached_destination:
                    embed.add_field(name="Destination", value=f"({hide.location_lat:.6f}, {hide.location_lon:.6f})", inline=False)
                else:
                    embed.add_field(name="Intermediate Destination", value=f"({destination_lat:.6f}, {destination_lon:.6f})", inline=False)
                    embed.add_field(name="Remaining Distance", value=f"{remaining_distance:.2f} km to cache", inline=False)
                
                embed.add_field(name="Distance travelling", value=f"{actual_travel_distance:.2f} km", inline=True)
                embed.add_field(name="Vehicle", value=f"{vehicle_name} ({speed_kmh} km/h)", inline=True)
                embed.add_field(name="Time", value=f"<t:{int(arrival_time.timestamp())}:R> ({gamefunctions.format_timedelta(travel_time)})", inline=False)
                embed.set_footer(text="You will get a DM when you arrive, but only if your DMs are enabled.")
                
                travel_data.update({
                    "vehicle_id": vehicle_id,
                    "vehicle_name": vehicle_name,
                    "speed_kmh": speed_kmh,
                    "destination_lat": destination_lat,
                    "destination_lon": destination_lon,
                    "traveling_to": traveling_to,
                    "reached_destination": reached_destination,
                    "arrival_time": arrival_time,
                    "actual_travel_distance": actual_travel_distance,
                    "remaining_distance": remaining_distance,
                    "travel_time": travel_time
                })
                
                view = travel_views.TravelConfirmationView(travel_data)
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command()
    @app_commands.describe(cache_id="The ID of the cache to check distance to")
    @app_commands.autocomplete(cache_id=cache_id_autocomplete)
    async def distance_to_cache(self, interaction: discord.Interaction, cache_id: str):
        """
        Check the distance from your current location to a cache.
        """
        async with dbsetup.Session() as session:
            user_id = interaction.user.id
            user_database_settings = await dbfunctions.get_db_settings(session, user_id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return
            
            cache_id = cache_id.strip().upper()
            hide = await dbfunctions.get_hide_by_id(session, cache_id)
            if not hide:
                await interaction.response.send_message(
                    f"Cache `{cache_id}` not found.",
                    ephemeral=True
                )
                return
            
            if not hide.location_lat or not hide.location_lon:
                await interaction.response.send_message(
                    f"Cache `{cache_id}` does not have valid coordinates.",
                    ephemeral=True
                )
                return
            
            user_location = await dbfunctions.get_user_location(session, user_id)
            
            if user_location.arrival_time and user_location.arrival_time <= datetime.now() and user_location.traveling_to_cache_id:
                traveling_to = user_location.traveling_to_cache_id
                if traveling_to.startswith("PARTIAL:"):
                    parts = traveling_to.split(":")
                    if len(parts) >= 4:
                        dest_lat = float(parts[2])
                        dest_lon = float(parts[3])
                        user_location = await dbfunctions.complete_travel(session, user_id, dest_lat, dest_lon)
                else:
                    full_hide = await dbfunctions.get_hide_by_id(session, traveling_to)
                    if full_hide and full_hide.location_lat and full_hide.location_lon:
                        user_location = await dbfunctions.complete_travel(session, user_id, full_hide.location_lat, full_hide.location_lon)
                    else:
                        await dbfunctions.clear_travel_status(session, user_id)
                        user_location = await dbfunctions.get_user_location(session, user_id)
            
            distance_km = gamefunctions.calculate_distance(
                user_location.location_lat,
                user_location.location_lon,
                hide.location_lat,
                hide.location_lon
            )
            
            embed = discord.Embed(
                title="📏 Distance to Cache",
                description=f"Distance from your current location to cache **{hide.name}** ({cache_id})",
                colour=0xad7e66
            )
            
            embed.add_field(
                name="Your Location",
                value=f"Lat: {user_location.location_lat:.6f}\nLon: {user_location.location_lon:.6f}",
                inline=True
            )
            embed.add_field(
                name="Cache Location",
                value=f"Lat: {hide.location_lat:.6f}\nLon: {hide.location_lon:.6f}",
                inline=True
            )
            embed.add_field(
                name="Distance",
                value=f"**{distance_km:.2f} km**",
                inline=False
            )
            
            if hide.location_name:
                embed.add_field(
                    name="Location",
                    value=hide.location_name,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command()
    async def location(self, interaction: discord.Interaction):
        """
        View your current location on the map.
        """
        async with dbsetup.Session() as session:
            user_id = interaction.user.id
            user_database_settings = await dbfunctions.get_db_settings(session, user_id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return
            
            user_location = await dbfunctions.get_user_location(session, user_id)
            
            if user_location.arrival_time and user_location.arrival_time <= datetime.now() and user_location.traveling_to_cache_id:
                traveling_to = user_location.traveling_to_cache_id
                if traveling_to.startswith("PARTIAL:"):
                    parts = traveling_to.split(":")
                    if len(parts) >= 4:
                        dest_lat = float(parts[2])
                        dest_lon = float(parts[3])
                        user_location = await dbfunctions.complete_travel(session, user_id, dest_lat, dest_lon)
                else:
                    hide = await dbfunctions.get_hide_by_id(session, traveling_to)
                    if hide and hide.location_lat and hide.location_lon:
                        user_location = await dbfunctions.complete_travel(session, user_id, hide.location_lat, hide.location_lon)
                    else:
                        await dbfunctions.clear_travel_status(session, user_id)
                        user_location = await dbfunctions.get_user_location(session, user_id)
            
            embed = discord.Embed(
                title="📍 Your Location",
                colour=0xad7e66
            )
            embed.add_field(name="Coordinates", value=f"Lat: {user_location.location_lat:.6f}\nLon: {user_location.location_lon:.6f}", inline=False)
            
            if user_location.arrival_time and user_location.arrival_time > datetime.now():
                time_remaining = user_location.arrival_time - datetime.now()
                traveling_to = user_location.traveling_to_cache_id
                cache_id = traveling_to.split(":")[1] if traveling_to.startswith("PARTIAL:") else traveling_to
                is_partial = traveling_to.startswith("PARTIAL:")
                travel_desc = f"To cache `{cache_id}`" if not is_partial else f"Towards cache `{cache_id}` (partial travel)"
                embed.add_field(
                    name="travelling",
                    value=f"{travel_desc}\nArrival: <t:{int(user_location.arrival_time.timestamp())}:R>",
                    inline=False
                )
            else:
                embed.add_field(name="Status", value="📍 Not travelling", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command()
    async def find(self, interaction: discord.Interaction):
        """
        Find a cache and log it.
        """
        modal = find_views.FindCacheModal()
        await interaction.response.send_modal(modal)

    @app_commands.command()
    @app_commands.describe(cache_id="The ID of the cache to view finds for")
    @app_commands.autocomplete(cache_id=cache_id_autocomplete)
    async def cache_finds(self, interaction: discord.Interaction, cache_id: str):
        """
        Retrieve all finds for a specific cache.
        
        Args:
            cache_id (str): The ID of the cache to retrieve finds for.
        """
        async with dbsetup.Session() as session:
            user_database_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return

            user_id = interaction.user.id
            cache_id = cache_id.strip().upper()
            hide = await dbfunctions.get_hide_by_id(session, cache_id)
            if not hide:
                await interaction.response.send_message(f"Cache `{cache_id}` not found.", ephemeral=True)
                return

            finds = await dbfunctions.get_finds_for_cache(session, cache_id)

            if not finds:
                await interaction.response.send_message(f"No finds have been logged for cache `{cache_id}` yet.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"Finds for Cache: {hide.name}",
                description=f"Cache ID: `{cache_id}`\nTotal Finds: **{len(finds)}**",
                colour=0xad7e66
            )

            for find in finds:
                finder_db = await dbfunctions.get_db_settings(session, find.user_id)
                finder_name = finder_db.cacher_name if finder_db and finder_db.cacher_name else f"User {find.user_id}"
                log_content = find.log_content if find.log_content else "No log content provided."
                fp_status = "✅" if find.fp_status == 1 else "❌"
                embed.add_field(
                    name=f"Finder: {finder_name}",
                    value=f"**Log:** {log_content}\n**FP:** {fp_status}",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command()
    async def tb_activate(self, interaction: discord.Interaction, private_code: str):
        """Activate a trackable using its private code.
        
        Args:
            private_code (str): The private code of the trackable to activate.
        """
        user_id = interaction.user.id
        async with dbsetup.Session() as session:
            user_database_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return

            trackable = await dbsetup.activate_trackable(session, user_id, private_code)
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
        async with dbsetup.Session() as session:
            user_database_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return
    
            trackable = await dbfunctions.get_trackable(public_code)

            if not trackable:
                await interaction.response.send_message(
                    f"Trackable with public code `{public_code}` not found.",
                    ephemeral=True
                )
                return

            activated_time_dt = datetime.strptime(trackable.activated_time.split('.')[0], "%Y-%m-%d %H:%M:%S") if trackable.activated_time else "N/A"
            unix_timestamp = int(activated_time_dt.timestamp()) if activated_time_dt != "N/A" else None

            discoveries = await dbfunctions.get_trackable_discoveries(session, public_code)

            embed = discord.Embed(
                title=f"Trackable Details",
                colour=0xad7e66
            )
            embed.add_field(name="Public Code", value=trackable.public_code, inline=True)
            embed.add_field(name="Owner", value=await dbfunctions.get_cacher_name(session, trackable.user_id), inline=True)
            embed.add_field(name="Activation Status", value="✅ Activated" if trackable.activated == 1 else "❌ Not Activated", inline=False)
            embed.add_field(name="Activation Date", value=f"<t:{unix_timestamp}:R>" if trackable.activated_time else "❌ Not Activated", inline=False)

            if discoveries:
                for discovery in discoveries:
                    cacher_name = await dbfunctions.get_db_settings(session, discovery.user_id if discovery else None).cacher_name
                    discover_date = int(datetime.strptime(discovery.discover_date, "%Y-%m-%d %H:%M:%S").timestamp()) if discovery.discover_date else "N/A"
                    embed.add_field(
                        name=f"Discovered by {cacher_name}",
                        value=f"**Date:** {f'<t:{discover_date}:f> (<t:{discover_date}:R>)' if discover_date != 'N/A' else 'N/A'}\n**Log:** {discovery.discover_log or 'No log provided.'}",
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
        async with dbsetup.Session() as session:
            user_database_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return

            trackable = await dbfunctions.get_trackable(session, private_code)

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

            existing_discovery = await dbfunctions.get_trackable_discoveries(session, private_code).scalars().first()

            if existing_discovery:
                await interaction.response.send_message(
                    f"You have already discovered this trackable.",
                    ephemeral=True
                )
                return

            discover_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await dbsetup.add_tb_discovery(session, interaction.user.id, private_code, discover_date, log)
            tbdis = await dbfunctions.get_trackables_discovered(session, interaction.user.id)
            await dbsetup.update_trackables_discovered(session, interaction.user.id, tbdis + 1)

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
        """Claim daily G$ rewards."""
        async with dbsetup.Session() as session:
            user_database_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_database_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return

            getlastclaim = await dbfunctions.get_lastclaim(session, interaction.user.id)
            if getlastclaim:
                if getlastclaim.last_withdraw is not None:
                    last_withdraw_date = datetime.strptime(getlastclaim.last_withdraw, "%Y-%m-%d %H:%M:%S").date() 
                    current_date = datetime.now().date()  

                    if current_date > last_withdraw_date:
                        currentbalance = await dbfunctions.get_balance(session, interaction.user.id)
                        newbalance = currentbalance + 25
                        await dbfunctions.update_balance(session, interaction.user.id, newbalance)
                        await dbfunctions.set_lastclaim(session, interaction.user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        await interaction.response.send_message(f"Daily Reward claimed! New Balance: G${newbalance}", ephemeral=True)
                    else:
                        next_reset = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                        reset_timestamp = int(next_reset.timestamp())
                        await interaction.response.send_message(f"You have already claimed your daily reward today. This resets in <t:{reset_timestamp}:R>.", ephemeral=True)
                else:
                    currentbalance = await dbfunctions.get_balance(session, interaction.user.id)
                    newbalance = currentbalance + 25
                    await dbfunctions.update_balance(session, interaction.user.id, newbalance)
                    await dbfunctions.set_lastclaim(session, interaction.user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    await interaction.response.send_message(f"Daily Reward claimed! New Balance: G${newbalance}", ephemeral=True)
            else:
                currentbalance = await dbfunctions.get_balance(session, interaction.user.id)
                newbalance = currentbalance + 25
                await dbfunctions.update_balance(session, interaction.user.id, newbalance)
                await dbfunctions.set_lastclaim(session, interaction.user.id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                await interaction.response.send_message(f"Daily Reward claimed! New Balance: G${newbalance}", ephemeral=True)
        
    @app_commands.command()
    async def gift(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Gift G$ to another user."""
        with dbsetup.Session() as session:
            userbal = await dbfunctions.get_balance(session, interaction.user.id)
            if amount <= 0:
                await interaction.response.send_message("⛔ | You must gift at least G$1.", ephemeral=True)
                return
            if userbal < amount:
                await interaction.response.send_message(f"⛔ | You do not have enough G$. Current balance: G${userbal}.", ephemeral=True)
                return
            recipientbal = await dbfunctions.get_balance(session, user.id)
            await dbfunctions.update_balance(session, user.id, recipientbal + amount)
            await interaction.response.send_message(f"🎁 | Successfully gifted G${amount} to {user.mention}!")
    
    @app_commands.command()
    @app_commands.describe(amount="Number of vote crates to open (default: 1)")
    async def open_votecrate(self, interaction: discord.Interaction, amount: int = 1):
        """Open vote crate(s) to receive random rewards."""
        async with dbsetup.Session() as session:
            user_db_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_db_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return
            
            # Validate amount
            if amount < 1:
                await interaction.response.send_message(
                    "You must open at least 1 vote crate!",
                    ephemeral=True
                )
                return
            
            # Check if user has enough vote crates
            inventory_items = await dbfunctions.get_inventory(session, interaction.user.id)
            vote_crate_count = inventory_items.count("48")
            
            if vote_crate_count == 0:
                await interaction.response.send_message(
                    "You don't have any vote crates to open! Vote on top.gg or DBL to earn vote crates.",
                    ephemeral=True
                )
                return
            
            if amount > vote_crate_count:
                await interaction.response.send_message(
                    f"You only have {vote_crate_count} vote crate(s)! You can't open {amount}.",
                    ephemeral=True
                )
                return
            
            # Accumulate rewards from all crates
            total_money = 0
            all_reward_items = []
            all_reward_names = []
            
            for _ in range(amount):
                # Select rewards based on probabilities
                reward_items, money_amount = gamefunctions.select_vote_crate_reward()
                total_money += money_amount
                
                # Remove one vote crate
                await dbfunctions.remove_inv_item(session, interaction.user.id, "48")
                
                # Add all reward items and track names
                for item_id in reward_items:
                    await dbfunctions.add_inv_item(session, interaction.user.id, item_id)
                    all_reward_items.append(item_id)
                    
                    # Get display name for the item
                    parts = re.findall(r'\d+|\.\d+|[A-Za-z]', item_id)
                    if not parts:
                        all_reward_names.append("Unknown Item")
                        continue
                    
                    main_item = dicts.MAIN_INVENTORY.get(parts[0], "Unknown Item")
                    
                    # Handle containers (which use get_container_name for proper formatting)
                    if parts[0] in ["7", "8", "9", "11", "13", "14", "15", "16", "19", "20", "21"]:
                        all_reward_names.append(gamefunctions.get_container_name(item_id))
                    else:
                        # For other items, build the name
                        alt_items = [dicts.ALT_INVENTORY.get(part, "") for part in parts[1:]]
                        alt_items = [alt for alt in alt_items if alt]
                        if alt_items:
                            item_name = f"{main_item} {' '.join(alt_items)}".strip()
                        else:
                            item_name = main_item
                        all_reward_names.append(item_name)
            
            # Add money
            current_balance = await dbfunctions.get_balance(session, interaction.user.id)
            await dbfunctions.update_balance(session, interaction.user.id, current_balance + total_money)
            
            # Create embed
            title = "🎁 Vote Crate Opened!" if amount == 1 else f"🎁 {amount} Vote Crates Opened!"
            description = f"You opened {'a vote crate' if amount == 1 else f'{amount} vote crates'} and received:" if amount == 1 else f"You opened {amount} vote crates and received:"
            
            embed = discord.Embed(
                title=title,
                description=description,
                colour=0xad7e66
            )
            
            # Add money field
            embed.add_field(
                name="💰 Money",
                value=f"**G${total_money}**",
                inline=False
            )
            
            # Add items field - group duplicates
            if all_reward_names:
                item_counts = Counter(all_reward_names)
                items_text = "\n".join([f"• **{count}x {name}**" if count > 1 else f"• **{name}**" for name, count in sorted(item_counts.items())])
                
                # Discord embed field value limit is 1024 characters
                if len(items_text) > 1024:
                    # Truncate and add note
                    items_text = items_text[:1000] + "\n... (and more items)"
                
                embed.add_field(
                    name="📦 Items",
                    value=items_text,
                    inline=False
                )
            
            remaining = vote_crate_count - amount
            embed.set_footer(text=f"You have {remaining} vote crate(s) remaining." if remaining > 0 else "You have no vote crates remaining.")
            
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command()
    async def stickers(self, interaction: discord.Interaction):
        """View your sticker book with achievements and collectibles."""
        async with dbsetup.Session() as session:
            user_db_settings = await dbfunctions.get_db_settings(session, interaction.user.id)
            if user_db_settings.cacher_name is None:
                await interaction.response.send_message(
                    f"It appears you haven't set your cacher name yet! Please press the button below to enter your name and start caching.",
                    ephemeral=True
                )
                original_message = await interaction.original_response()
                await original_message.edit(view=hide_views.CacherNameView(original_message))
                return
            
            view = sticker_views.StickerBookView(interaction.user.id, "achievements", "all")
            embed, files = await view.get_achievements_embed_with_files(session)
            if files:
                await interaction.response.send_message(embed=embed, view=view, files=files, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
eco_commands = Economy(name="game", description="Geocaching Game Commands.")

class Game_Admin(app_commands.Group):
    """Geocaching Game Admin Commands!"""

    @app_commands.command()
    @checks.is_dev()
    async def userpanel(self, interaction: discord.Interaction, dc_user: discord.Member = None, user_id: str = None, cacher_name: str = None):
        """
        Open an Admin panel for the specified member.
        
        Args:
            dc_user (discord.Member): The user to manage. 
            user_id (str): The ID of the user to manage. 
            cacher_name (str): The cacher name of the user to manage.
        """
        if not (dc_user or user_id or cacher_name):
            await interaction.response.send_message("You must provide either a user, user ID, or cacher name.", ephemeral=True)
            return

        async with dbsetup.Session() as session:
            if dc_user: 
                cacher_data = await dbfunctions.get_db_settings(session, dc_user.id)
                if not cacher_data:
                    await interaction.response.send_message(f"No user data found for {dc_user.mention}.", ephemeral=True)
                    return
                user_id = dc_user.id
                user = dc_user
            elif user_id: 
                user_id = int(user_id)
                cacher_data = await dbfunctions.get_db_settings(session, user_id)
                if not cacher_data:
                    await interaction.response.send_message(f"No user data found for user ID `{user_id}`.", ephemeral=True)
                    return
                # Try to get user from cache (doesn't require Members intent)
                user = interaction.client.get_user(user_id)
                if not user:
                    # Create a minimal user-like object if not in cache
                    class MinimalUser:
                        def __init__(self, user_id, name):
                            self.id = user_id
                            self.name = name
                            self.mention = f"<@{user_id}>"
                    user = MinimalUser(user_id, cacher_data.cacher_name or f"User {user_id}")
            elif cacher_name: 
                cacher_data = await dbfunctions.get_cacher_info(session, cacher_name)
                if not cacher_data:
                    await interaction.response.send_message(f"No user found with cacher name `{cacher_name}`.", ephemeral=True)
                    return
                user_id = cacher_data.user_id
                # Try to get user from cache (doesn't require Members intent)
                user = interaction.client.get_user(user_id)
                if not user:
                    # Create a minimal user-like object if not in cache
                    class MinimalUser:
                        def __init__(self, user_id, name):
                            self.id = user_id
                            self.name = name
                            self.mention = f"<@{user_id}>"
                    user = MinimalUser(user_id, cacher_name)
            else:
                await interaction.response.send_message("No user found with the provided details.", ephemeral=True)
                return
            
            if cacher_data.time_started:
                timestamp = int(cacher_data.time_started.timestamp())
                time_started_str = f"<t:{timestamp}:F> (<t:{timestamp}:R>)"
            else:
                time_started_str = "Not Found"
            suspended_status = "Yes" if cacher_data.suspended == 1 else "No"
            embed = discord.Embed(title=f"Game Admin Panel for {cacher_data.cacher_name}",
                      description=f"ID: {user_id} | <@{user_id}> | {user.name}\nStarted on {time_started_str}\nSuspended: {suspended_status}",
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
        await original_response.edit(embed=embed, view=views.UserManagerView(interaction.user, user, original_response))

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
        try:
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.primary)
    async def edit_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.permitted_user_id:
            await interaction.response.send_message(embed=static_var.YOUCANTUSETHIS, ephemeral=True)
            return
        modal = UnpublishedHideEditModal(self.unpublished_hides, self.on_edit)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.secondary)
    async def continue_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.permitted_user_id:
            await interaction.response.send_message(embed=static_var.YOUCANTUSETHIS, ephemeral=True)
            return
        await interaction.response.defer()  
        await self.on_continue(interaction)

async def setup(bot):
    bot.tree.add_command(eco_commands)
    bot.tree.add_command(eco_a_commands)