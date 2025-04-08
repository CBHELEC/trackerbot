import discord
from discord.ui import Select, Button, View, Modal, TextInput
import typing
from economy import *
import re
import string
from discord import Embed

class DeleteEmbedView(View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="🗑️", style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

containersembed = discord.Embed(title="Containers",
                      description="__Container Type__:\nPlastic Container [ID: **7**] (Price: **G$15**)\n3D printed Container [ID: **8**] (Price: **G$15**)\nDecoy Rock [ID: **9**] (Price: **G$30**)\nDecoy Electric Metal Plate (Only Comes In ***__S__***) [ID: **10**] (Price: **G$45**)\nBottle Cap Container (Only Comes In ***__XS__*** And ***__S__***) [ID: **11**] (Price: **G$20**)\nDecoy Bolt [ID: **12**] (Price: **G$10**)\nBison Tube (Only Comes in ***__XS__***, ***__S__***, And ***__M__***) [ID: **13**] (Price: **G$5**)\nAmmo Can (Only Comes in ***__M__***, ***__L__***, And ***__XL__***) [ID: **14**] (Price: **G$50**)\nPill Bottle (Only Comes in ***__XS__***, ***__S__***, And ***__M__***) [ID: **15**] (Price: **G$5**)\nMagnetic Container (Only Comes in ***__XS__*** And ***__S__***) [ID: **16**] (Price: **G$10**)\nMaze Container (Only Comes In ***__M__***) [ID: **22**] (Price: **G$55**)\n\n__Container Size__:\n***__XS__*** Container [ID: **.6**] (Price: **G$5**)\n***__S__*** Container [ID: **.7**] (Price: **G$10**)\n***__M__*** Container [ID: **.8**] (Price: **G$20**)\n***__L__*** Container [ID: **.9**] (Price: **G$40**)\n***__XL__*** Container [ID: **.10**] (Price: **G$80**)\n\n__Container Colour__:\nRed [ID: **.11**]\nOrange [ID: **.12**]\nYellow [ID: **.13**]\nGreen [ID: **.14**]\nBlue [ID: **.15**]\nPurple [ID: **.16**]\nBlack [ID: **.17**]\n\n__Add a log__ *(plain paper)*: +**G$1** [ID: **L**]",
                      colour=0xad7e66)

writingembed = discord.Embed(title="Writing Instruments", 
              description="""__Pen Type__:\nEZWrite [ID: **1**] {Uses: **10**} (Price: **G$5**)\nGlideMaster [ID: **2**] {Uses: **30**} (Price: **G$15**)\nCosmoScribe [ID: **3**] {Uses: **100**} (Price: **G$50**)\n\n__Pen Colour__:\nRed [ID: **.1**]\nGreen [ID: **.2**]\nBlue [ID: **.3**]\nBlack [ID: **.4**]\nPurple [ID: **.5**]\n\n__Pencil Type__:\nRegular Pencil [ID: **4**] {Uses: **5**} (Price: **G$3**)\nGolf Pencil (goes inside a cache) [ID: **5**] {Uses: **10**} (Price: **G$5**)\nMechanical Pencil [ID: **6**] {Uses: **50**} (Price: **G$30**)""", 
              colour=0xad7e66)

vehiclesembed = discord.Embed(title="Vehicles & Tickets:",
                      description="__Vehicle Types__:\nBike [ID: **23**] {Distance: **100km**} (Price: **G$50**)\nScooter [ID: **24**] {Distance: **25km**} (Price: **G$40**)\nSkateboard [ID: **25**] {Distance: **20km**} (Price: **G$35**)\nSedan [ID: **26**] {Distance: **7500km**} (Price: **G$300**)\nTruck [ID: **27**] {Distance: **10000km**} (Price: **G$500**)\nQuad [ID: **28**] {Distance: **7000km**} (Price: **G$250**)\n\n__Tickets__:\nTaxi Tickets [ID: **29**] {Distance: **50km**} (Price: **G$15**)\nTaxi Tickets X5 [ID: **30**] (Price: **G$70**)\nBus Ticket [ID:** 31**] {Distance: **100km**} (Price: **G$10**)\nBus Ticket X5 [ID: **32**] (Price: **G$45**)\n\nVehicle Distance = ***Max*** distance that vehicle can go.\nTicket Distance = ***Max*** distance for one trip.",
                      colour=0xad7e66)

tbembed = discord.Embed(title="Trackables",
                      description="__Travel Bugs__:\n<:TBTAG_BASIC:1359163550697914538> Basic Tag [ID: **33**] (Price: **G$25**)\n<:TBTAG_TRACKER:1359166477986562138> Tracker Tag [ID: **34**] (Price: **G$30**)\n\n__Geocoins__:\n<:TBCOIN_LOGO_GOLD:1359172201726873894> GC Logo Coin Gold [ID: **35**] (Price: **G$50**)\n<:TBCOIN_LOGO_SILVER:1359172203433689218> GC Logo Coin Silver [ID: **36**] (Price: **G$45**)\n<:TBCOIN_TRACKER_GOLD:1359178687051730974> Tracker Coin Gold [ID: **37**] (Price: **G$60**)\n<:TBCOIN_SIGNAL_GOLD:1359182225853382858> Signal Coin Gold [ID: **38**] (Price: **G$55**)\n<:TBCOIN_DISCORD_SILVER:1359188642941374504> Discord Coin Silver [ID: **39**] (Price: **G$50**)\n<:TBCOIN_AMMOCAN_BRASS:1359192217750732850> Ammo Can Coin Brass [ID: **40**] (Price: **G$50**)\n<:TBCOIN_BOTSTART_ANCIENTSILVER:1359199275619192973> Game Start Coin Ancient Silver [ID: **41**] (Price: **G$50**)",
                      colour=0xad7e66)

class ShopDropdown(Select):
    def __init__(self, author: typing.Union[discord.Member, discord.User]):
        self.author = author
        options = [
            discord.SelectOption(label="Writing Instruments", value="writing"),
            discord.SelectOption(label="Logbooks", value="logbooks"),
            discord.SelectOption(label="Containers", value="containers"),
            discord.SelectOption(label="Transport", value="transport"),
            discord.SelectOption(label="Trackables", value="trackables"),
        ]
        super().__init__(placeholder="Select a category", options=options)

    async def callback(self, interaction: discord.Interaction):
        embeds = {
            "writing": writingembed,
            "logbooks": discord.Embed(title="Logbooks", description="Coming soon...", colour=0xad7e66),
            "containers": containersembed,
            "transport": vehiclesembed,
            "trackables": tbembed,
        }
        await interaction.response.edit_message(embed=embeds[self.values[0]], view=self.view)
        
    async def interaction_check(self, interaction: discord.Interaction):
            if not interaction.user == self.author:
                await interaction.response.send_message(content="You cannot use this dropdown!", ephemeral=True)
                return False
            return True

class PurchaseModal(Modal, title="Purchase Items"):
    selection = TextInput(
        label="Enter Item IDs",
        placeholder="E.g., 7.8.11L, 1.1, 23",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        raw_input = self.selection.value.strip()
        item_ids = [item.strip() for item in raw_input.split(',') if item.strip()] 

        total_price = 0
        purchased_items = []
        async with Session() as session:
            user_id = interaction.user.id
            balance = await get_balance(session, user_id)

            for item_id in item_ids:
                try:
                    price = calculate_price(item_id)
                except ValueError as e:
                    await interaction.response.send_message(str(e), ephemeral=True)
                    return

                if balance < total_price + price:
                    await interaction.response.send_message(
                        f"You don't have enough money to buy all items. Current balance: G${balance}.", ephemeral=True
                    )
                    return

                total_price += price
                purchased_items.append(item_id)

            new_balance = balance - total_price
            await update_balance(session, user_id, new_balance)
            for item_id in purchased_items:
                await add_inv_item(session, user_id, item_id)

            await interaction.response.send_message(
                f"You bought **{', '.join(purchased_items)}**. Total cost: **G${total_price}**. New balance: **G${new_balance}**.",
                ephemeral=True
            )

class ShopView(View):
    def __init__(self, interaction):
        super().__init__()
        self.add_item(ShopDropdown(interaction.user))
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
    "pens": {
        "1": {"base": 5},   # EZWrite Pen
        "2": {"base": 15},  # GlideMaster Pen
        "3": {"base": 50},  # CosmoScribe Pen
        "colors": {
            ".1": 0,  # Red
            ".2": 0,  # Green
            ".3": 0,  # Blue
            ".4": 0,  # Black
            ".5": 0   # Purple
        }
    },
    "pencilWC": {
        "4": {"base": 3},   # Regular Pencil
        "5": {"base": 5},   # Golf Pencil
        "colors": {
            ".1": 0,  # Red
            ".2": 0,  # Green
            ".3": 0,  # Blue
            ".4": 0,  # Black
            ".5": 0   # Purple
        }
    },
    "pencilNC": {
        "6": {"base": 30},  # Mechanical Pencil
    },
    "containers": {
        "7": {"base": 15},  # Plastic Container
        "8": {"base": 15},  # 3D Printed Container
        "9": {"base": 30},  # Decoy Rock
        "10": {"base": 45}, # Decoy Electric Metal Plate
        "11": {"base": 20}, # Bottle Cap Container
        "12": {"base": 10}, # Decoy Bolt
        "13": {"base": 5},  # Bison Tube
        "14": {"base": 50}, # Ammo Can
        "15": {"base": 5},  # Pill Bottle
        "16": {"base": 20}, # Magnetic Container
        "22": {"base": 55}, # Maze Container
        "sizes": {
            ".6": 5,   # XS
            ".7": 10,  # S
            ".8": 20,  # M
            ".9": 40,  # L
            ".10": 80  # XL
        },
        "colors": {
            ".11": 0,  # Red
            ".12": 0,  # Orange
            ".13": 0,  # Yellow
            ".14": 0,  # Green
            ".15": 0,  # Blue
            ".16": 0,  # Purple
            ".17": 0   # Black
        },
        "log": {
            "L": 1  # Add a log
        }
    },
    "transport": {
        "23": {"base": 50},   # Bike
        "24": {"base": 40},   # Scooter
        "25": {"base": 35},   # Skateboard
        "26": {"base": 300},  # Sedan
        "27": {"base": 500},  # Truck
        "28": {"base": 250},  # Quad
    },  
    "tickets": {
        "29": {"base": 15},  # Taxi Ticket
        "30": {"base": 70},  # Taxi Tickets X5
        "31": {"base": 10},  # Bus Ticket
        "32": {"base": 45}   # Bus Tickets X5
    },
    "trackables": {
        "33": {"base": 25},  # Taxi Ticket
        "34": {"base": 30},  # Taxi Tickets X5
        "35": {"base": 50},  # Bus Ticket
        "36": {"base": 45},   # Bus Tickets X5
        "37": {"base": 60},   # Bus Tickets X5
        "38": {"base": 55},   # Bus Tickets X5
        "39": {"base": 50},   # Bus Tickets X5
        "40": {"base": 50},   # Bus Tickets X5
        "41": {"base": 50}   # Bus Tickets X5
    }
}

MAIN_INVENTORY = {
    # Pens
    "1": "EZWrite Pen",
    "2": "GlideMaster Pen",
    "3": "CosmoScribe Pen",
    "4": "Regular Pencil",
    "5": "Golf Pencil",
    "6": "Mechanical Pencil",
    # Containers
    "7": "Plastic Container",
    "8": "3D Printed Container",
    "9": "Decoy Rock",
    "10": "Decoy Electric Metal Plate",
    "11": "Bottle Cap Container",
    "12": "Decoy Bolt",
    "13": "Bison Tube",
    "14": "Ammo Can",
    "15": "Pill Bottle",
    "16": "Magnetic Container",
    "22": "Maze Container",
    # Transport
    "23": "Bike",
    "24": "Scooter",
    "25": "Skateboard",
    "26": "Sedan",
    "27": "Truck",
    "28": "Quad",
    # Tickets
    "29": "Taxi Ticket",
    "30": "Taxi Tickets X5",
    "31": "Bus Ticket",
    "32": "Bus Tickets X5",
    # Trackables
    "33": "Basic TB Tag",
    "34": "Tracker TB Tag",
    "35": "GC Logo Geocoin Gold",
    "36": "GC Logo Geocoin Silver",
    "37": "Tracker Geocoin Gold",
    "38": "Signal Geocoin Gold",
    "39": "Discord Geocoin Silver",
    "40": "Ammo Can Geocoin Brass",
    "41": "Game Start Geocoin Ancient Silver",
}

ALT_INVENTORY = {
    # Pen Colors
    ".1": "Red",
    ".2": "Green",
    ".3": "Blue",
    ".4": "Black",
    ".5": "Purple",
    # Container Sizes
    ".6": "XS",
    ".7": "S",
    ".8": "M",
    ".9": "L",
    ".10": "XL",
    # Container Colors
    ".11": "Red",
    ".12": "Orange",
    ".13": "Yellow",
    ".14": "Green",
    ".15": "Blue",
    ".16": "Purple",
    ".17": "Black",
    # Logs
    "L": "Log (Plain Paper)",
}

def calculate_price(item_id: str) -> int:
    """
    Calculate the total price of an item based on its ID.

    Args:
        item_id (str): The item ID (e.g., "7.10.11L" or "1.1").

    Returns:
        int: The total price of the item.
    """
    # Use regex to split the item ID while preserving periods and letters
    parts = re.findall(r'\d+|\.\d+|[A-Za-z]', item_id)
    print(parts)  # Debugging output to verify the parsed parts
    category = None
    total_price = 0

    # Determine the category
    if parts[0] in SHOP_PRICES["pens"]:
        category = "pens"
    elif parts[0] in SHOP_PRICES["containers"]:
        category = "containers"
    elif parts[0] in SHOP_PRICES["transport"]:
        category = "transport"
    elif parts[0] in SHOP_PRICES["tickets"]:
        category = "tickets"
    elif parts[0] in SHOP_PRICES["pencilWC"]:
        category = "pencilWC"
    elif parts[0] in SHOP_PRICES["pencilNC"]:
        category = "pencilNC"
    elif parts[0] in SHOP_PRICES["trackables"]:
        category = "trackables"

    if not category:
        raise ValueError(f"Invalid item ID: {item_id}")

    # Add base price
    if category == "tickets":
        total_price += SHOP_PRICES["tickets"][parts[0]]["base"]
    else:
        total_price += SHOP_PRICES[category][parts[0]]["base"]

    # Process additional components
    for part in parts[1:]:
        # Add color price (for pens and containers)
        if category in ["pens", "containers", "pencilWC"] and part in SHOP_PRICES[category].get("colors", {}):
            # Check if the specific item supports colors
            if parts[0] in SHOP_PRICES[category]["colors"]:
                total_price += SHOP_PRICES[category]["colors"][part]

        # Add size price (for containers)
        elif category == "containers" and part in SHOP_PRICES["containers"]["sizes"]:
            total_price += SHOP_PRICES["containers"]["sizes"][part]

        # Add log price (for containers)
        elif category == "containers" and part in SHOP_PRICES["containers"]["log"]:
            total_price += SHOP_PRICES["containers"]["log"][part]

    return total_price

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