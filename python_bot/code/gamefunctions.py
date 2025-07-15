import discord
import typing
import re
import string
import random
from functions import *
from economy import *
from discord.ui import Select, Button, View, Modal, TextInput
from collections import Counter

def get_container_name(container_code):
    parts = re.findall(r'\d+|\.\d+|[A-Za-z]', container_code)
    
    # Get the main item name from MAIN_INVENTORY
    main_item_code = parts[0]
    main_item = MAIN_INVENTORY.get(main_item_code, "Unknown Item")
    
    # Get additional items from ALT_INVENTORY
    alt_items = [ALT_INVENTORY.get(part, "") for part in parts[1:]]
    alt_items = [alt for alt in alt_items if alt]  # Filter out empty items
    
    # Combine the main item name and any additional attributes
    container_name = f"{main_item} {' '.join(alt_items)}".strip()
    
    return container_name

async def generate_public_code(session) -> str:
    """
    Generate a unique public code for a trackable.
    The code will start with 'TB' followed by a mix of letters and numbers.
    """
    while True:
        public_code = "TB" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        
        result = await session.execute(select(Trackables).where(Trackables.public_code == public_code))
        if not result.scalar():  
            return public_code

async def generate_private_code(session) -> str:
    """
    Generate a unique private code for a trackable.
    The code will consist of 8 alphanumeric characters.
    """
    while True:
        private_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        result = await session.execute(select(Trackables).where(Trackables.private_code == private_code))
        if not result.scalar():  
            return private_code

class DeleteEmbedView(View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="🗑️", style=discord.ButtonStyle.red)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

containersembed = discord.Embed(title="Containers",
                      description="__Container Type__:\nPlastic Container [ID: **7**] (Price: **G$10**)\n3D printed Container [ID: **8**] (Price: **G$15**)\nFake Rock [ID: **9**] (Price: **G$15**)\nFake Electric Metal Plate (Only Comes In ***__S__***) [ID: **10**] (Price: **G$17**)\nBottle Cap Container (Only Comes In ***__XS__*** And ***__S__***) [ID: **11**] (Price: **G$15**)\nFake Bolt [ID: **12**] (Price: **G$7**)\nBison Tube (Only Comes in ***__XS__***, ***__S__***, And ***__M__***) [ID: **13**] (Price: **G$5**)\nAmmo Can (Only Comes in ***__M__***, ***__L__***, And ***__XL__***) [ID: **14**] (Price: **G$50**)\nPill Bottle (Only Comes in ***__XS__***, ***__S__***, And ***__M__***) [ID: **15**] (Price: **G$5**)\nMagnetic Container (Only Comes in ***__XS__*** And ***__S__***) [ID: **16**] (Price: **G$10**)\nFake Gum (Only Comes In __***XS***__ and __***S***__) [ID: **17**] (Price: **G$7**)\nFake Log (Only Comes In __***S***__ and __***M***__) [ID: **18**] (Price: **G$25**)\nFilm Canister (Only Comes In __***S***__  and __***M***__) [ID: **19**] (Price: **G$5**)\nFake Snail (Only Comes In __***XS***__ and __***S***__) [ID: **20**] (Price: **G$13**)\nFake Pinecone (Only Comes In __***S***__ and __***M***__) [ID: **21**] (Price: **G$15**)\nMaze Container (Only Comes In ***__M__***) [ID: **22**] (Price: **G$55**)\n\n__Container Size__:\n***__XS__*** Container [ID: **.6**] (Price: **G$5**)\n***__S__*** Container [ID: **.7**] (Price: **G$10**)\n***__M__*** Container [ID: **.8**] (Price: **G$20**)\n***__L__*** Container [ID: **.9**] (Price: **G$40**)\n***__XL__*** Container [ID: **.10**] (Price: **G$80**)\n\n__Container Colour__:\nRed [ID: **.11**]\nOrange [ID: **.12**]\nYellow [ID: **.13**]\nGreen [ID: **.14**]\nBlue [ID: **.15**]\nPurple [ID: **.16**]\nBlack [ID: **.17**]\nCamo [ID: **.18**] (+**G$5**)\n\n__Add a log__ *(plain paper)*: +**G$1** [ID: **L**]",
                      colour=0xad7e66)

writingembed = discord.Embed(title="Writing Instruments", 
              description="""__Pen Type__:\nEZWrite [ID: **1**] {Uses: **10**} (Price: **G$5**)\nGlideMaster [ID: **2**] {Uses: **30**} (Price: **G$15**)\nCosmoScribe [ID: **3**] {Uses: **100**} (Price: **G$50**)\nMiniWrite Pencil <goes inside a cache> [ID: **5.19**] {Uses: **20**} (Price: **G$5**)\nMiniWrite Pen <goes inside a cache> [ID: **5.20**] {Uses: **20**} (Price: **G$5**)\n__Pen Colour__:\nRed [ID: **.1**]\nGreen [ID: **.2**]\nBlue [ID: **.3**]\nBlack [ID: **.4**]\nPurple [ID: **.5**]\n\n__Pencil Type__:\nRegular Pencil [ID: **4**] {Uses: **5**} (Price: **G$3**)\nGolf Pencil (goes inside a cache) [ID: **5**] {Uses: **10**} (Price: **G$5**)\nMechanical Pencil [ID: **6**] {Uses: **50**} (Price: **G$30**)""", 
              colour=0xad7e66)

vehiclesembed = discord.Embed(title="Vehicles & Tickets:",
                      description="__Vehicle Types__:\nBike [ID: **23**] {Distance: **100km**} (Price: **G$50**)\nScooter [ID: **24**] {Distance: **25km**} (Price: **G$40**)\nSkateboard [ID: **25**] {Distance: **20km**} (Price: **G$35**)\nSedan [ID: **26**] {Distance: **7500km**} (Price: **G$300**)\nTruck [ID: **27**] {Distance: **10000km**} (Price: **G$500**)\nQuad [ID: **28**] {Distance: **7000km**} (Price: **G$250**)\n\n__Tickets__:\nTaxi Tickets [ID: **29**] {Distance: **50km**} (Price: **G$15**)\nTaxi Tickets X5 [ID: **30**] (Price: **G$70**)\nBus Ticket [ID:** 31**] {Distance: **100km**} (Price: **G$10**)\nBus Ticket X5 [ID: **32**] (Price: **G$45**)\n\nVehicle Distance = ***Max*** distance that vehicle can go.\nTicket Distance = ***Max*** distance for one trip.",
                      colour=0xad7e66)

tbembed = discord.Embed(title="Trackables",
                      description="__Travel Bugs__:\n<:TBTAG_BASIC:1359163550697914538> Basic Tag [ID: **33**] (Price: **G$25**)\n<:TBTAG_TRACKER:1359166477986562138> Tracker Tag [ID: **34**] (Price: **G$30**)\n\n__Geocoins__:\n<:TBCOIN_LOGO_GOLD:1359172201726873894> GC Logo Coin Gold [ID: **35**] (Price: **G$50**)\n<:TBCOIN_LOGO_SILVER:1359172203433689218> GC Logo Coin Silver [ID: **36**] (Price: **G$45**)\n<:TBCOIN_TRACKER_GOLD:1359178687051730974> Tracker Coin Gold [ID: **37**] (Price: **G$60**)\n<:TBCOIN_SIGNAL_GOLD:1359182225853382858> Signal Coin Gold [ID: **38**] (Price: **G$55**)\n<:TBCOIN_DISCORD_SILVER:1359188642941374504> Discord Coin Silver [ID: **39**] (Price: **G$50**)\n<:TBCOIN_AMMOCAN_BRASS:1359192217750732850> Ammo Can Coin Brass [ID: **40**] (Price: **G$50**)\n<:TBCOIN_BOTSTART_ANCIENTSILVER:1359199275619192973> Game Start Coin Ancient Silver [ID: **41**] (Price: **G$50**)",
                      colour=0xad7e66)

accessoryembed = discord.Embed(title="Container Accessories",
                      description="__Container Restraints__:\nRope [ID: **42**] (Price: **G$20**)\nChain [ID: **43**] (Price: **G$35**)\nZip Tie [ID: **44**] (Price: **G$7**)\n\n__Logbooks__:\nPlain Paper [ID: **45**] (Price: **G$3**)\nSmall Notepad [ID: **46**] (Price: **G$5**)\nNotebook [ID: **47**] (Price: **G$10**)",
                      colour=0xad7e66)

class ShopDropdown(Select):
    def __init__(self, author: typing.Union[discord.Member, discord.User]):
        self.author = author
        options = [
            discord.SelectOption(label="Writing Instruments", value="writing"),
            discord.SelectOption(label="Container Accessories", value="accessoryembed"),
            discord.SelectOption(label="Containers", value="transport"),
            discord.SelectOption(label="Trackables", value="trackables"),
        ]
        super().__init__(placeholder="Select a category", options=options)

    async def callback(self, interaction: discord.Interaction):
        embeds = {
            "writing": writingembed,
            "accessoryembed": accessoryembed,
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

items_by_id = {
    33: {"emoji": "<:TBTAG_BASIC:1359163550697914538>", "name": "Basic Tag"},
    34: {"emoji": "<:TBTAG_TRACKER:1359166477986562138>", "name": "Tracker Tag"},
    35: {"emoji": "<:TBCOIN_LOGO_GOLD:1359172201726873894>", "name": "GC Logo Geocoin Gold"},
    36: {"emoji": "<:TBCOIN_LOGO_SILVER:1359172203433689218>", "name": "GC Logo Geocoin Silver"},
    37: {"emoji": "<:TBCOIN_TRACKER_GOLD:1359178687051730974>", "name": "Tracker Geocoin Gold"},
    38: {"emoji": "<:TBCOIN_SIGNAL_GOLD:1359182225853382858>", "name": "Signal Geocoin Gold"},
    39: {"emoji": "<:TBCOIN_DISCORD_SILVER:1359188642941374504>", "name": "Discord Geocoin Silver"},
    40: {"emoji": "<:TBCOIN_AMMOCAN_BRASS:1359192217750732850>", "name": "Ammo Can Geocoin Brass"},
    41: {"emoji": "<:TBCOIN_BOTSTART_ANCIENTSILVER:1359199275619192973>", "name": "Game Start Geocoin Ancient Silver"},
}

class PurchaseModal(Modal, title="Purchase Items"):
    selection = TextInput(
        label="Enter Item IDs",
        placeholder="E.g., 7.8.11L, 1.1, 23",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        raw_input = self.selection.value.strip()
        item_ids = [item.strip() for item in re.split(r'[,\s;/|]+', raw_input) if item.strip()]

        total_price = 0
        purchased_items = []
        async with Session() as session:
            user_id = interaction.user.id
            balance = await get_balance(session, user_id)

            for item_id in item_ids:
                try:
                    price = calculate_price(item_id)
                except ValueError as e:
                    await interaction.followup.send(str(e), ephemeral=True)
                    return

                if balance < total_price + price:
                    await interaction.followup.send(
                        f"You don't have enough money to buy all items. Current balance: G${balance}.", ephemeral=True
                    )
                    return

                if item_id.split('.')[0] in SHOP_PRICES["containers"]:
                    has_size = any(size in item_id for size in SHOP_PRICES["containers"]["sizes"].keys())
                    if not has_size:
                        await interaction.followup.send(
                            f"Item ID `{item_id}` is invalid. Containers must have a size (e.g., `.6` for XS, `.7` for S).",
                            ephemeral=True
                        )
                        return

                if 'L' in item_id:
                    if item_id.split('.')[0] not in SHOP_PRICES["containers"]:
                        await interaction.followup.send(f"Item ID `{item_id}` is invalid. 'L' can only be used with containers.")
                        return

                total_price += price
                purchased_items.append(item_id)

            new_balance = balance - total_price
            await update_balance(session, user_id, new_balance)
            valid_ids = {33, 34, 35, 36, 37, 38, 39, 40, 41}
            for item_id in purchased_items:
                originalitemid = item_id
                if 'L' in item_id:
                    item_id = item_id.replace('L','')
                if '.' in item_id:
                    item_id = item_id.replace('.','')
                if int(item_id) in valid_ids:
                    public_code = await generate_public_code(session)
                    private_code = await generate_private_code(session)
                    current = await get_trackables_owned(session, user_id)
                    new = current + 1
                    await update_trackables_owned(session, user_id, new)
                    await add_trackable(session, user_id, public_code, private_code, item_id)
                    item = items_by_id.get(int(float(item_id)))
                    embed = discord.Embed(title="Thank you for your TB purchase!",
                      description=f"You purchased a {item['emoji']} {item['name']}.\nPublic Code: {public_code}, Private Code: {private_code}\n\nTo activate your TB, run </game activate_tb:1359120516627169318> and enter the private code in the appropriate field.",
                      colour=0xad7e66)
                    await interaction.user.send(embed=embed)
                else:
                    if int(item_id) == 30:
                        for _ in range(5):
                            await add_inv_item(session, user_id, "29")
                    elif int(item_id) == 32:
                        for _ in range(5):
                            await add_inv_item(session, user_id, "31")
                    else:
                        item_id = originalitemid
                        await add_inv_item(session, user_id, item_id)

            await interaction.followup.send(
                f"You bought **{', '.join(purchased_items)}**. Total cost: **G${total_price}**. New balance: **G${new_balance}**.",
                ephemeral=True
            )

class ShopView(View):
    def __init__(self, interaction, msg):
        super().__init__(timeout=600)
        self.add_item(ShopDropdown(interaction.user))
        self.add_item(PurchaseButton())
        self.msg = msg
        
    async def on_timeout(self):
        """Disable all buttons when the view times out."""
        for child in self.children:
            child.disabled = True
        if self.msg:
            await self.msg.edit(view=self)

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

        if (last_letter == 'Z'):
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
        "5": {"base": 5},   # MiniWrite
        "colors": {
            ".1": 0,  # Red
            ".2": 0,  # Green
            ".3": 0,  # Blue
            ".4": 0,  # Black
            ".5": 0,  # Purple
            ".19": 0, # MiniWrite Pencil
            ".20": 0  # MiniWrite Pen
        }
    },
    "pencilNC": {
        "6": {"base": 30},  # Mechanical Pencil
    },
    "containers": {
        "7": {"base": 10},  # Plastic Container
        "8": {"base": 15},  # 3D Printed Container
        "9": {"base": 15},  # Decoy Rock
        "10": {"base": 17}, # Decoy Electric Metal Plate
        "11": {"base": 15}, # Bottle Cap Container
        "12": {"base": 7}, # Decoy Bolt
        "13": {"base": 5},  # Bison Tube
        "14": {"base": 50}, # Ammo Can
        "15": {"base": 5},  # Pill Bottle
        "16": {"base": 20}, # Magnetic Container
        "17": {"base": 7}, # Magnetic Container
        "18": {"base": 25}, # Magnetic Container
        "19": {"base": 5}, # Magnetic Container
        "20": {"base": 13}, # Magnetic Container
        "21": {"base": 15}, # Magnetic Container
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
            ".17": 0,  # Black
            ".18": 5   # Camo
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
        "33": {"base": 25},  # Basic TB Tag
        "34": {"base": 30},  # Tracker TB Tag
        "35": {"base": 50},  # GC Logo Coin Gold
        "36": {"base": 45},  # GC Logo Coin Silver
        "37": {"base": 60},  # Tracker Coin Gold
        "38": {"base": 55},  # Signal Coin Gold
        "39": {"base": 50},  # Discord Coin Silver
        "40": {"base": 50},  # Ammo Can Coin Brass
        "41": {"base": 50}   # Game Start Coin Ancient Silver
    },
    "accessories": {
        "42": {"base": 20},  # Rope
        "43": {"base": 35},  # Chain
        "44": {"base": 7},   # Zip Tie
        "45": {"base": 3},   # Plain Paper Log
        "46": {"base": 5},   # Small Notepad Log
        "47": {"base": 10}   # Notebook Log
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
    "17": "Fake Gum",
    "18": "Fake Log",
    "19": "Film Canister",
    "20": "Fake Snail",
    "21": "Fake Pinecone",
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
    # Accessories
    "42": "Rope",
    "43": "Chain",
    "44": "Zip Tie",
    "45": "Plain Paper Log",
    "46": "Small Notepad Log",
    "47": "Notebook Log",
}

ALT_INVENTORY = {
    # Pen Colors
    ".1": "Red",
    ".2": "Green",
    ".3": "Blue",
    ".4": "Black",
    ".5": "Purple",
    ".19": "MiniWrite Pencil",
    ".20": "MiniWrite Pen",
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
    ".18": "Camo",
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
    parts = re.findall(r'\d+|\.\d+|[A-Za-z]', item_id)
    category = None
    total_price = 0

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
    elif parts[0] in SHOP_PRICES["accessories"]:
        category = "accessories"

    if not category:
        raise ValueError(f"Invalid item ID: {item_id}")

    if category == "tickets":
        total_price += SHOP_PRICES["tickets"][parts[0]]["base"]
    else:
        total_price += SHOP_PRICES[category][parts[0]]["base"]

    for part in parts[1:]:
        if category in ["pens", "containers", "pencilWC"] and part in SHOP_PRICES[category].get("colors", {}):
            total_price += SHOP_PRICES[category]["colors"][part]

        elif category == "containers" and part in SHOP_PRICES["containers"]["sizes"]:
            total_price += SHOP_PRICES["containers"]["sizes"][part]

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
        self.container = None 
        self.container_id = None
        self.log_id = None
        self.log = None
        self.log_status = None
        self.writing_instrument_id = None
        self.pen = None
       
async def send_a_modal(interaction, modal):
    await interaction.response.send_modal(modal)
        
class HideConfigureSelect(Select):
    def __init__(self, hide_data: HideConfigData, interaction: discord.Interaction, original_message: discord.Message, hide_id: str = None):
        self.hide_data = hide_data
        self.interaction = interaction
        self.original_message = original_message  # Store the original message
        self.hide_id = hide_id  # If editing an existing unpublished hide
        options = [
            discord.SelectOption(label="Name", value="name"),
            discord.SelectOption(label="Location", value="location"),
            discord.SelectOption(label="Description", value="description"),
            discord.SelectOption(label="Difficulty", value="difficulty"),
            discord.SelectOption(label="Terrain", value="terrain"),
            discord.SelectOption(label="Pen", value="pen"),
            discord.SelectOption(label="Save", value="save"),
            discord.SelectOption(label="Publish Hide", value="publish")
        ]
        super().__init__(placeholder="Select an option to configure...", options=options)

    async def update_embed(self, interaction=None):
        print("[DEBUG] HideConfigureSelect.update_embed called")
        print(f"[DEBUG] original_message: {self.original_message}")
        print(f"[DEBUG] interaction: {interaction}")
        embed = discord.Embed(
            title="Configure Your Hide",
            description="Use the dropdown below to configure your hide.",
            colour=0xad7e66
        )
        embed.add_field(name="Name", value=self.hide_data.name or "Not set", inline=False)
        embed.add_field(name="Location", value=self.hide_data.location or "Not set", inline=False)
        embed.add_field(name="Description", value=self.hide_data.description or "Not set", inline=False)
        embed.add_field(name="Difficulty", value=f"{self.hide_data.difficulty}/5" if self.hide_data.difficulty else "Not set", inline=True)
        embed.add_field(name="Terrain", value=f"{self.hide_data.terrain}/5" if self.hide_data.terrain else "Not set", inline=True)
        embed.add_field(name="Container", value=self.hide_data.container or "Not set", inline=False)
        if self.hide_data.log_status == True:
            embed.add_field(name="Logbook", value=self.hide_data.log or "Not set", inline=False)
        if self.hide_data.writing_instrument_id:
            wi = "MiniWrite Pencil (5.19)" if self.hide_data.writing_instrument_id == "5.19" else "MiniWrite Pen (5.20)"
            embed.add_field(name="Writing Instrument", value=wi, inline=False)
        view = View()
        # Always pass hide_id to the new HideConfigureSelect
        view.add_item(HideConfigureSelect(self.hide_data, self.interaction, self.original_message, hide_id=self.hide_id))

        # Try all possible update methods in order of preference
        try:
            if self.original_message is not None:
                await self.original_message.edit(embed=embed, view=view)
            elif interaction is not None:
                try:
                    await interaction.edit_original_response(embed=embed, view=view)
                except Exception as e:
                    print(e)
                    try:
                        await interaction.response.edit_message(embed=embed, view=view)
                    except Exception as e:
                        print(e)
                        try:
                            await interaction.message.edit(embed=embed, view=view)
                        except Exception as e:
                            print(e)
        except Exception as e:
            print(e)

    async def callback(self, interaction: discord.Interaction):
        # Only defer if not sending a modal (which itself responds)
        if self.values[0] in ["name", "description"]:
            modal = InputModal(
                title=f"Enter {self.values[0]}",
                field_name=self.values[0],
                hide_data=self.hide_data,
                interaction=interaction,
                original_message=self.original_message
            )
            modal.hide_id = getattr(self, 'hide_id', None)
            try:
                await send_a_modal(interaction, modal)
            except Exception as e:
                print(e)
                return
        else:
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer()
            except Exception:
                pass
            if self.values[0] == "location":
                view = View()
                view.add_item(LocationSelect(self.hide_data, interaction, self.original_message, hide_id=getattr(self, 'hide_id', None)))
                view.add_item(BackToConfigButton(self.hide_data, interaction, self.original_message, getattr(self, 'hide_id', None)))
                embed = discord.Embed(
                    title="Select Location",
                    description="Choose a location for your hide.",
                    colour=0xad7e66
                )
                await self.original_message.edit(embed=embed, view=view)
            elif self.values[0] == "difficulty":
                view = View()
                view.add_item(DifficultySelect(self.hide_data, interaction, self.original_message, hide_id=getattr(self, 'hide_id', None)))
                view.add_item(BackToConfigButton(self.hide_data, interaction, self.original_message, getattr(self, 'hide_id', None)))
                embed = discord.Embed(
                    title="Select Difficulty",
                    description="Choose a difficulty for your hide.",
                    colour=0xad7e66
                )
                await self.original_message.edit(embed=embed, view=view)
            elif self.values[0] == "terrain":
                view = View()
                view.add_item(TerrainSelect(self.hide_data, interaction, self.original_message, hide_id=getattr(self, 'hide_id', None)))
                view.add_item(BackToConfigButton(self.hide_data, interaction, self.original_message, getattr(self, 'hide_id', None)))
                embed = discord.Embed(
                    title="Select Terrain",
                    description="Choose a terrain rating for your hide.",
                    colour=0xad7e66
                )
                await self.original_message.edit(embed=embed, view=view)
            elif self.values[0] == "pen":
                # Show pen selection dropdown
                view = View()
                view.add_item(PenSelect(self.hide_data, interaction, self.original_message, hide_id=self.hide_id))
                embed = discord.Embed(
                    title="Select a Writing Instrument",
                    description="Choose a pen or pencil for your hide.",
                    colour=0xad7e66
                )
                await self.original_message.edit(embed=embed, view=view)
            elif self.values[0] == "save":
                # Route to PenSelect's save_hide
                pen_select = PenSelect(self.hide_data, interaction, self.original_message, hide_id=self.hide_id)
                await pen_select.save_hide(interaction)
            elif self.values[0] == "publish":
                # Route to PenSelect's publish_hide
                pen_select = PenSelect(self.hide_data, interaction, self.original_message, hide_id=self.hide_id)
                await pen_select.publish_hide(interaction)
        # Reset the dropdown to its placeholder
        self.placeholder = "Select an option to configure..."
        # Only update embed for options that do not open a subview
        if self.values[0] not in ["location", "difficulty", "terrain", "publish", "pen"]:
            await self.update_embed(interaction)
class PenSelect(Select):
    def __init__(self, hide_data, interaction, original_message, hide_id=None):
        self.hide_data = hide_data
        self.interaction = interaction
        self.original_message = original_message
        self.hide_id = hide_id
        options = [
            discord.SelectOption(label="MiniWrite Pencil", value="5.19"),
            discord.SelectOption(label="MiniWrite Pen", value="5.20"),
        ]
        super().__init__(placeholder="Select a writing instrument...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_id = self.values[0]
        self.hide_data.writing_instrument_id = selected_id
        # Optionally, set a human-readable name
        if selected_id == "5.19":
            self.hide_data.pen = "MiniWrite Pencil (5.19)"
        elif selected_id == "5.20":
            self.hide_data.pen = "MiniWrite Pen (5.20)"
        # Update the embed and return to config view
        view = View()
        view.add_item(HideConfigureSelect(self.hide_data, self.interaction, self.original_message, hide_id=self.hide_id))
        embed = discord.Embed(
            title="Configure Your Hide",
            description="Use the dropdown below to configure your hide.",
            colour=0xad7e66
        )
        embed.add_field(name="Name", value=self.hide_data.name or "Not set", inline=False)
        embed.add_field(name="Location", value=self.hide_data.location or "Not set", inline=False)
        embed.add_field(name="Description", value=self.hide_data.description or "Not set", inline=False)
        embed.add_field(name="Difficulty", value=f"{self.hide_data.difficulty}/5" if self.hide_data.difficulty else "Not set", inline=True)
        embed.add_field(name="Terrain", value=f"{self.hide_data.terrain}/5" if self.hide_data.terrain else "Not set", inline=True)
        embed.add_field(name="Container", value=self.hide_data.container or "Not set", inline=False)
        if self.hide_data.log_status == True:
            embed.add_field(name="Logbook", value=self.hide_data.log or "Not set", inline=False)
        if self.hide_data.writing_instrument_id:
            wi = "MiniWrite Pencil (5.19)" if self.hide_data.writing_instrument_id == "5.19" else "MiniWrite Pen (5.20)"
            embed.add_field(name="Writing Instrument", value=wi, inline=False)
        await self.original_message.edit(embed=embed, view=view)

    async def save_hide(self, interaction: discord.Interaction):
        """
        Save the current hide configuration to the database using the appropriate update_* functions.
        Handles both new and existing (unpublished) hides using hide_id if present.
        Now saves all fields, even if incomplete, so users can fill in partial data and return later.
        """
        try:
            async with Session() as session:
                if self.hide_id:
                    hide = await get_hide_by_id(session, self.hide_id)
                    if not hide:
                        await interaction.followup.send(f"No unpublished hide with ID `{self.hide_id}` found.", ephemeral=True)
                        return
                    # Save all fields, even if blank or None
                    await update_hide_name(session, self.hide_id, self.hide_data.name)
                    await update_hide_location(session, self.hide_id, float(self.hide_data.lat) if self.hide_data.lat is not None else None, float(self.hide_data.lon) if self.hide_data.lon is not None else None)
                    await update_hide_description(session, self.hide_id, self.hide_data.description)
                    await update_hide_difficulty(session, self.hide_id, self.hide_data.difficulty if self.hide_data.difficulty is not None else None)
                    await update_hide_terrain(session, self.hide_id, self.hide_data.terrain if self.hide_data.terrain is not None else None)
                    await update_hide_size(session, self.hide_id, self.hide_data.container)
                    containernametoid = await container_name_to_id(self.hide_data.container) if self.hide_data.container else None
                    await update_hide_containerid(session, self.hide_id, containernametoid)
                    await update_hide_location_name(session, self.hide_id, self.hide_data.location)
                    # Save writing instrument
                    await update_hide_writing_instrument(session, self.hide_id, self.hide_data.writing_instrument_id)
                    # Remove pen from inventory if selected and container size is Medium or larger
                    if self.hide_data.writing_instrument_id and self.hide_data.container:
                        # Check for .8, .9, .10 in container string
                        if any(size in self.hide_data.container for size in [".8", ".9", ".10"]):
                            await remove_inv_item(session, interaction.user.id, self.hide_data.writing_instrument_id)
                    await interaction.followup.send(f"Hide `{self.hide_id}` has been saved! You can dismiss the previous message, or continue editing.", ephemeral=True)
                else:
                    # New hide: create a new unpublished hide entry, even if incomplete
                    hide_id = await get_next_gc_code(session)
                    await add_hide(
                        session,
                        hide_id,
                        interaction.user.id,
                        self.hide_data.name,
                        float(self.hide_data.lat) if self.hide_data.lat is not None else None,
                        float(self.hide_data.lon) if self.hide_data.lon is not None else None,
                        self.hide_data.description,
                        self.hide_data.difficulty if self.hide_data.difficulty is not None else None,
                        self.hide_data.terrain if self.hide_data.terrain is not None else None,
                        None,  # hidden_at (or set to datetime.now() if you want)
                        self.hide_data.container,  # size
                        self.hide_data.location if self.hide_data.location is not None else None  # location_name
                    )
                    containernametoid = await container_name_to_id(self.hide_data.container) if self.hide_data.container else None
                    await update_hide_containerid(session, hide_id, containernametoid)
                    await update_hide_writing_instrument(session, hide_id, self.hide_data.writing_instrument_id)
                    # Remove pen from inventory if selected and container size is Medium or larger
                    if self.hide_data.writing_instrument_id and self.hide_data.container:
                        if any(size in self.hide_data.container for size in [".8", ".9", ".10"]):
                            await remove_inv_item(session, interaction.user.id, self.hide_data.writing_instrument_id)
                    self.hide_id = hide_id
                    await interaction.followup.send(f"Hide `{hide_id}` has been saved! You can dismiss the previous message, or continue editing.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error saving hide: {e}", ephemeral=True)
        # Update the embed using HideConfigureSelect
        config_select = HideConfigureSelect(self.hide_data, self.interaction, self.original_message, hide_id=self.hide_id)
        await config_select.update_embed(interaction)

    async def publish_hide(self, interaction: discord.Interaction):
        """
        Save the current hide configuration and set published=1.
        Only allows publishing if all required fields are filled in.
        Handles both new and existing (unpublished) hides using hide_id if present.
        """
        try:
            async with Session() as session:
                # Gather all required fields
                required_fields = [
                    self.hide_data.name,
                    self.hide_data.lat,
                    self.hide_data.lon,
                    self.hide_data.description,
                    self.hide_data.difficulty,
                    self.hide_data.terrain,
                    self.hide_data.container,
                    self.hide_data.location
                ]
                if not all(field is not None and field != "" for field in required_fields):
                    await interaction.followup.send(
                        "Please fill out all fields before publishing your hide. If you want to save it for later, use the 'Save' option.",
                        ephemeral=True
                    )
                    return

                if self.hide_id:
                    hide = await get_hide_by_id(session, self.hide_id)
                    if not hide:
                        await interaction.followup.send(f"No unpublished hide with ID `{self.hide_id}` found.", ephemeral=True)
                        return
                    # Update all fields as in save_hide
                    await update_hide_name(session, self.hide_id, self.hide_data.name)
                    await update_hide_location(session, self.hide_id, float(self.hide_data.lat), float(self.hide_data.lon))
                    await update_hide_description(session, self.hide_id, self.hide_data.description)
                    await update_hide_difficulty(session, self.hide_id, self.hide_data.difficulty)
                    await update_hide_terrain(session, self.hide_id, self.hide_data.terrain)
                    await update_hide_size(session, self.hide_id, self.hide_data.container)
                    functionname = self.hide_data.container.replace(" (NO LOG)", "")
                    containernametoid = await container_name_to_id(functionname)
                    print(self.hide_data.container if hasattr(self.hide_data, 'container') else None)
                    print(self.hide_data.container_id if hasattr(self.hide_data, 'container_id') else None)
                    print(containernametoid if containernametoid else "No container ID found")
                    await update_hide_containerid(session, self.hide_id, containernametoid)
                    logbookid = await logbook_name_to_id(self.hide_data.log)
                    print(self.hide_data.log if hasattr(self.hide_data, 'log') else None)
                    print(self.hide_data.log_id if hasattr(self.hide_data, 'log_id') else None)
                    print(self.hide_data.log_status if hasattr(self.hide_data, 'log_status') else None)
                    print(logbookid if logbookid else "No logbook ID found")
                    await remove_inv_item(session, interaction.user.id, logbookid)
                    await update_hide_logbook(session, self.hide_id, logbookid)
                    await update_hide_location_name(session, self.hide_id, self.hide_data.location)
                    await update_hide_hidden_at(session, self.hide_id, datetime.now())
                    # Set published=1
                    await update_hide_published(session, self.hide_id, 1)
                    if self.hide_data.writing_instrument_id:
                        await remove_inv_item(session, interaction.user.id, self.hide_data.writing_instrument_id)
                    embed = discord.Embed(
                        title="Hide Published!",
                        description=f"Your hide has been successfully published with the code: `{self.hide_id}` and the container has been removed from your inventory.",
                        colour=0x00f51d
                    )
                    embed.add_field(name="Name:", value=self.hide_data.name, inline=False)
                    embed.add_field(name="Description:", value=self.hide_data.description, inline=False)
                    embed.add_field(name="Location:", value=self.hide_data.location, inline=False)
                    embed.add_field(name="Difficulty:", value=f"{str(self.hide_data.difficulty).replace('.0', '')}/5", inline=False)
                    embed.add_field(name="Terrain:", value=f"{str(self.hide_data.terrain).replace('.0', '')}/5", inline=False)
                    embed.add_field(name="Container:", value=self.hide_data.container, inline=False)
                    if self.original_message is not None:
                        await self.original_message.edit(embed=embed, view=None)
                else:
                    # New hide: create and publish
                    hide_id = await get_next_gc_code(session)
                    await add_hide(
                        session,
                        hide_id,
                        interaction.user.id,
                        self.hide_data.name,
                        float(self.hide_data.lat),
                        float(self.hide_data.lon),
                        self.hide_data.description,
                        self.hide_data.difficulty,
                        self.hide_data.terrain,
                        datetime.now(),
                        self.hide_data.container,
                        self.hide_data.location
                    )
                    await update_hide_published(session, hide_id, 1)
                    print(self.hide_data.container if hasattr(self.hide_data, 'container') else None)
                    print(self.hide_data.container_id if hasattr(self.hide_data, 'container_id') else None)
                    functionname = self.hide_data.container.replace(" (NO LOG)", "")
                    containernametoid = await container_name_to_id(functionname)
                    print(containernametoid if containernametoid else "No container ID found")
                    await update_hide_containerid(session, hide_id, containernametoid)
                    if self.hide_data.writing_instrument_id:
                        await remove_inv_item(session, interaction.user.id, self.hide_data.writing_instrument_id)
                    logbookid = await logbook_name_to_id(self.hide_data.log)
                    await update_hide_logbook(session, hide_id, logbookid)
                    await remove_inv_item(session, interaction.user.id, logbookid)
                    print(self.hide_data.log if hasattr(self.hide_data, 'log') else None)
                    print(self.hide_data.log_id if hasattr(self.hide_data, 'log_id') else None)
                    print(self.hide_data.log_status if hasattr(self.hide_data, 'log_status') else None)
                    print(logbookid if logbookid else "No logbook ID found")
                    self.hide_id = hide_id
                    embed = discord.Embed(
                        title="Hide Published!",
                        description=f"Your hide has been successfully published with the code: `{self.hide_id}` and the container has been removed from your inventory.",
                        colour=0x00f51d
                    )
                    embed.add_field(name="Name:", value=self.hide_data.name, inline=False)
                    embed.add_field(name="Description:", value=self.hide_data.description, inline=False)
                    embed.add_field(name="Location:", value=self.hide_data.location, inline=False)
                    embed.add_field(name="Difficulty:", value=f"{str(self.hide_data.difficulty).replace('.0', '')}/5", inline=False)
                    embed.add_field(name="Terrain:", value=f"{str(self.hide_data.terrain).replace('.0', '')}/5", inline=False)
                    embed.add_field(name="Container:", value=self.hide_data.container, inline=False)
                    if self.original_message is not None:
                        await self.original_message.edit(embed=embed, view=None)
        except Exception as e:
            await interaction.followup.send(f"Error publishing hide: {e}", ephemeral=True)

class BackToConfigButton(Button):
    def __init__(self, hide_data, interaction, original_message, hide_id=None):
        super().__init__(label="Back", style=discord.ButtonStyle.secondary)
        self.hide_data = hide_data
        self.interaction = interaction
        self.original_message = original_message
        self.hide_id = hide_id

    async def callback(self, interaction: discord.Interaction):
        view = View()
        view.add_item(HideConfigureSelect(self.hide_data, self.interaction, self.original_message, hide_id=self.hide_id))
        embed = discord.Embed(
            title="Configure Your Hide",
            description="Use the dropdown below to configure your hide.",
            colour=0xad7e66
        )
        embed.add_field(name="Name", value=self.hide_data.name or "Not set", inline=False)
        embed.add_field(name="Location", value=self.hide_data.location or "Not set", inline=False)
        embed.add_field(name="Description", value=self.hide_data.description or "Not set", inline=False)
        embed.add_field(name="Difficulty", value=f"{self.hide_data.difficulty}/5" if self.hide_data.difficulty else "Not set", inline=True)
        embed.add_field(name="Terrain", value=f"{self.hide_data.terrain}/5" if self.hide_data.terrain else "Not set", inline=True)
        embed.add_field(name="Container", value=self.hide_data.container or "Not set", inline=False)
        if getattr(self.hide_data, 'log_status', None) == True:
            embed.add_field(name="Logbook", value=self.hide_data.log or "Not set", inline=False)
        if self.hide_data.writing_instrument_id:
            wi = "MiniWrite Pencil (5.19)" if self.hide_data.writing_instrument_id == "5.19" else "MiniWrite Pen (5.20)"
            embed.add_field(name="Writing Instrument", value=wi, inline=False)
        await self.original_message.edit(embed=embed, view=view)

class LocationSelect(Select):
    def __init__(self, hide_data: HideConfigData, interaction: discord.Interaction, original_message: discord.Message, hide_id: str = None):
        self.hide_data = hide_data
        self.interaction = interaction
        self.original_message = original_message  
        self.hide_id = hide_id
        options = [
            discord.SelectOption(label=location, value=location) for location in LOCATION_COORDS.keys()
        ]
        super().__init__(placeholder="Select a location", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except Exception:
            pass
        selected_location = self.values[0]
        self.hide_data.location = selected_location
        self.hide_data.lat, self.hide_data.lon = LOCATION_COORDS[selected_location]
        # Restore main config menu after selection
        view = View()
        view.add_item(HideConfigureSelect(self.hide_data, interaction, self.original_message, hide_id=self.hide_id))
        embed = discord.Embed(
            title="Configure Your Hide",
            description="Use the dropdown below to configure your hide.",
            colour=0xad7e66
        )
        embed.add_field(name="Name", value=self.hide_data.name or "Not set", inline=False)
        embed.add_field(name="Location", value=self.hide_data.location or "Not set", inline=False)
        embed.add_field(name="Description", value=self.hide_data.description or "Not set", inline=False)
        embed.add_field(name="Difficulty", value=f"{self.hide_data.difficulty}/5" if self.hide_data.difficulty else "Not set", inline=True)
        embed.add_field(name="Terrain", value=f"{self.hide_data.terrain}/5" if self.hide_data.terrain else "Not set", inline=True)
        embed.add_field(name="Container", value=self.hide_data.container or "Not set", inline=False)
        if getattr(self.hide_data, 'log_status', None) == True:
            embed.add_field(name="Logbook", value=self.hide_data.log or "Not set", inline=False)
        if self.hide_data.writing_instrument_id:
            wi = "MiniWrite Pencil (5.19)" if self.hide_data.writing_instrument_id == "5.19" else "MiniWrite Pen (5.20)"
            embed.add_field(name="Writing Instrument", value=wi, inline=False)
        await self.original_message.edit(embed=embed, view=view)

class DifficultySelect(Select):
    def __init__(self, hide_data: HideConfigData, interaction: discord.Interaction, original_message: discord.Message, hide_id: str = None):
        self.hide_data = hide_data
        self.interaction = interaction
        self.original_message = original_message  
        self.hide_id = hide_id
        options = [
            discord.SelectOption(label=f"{i/2}", value=f"{i/2}") for i in range(2, 11) 
        ]
        super().__init__(placeholder="Select difficulty (1.0-5.0)", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except Exception:
            pass
        self.hide_data.difficulty = float(self.values[0])
        # Restore main config menu after selection
        view = View()
        view.add_item(HideConfigureSelect(self.hide_data, interaction, self.original_message, hide_id=self.hide_id))
        embed = discord.Embed(
            title="Configure Your Hide",
            description="Use the dropdown below to configure your hide.",
            colour=0xad7e66
        )
        embed.add_field(name="Name", value=self.hide_data.name or "Not set", inline=False)
        embed.add_field(name="Location", value=self.hide_data.location or "Not set", inline=False)
        embed.add_field(name="Description", value=self.hide_data.description or "Not set", inline=False)
        embed.add_field(name="Difficulty", value=f"{self.hide_data.difficulty}/5" if self.hide_data.difficulty else "Not set", inline=True)
        embed.add_field(name="Terrain", value=f"{self.hide_data.terrain}/5" if self.hide_data.terrain else "Not set", inline=True)
        embed.add_field(name="Container", value=self.hide_data.container or "Not set", inline=False)
        if getattr(self.hide_data, 'log_status', None) == True:
            embed.add_field(name="Logbook", value=self.hide_data.log or "Not set", inline=False)
        if self.hide_data.writing_instrument_id:
            wi = "MiniWrite Pencil (5.19)" if self.hide_data.writing_instrument_id == "5.19" else "MiniWrite Pen (5.20)"
            embed.add_field(name="Writing Instrument", value=wi, inline=False)
        await self.original_message.edit(embed=embed, view=view)

class TerrainSelect(Select):
    def __init__(self, hide_data: HideConfigData, interaction: discord.Interaction, original_message: discord.Message, hide_id: str = None):
        self.hide_data = hide_data
        self.interaction = interaction
        self.original_message = original_message 
        self.hide_id = hide_id
        options = [
            discord.SelectOption(label=f"{i/2}", value=f"{i/2}") for i in range(2, 11)  
        ]
        super().__init__(placeholder="Select terrain (1.0-5.0)", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except Exception:
            pass
        self.hide_data.terrain = (self.values[0])
        # Restore main config menu after selection
        view = View()
        view.add_item(HideConfigureSelect(self.hide_data, interaction, self.original_message, hide_id=self.hide_id))
        embed = discord.Embed(
            title="Configure Your Hide",
            description="Use the dropdown below to configure your hide.",
            colour=0xad7e66
        )
        embed.add_field(name="Name", value=self.hide_data.name or "Not set", inline=False)
        embed.add_field(name="Location", value=self.hide_data.location or "Not set", inline=False)
        embed.add_field(name="Description", value=self.hide_data.description or "Not set", inline=False)
        embed.add_field(name="Difficulty", value=f"{self.hide_data.difficulty}/5" if self.hide_data.difficulty else "Not set", inline=True)
        embed.add_field(name="Terrain", value=f"{self.hide_data.terrain}/5" if self.hide_data.terrain else "Not set", inline=True)
        embed.add_field(name="Container", value=self.hide_data.container or "Not set", inline=False)
        if getattr(self.hide_data, 'log_status', None) == True:
            embed.add_field(name="Logbook", value=self.hide_data.log or "Not set", inline=False)
        if self.hide_data.writing_instrument_id:
            wi = "MiniWrite Pencil (5.19)" if self.hide_data.writing_instrument_id == "5.19" else "MiniWrite Pen (5.20)"
            embed.add_field(name="Writing Instrument", value=wi, inline=False)
        await self.original_message.edit(embed=embed, view=view)

class InputModal(Modal):
    def __init__(self, title: str, field_name: str, hide_data: HideConfigData, interaction: discord.Interaction, original_message: discord.Message):
        super().__init__(title=title)
        self.field_name = field_name
        self.hide_data = hide_data
        self.interaction = interaction
        self.original_message = original_message 
        self.input_field = TextInput(
            label=f"Enter {field_name}",
            placeholder=f"Enter the {field_name.lower()} here...",
            required=True
        )
        self.add_item(self.input_field)

    async def on_submit(self, interaction: discord.Interaction):
        setattr(self.hide_data, self.field_name, self.input_field.value)
        # Always acknowledge the modal submission first
        try:
            await interaction.response.defer()
        except Exception:
            pass
        # Always update the main dropdown message's embed and view with the new values
        if self.original_message is not None:
            select = HideConfigureSelect(self.hide_data, interaction, self.original_message, hide_id=getattr(self, 'hide_id', None))
            await select.update_embed(interaction)
        else:
            select = HideConfigureSelect(self.hide_data, interaction, None, hide_id=getattr(self, 'hide_id', None))
            await select.update_embed(interaction)

class ContainerSelectionView(View):
    def __init__(self, deduped_items, item_to_container, user_id, original_message):
        super().__init__(timeout=None)
        self.containers = deduped_items
        self.item_map = item_to_container
        self.user_id = user_id
        self.original_message = original_message
        self.hide_data = HideConfigData()

    @discord.ui.button(label="Select Container", style=discord.ButtonStyle.primary)
    async def select_container(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(embed=YOUCANTUSETHIS, ephemeral=True)
            return
        await interaction.response.send_modal(
            ContainerSelectionModal(
                containers=self.containers,
                item_map=self.item_map,
                user_id=self.user_id,
                original_message=self.original_message,
                hide_data=self.hide_data
            )
        )

class ContainerSelectionModal(Modal, title="Select a Container"):
    def __init__(self, containers, item_map, user_id, original_message, hide_data):
        super().__init__(timeout=None)
        self.containers = containers
        self.item_map = item_map
        self.user_id = user_id
        self.original_message = original_message
        self.hide_data = hide_data

        self.container_input = TextInput(
            label="Enter container number",
            placeholder="e.g. 1",
            required=True,
            max_length=3
        )
        self.add_item(self.container_input)

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.container_input.value.strip()
        # parse index
        try:
            idx = int(raw) - 1
        except ValueError:
            return await interaction.response.send_message(
                "Please enter a valid number.", ephemeral=True
            )

        # bounds check
        if not 0 <= idx < len(self.containers):
            return await interaction.response.send_message(
                f"Number must be between 1 and {len(self.containers)}.", ephemeral=True
            )

        # unpack
        display_name, raw_key = self.containers[idx]
        # no‑log path
        if "(NO LOG)" in display_name:
            async with Session() as session:
                hide_id = await get_next_gc_code(session)
                hide = await start_hide(session, hide_id, self.user_id)
                hide_id = hide.id  # Use the existing or new hide's ID
            return await self._handle_missing_log(interaction, display_name, raw_key)

        # normal path
        await self._handle_container_selected(interaction, display_name, raw_key)

    async def _handle_container_selected(self, interaction, name, key):
       # await interaction.response.send_message(
        #    f"Container **{name}** selected.", ephemeral=True
        #)
        await interaction.response.defer()
        embed = discord.Embed(
            title="Configure Your Hide",
            description="Use the dropdown below to select options.",
            colour=0xad7e66
        )
        embed.add_field(name="Selected Container", value=name, inline=False)

        print(name)
        print(key)

        self.hide_data.container = name
        self.hide_data.container_id = key
        view = View(timeout=None)
        view.add_item(HideConfigureSelect(self.hide_data, interaction, self.original_message))

        # Only update the original message, do not send a new message in response to the modal
        if self.original_message is not None:
            await self.original_message.edit(embed=embed, view=view)
         #   await interaction.followup.send(
          #      f"Container **{name}** selected.", ephemeral=True
           # )
        else:
            await interaction.response.send_message(
                embed=embed, view=view, ephemeral=False
            )

    async def publish_hide(self, interaction: discord.Interaction):
        # fetch inventory and count logs
        async with Session() as session:
            inv = await get_inventory(session, self.user_id)
        # extract numeric IDs
        ids = [int(''.join(filter(str.isdigit, str(i)))) for i in inv if ''.join(filter(str.isdigit, str(i))).isdigit()]
        log_ids = [i for i in ids if i in (45, 46, 47)]
        counts = Counter(log_ids)

        # build embed
        embed = discord.Embed(
            title="Select a Log for your container",
            description="No log was found in this container. Pick one:",
            colour=0xad7e66
        )
        for num, (log_id, cnt) in enumerate(counts.items(), start=1):
            parts = re.findall(r'\d+|\.\d+|[A-Za-z]', str(log_id))
            main = MAIN_INVENTORY.get(parts[0], str(log_id))
            alts = [ALT_INVENTORY.get(p, "") for p in parts[1:]]
            label = f"{cnt}x {main} {' '.join(alts)}".strip()
            if cnt == 1:
                label = f"{main} {' '.join(alts)}".strip()
            embed.add_field(name=f"{num}. {label}", value="", inline=False)
            
        hide_data = HideConfigData()
      #  hide_data.container = display_name
       # hide_data.container_id = raw_key
        hide_data.log_status = True
        hide_data.log = label
        print(hide_data.container)

        view = LogSelectionView(self.user_id, list(counts.items()), self.original_message, hide_data)
        await interaction.response.edit_message(embed=embed, view=view)

class LogSelectionView(View):
    def __init__(self, user_id, counts_list, original_message, hide_data):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.counts_list = counts_list  # list of (log_id, count)
        self.original_message = original_message
        self.hide_data = hide_data

    @discord.ui.button(label="Select Log", style=discord.ButtonStyle.primary)
    async def select_log(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LogSelectionModal(self.counts_list, self.original_message, self.hide_data))

class LogSelectionModal(Modal, title="Select a Log"):
    def __init__(self, counts_list, original_message, hide_data):
        super().__init__(timeout=None)
        self.counts_list = counts_list
        self.original_message = original_message
        self.hide_data = hide_data
        self.log_input = TextInput(
            label="Enter log number",
            placeholder="e.g. 1",
            required=True,
            max_length=3
        )
        self.add_item(self.log_input)

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.log_input.value.strip()
        try:
            idx = int(raw) - 1
        except ValueError:
            return await interaction.response.send_message("Enter a valid number.", ephemeral=True)

        if not 0 <= idx < len(self.counts_list):
            return await interaction.response.send_message(
                f"Number must be between 1 and {len(self.counts_list)}.", ephemeral=True
            )

        log_id, _ = self.counts_list[idx]
        parts = re.findall(r'\d+|\.\d+|[A-Za-z]', str(log_id))
        main = MAIN_INVENTORY.get(parts[0], str(log_id))
        alts = [ALT_INVENTORY.get(p, "") for p in parts[1:]]
        name = f"{main} {' '.join(alts)}".strip()

        print(main)

        if "Plain Paper Log" in main:
            nuh_uh_sizes = ["L", "XL"]
            if any(size in self.hide_data.container for size in nuh_uh_sizes):
                return await interaction.response.send_message(
                    "You cannot use a Plain Paper Log with a Large or Extra Large container. Please select a different log.",
                    ephemeral=True
                )
        
        if "Small Notepad Log" in main:
            nuh_uh_sizes = ["XS", "S", "XL"]
            if any(size in self.hide_data.container for size in nuh_uh_sizes):
                # Remove pen from inventory if selected and container size is Medium or larger
                if self.hide_data.writing_instrument_id and self.hide_data.container:
                    if any(size in self.hide_data.container for size in [".8", ".9", ".10"]):
                        async with Session() as session:
                            await remove_inv_item(session, interaction.user.id, self.hide_data.writing_instrument_id)
                return await interaction.response.send_message(
                    "You cannot use a Small Notepad Log with an Extra Small, Small or Extra Large container. Please select a different log.",
                    ephemeral=True
                )
    
        if "Notebook Log" in main:
            nuh_uh_sizes = ["XS", "S", "M"]
            if any(size in self.hide_data.container for size in nuh_uh_sizes):
                return await interaction.response.send_message(
                    "You cannot use a Notebook Log with an Extra Small, Small or Medium container. Please select a different log.",
                    ephemeral=True
                )

        # build next embed
        embed = discord.Embed(
            title="Configure Your Hide",
            description="Now configure the details of your hide.",
            colour=0xad7e66
        )
        embed.add_field(name="Selected Logbook", value=name, inline=False)

        # Use the existing hide_data object and update only the log fields
        self.hide_data.log_id = log_id
        self.hide_data.log = name
        self.hide_data.log_status = True

        view = View(timeout=None)
        view.add_item(HideConfigureSelect(self.hide_data, interaction, self.original_message))

        await self.original_message.edit(embed=embed, view=view)
        await interaction.response.defer()
            
class ContainerSelectionView(View):
    def __init__(self, deduped_items, item_to_container, user_id, original_message):
        super().__init__(timeout=None)
        self.containers = deduped_items
        self.item_map = item_to_container
        self.user_id = user_id
        self.original_message = original_message
        self.hide_data = HideConfigData()

    @discord.ui.button(label="Select Container", style=discord.ButtonStyle.primary)
    async def select_container(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ContainerSelectionModal(
                containers=self.containers,
                item_map=self.item_map,
                user_id=self.user_id,
                original_message=self.original_message,
                hide_data=self.hide_data
            )
        )

class ExistingHideSelectionModal(Modal, title="Select a Hide"):
    def __init__(self, hide, item_map, user_id, original_message, hide_data):
        super().__init__(timeout=None)
        self.hide = hide
        self.item_map = item_map
        self.user_id = user_id
        self.original_message = original_message
        self.hide_data = hide_data

        self.hide_input = TextInput(
            label="Enter hide ID",
            placeholder="e.g. GX1",
            required=True,
            max_length=3
        )
        self.add_item(self.hide_input)

    async def on_submit(self, interaction: discord.Interaction):
        raw = self.container_input.value.strip()
        # parse index
        try:
            idx = int(raw) - 1
        except ValueError:
            return await interaction.response.send_message(
                "Please enter a valid number.", ephemeral=True
            )

        # bounds check
        if not 0 <= idx < len(self.containers):
            return await interaction.response.send_message(
                f"Number must be between 1 and {len(self.containers)}.", ephemeral=True
            )

        # unpack
        display_name, raw_key = self.containers[idx]
        # no‑log path
        if "(NO LOG)" in display_name:
            async with Session() as session:
                hide_id = await get_next_gc_code(session)
                hide = await start_hide(session, hide_id, self.user_id)
                hide_id = hide.id  # Use the existing or new hide's ID
            return await self._handle_missing_log(interaction, display_name, raw_key)

        # normal path
        await self._handle_container_selected(interaction, display_name, raw_key)

    async def _handle_container_selected(self, interaction, name, key):
        # build configuration embed
        embed = discord.Embed(
            title="Configure Your Hide",
            description="Use the dropdown below to select options.",
            colour=0xad7e66
        )
        embed.add_field(name="Selected Container", value=name, inline=False)

        print(name)
        print(key)

        # prepare next view
        self.hide_data.container = name
        self.hide_data.container_id = key
        view = View(timeout=None)
        view.add_item(HideConfigureSelect(self.hide_data, interaction, self.original_message))

        # Only update the original message, do not send a new message in response to the modal
        if self.original_message is not None:
            await self.original_message.edit(embed=embed, view=view)
         #   await interaction.followup.send(
          #      f"Container **{name}** selected.", ephemeral=True
           # )
        else:
            await interaction.response.send_message(
                embed=embed, view=view, ephemeral=False
            )

async def load_hide_data_from_db(hide_id: str) -> HideConfigData:
    async with Session() as session:
        hide = await get_hide_by_id(session, hide_id)
        if not hide:
            return None
        data = HideConfigData()
        data.name = hide.name
        data.location = hide.location_name
        data.description = hide.description
        data.difficulty = hide.difficulty
        data.terrain = hide.terrain
        data.lat = hide.location_lat
        data.lon = hide.location_lon
        data.container = hide.size
        data.container_id = None  # Not stored in DB, set later if needed
        # Optionally add log fields if you support them
        return data

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

async def start_hide_configuration(interaction, hide_data, hide_id=None):
    embed = discord.Embed(
        title="Configure Your Hide",
        description="Use the dropdown below to configure your hide.",
        colour=0xad7e66
    )
    embed.add_field(name="Name", value=hide_data.name or "Not set", inline=False)
    embed.add_field(name="Location", value=hide_data.location or "Not set", inline=False)
    embed.add_field(name="Description", value=hide_data.description or "Not set", inline=False)
    embed.add_field(name="Difficulty", value=f"{hide_data.difficulty}/5" if hide_data.difficulty else "Not set", inline=True)
    embed.add_field(name="Terrain", value=f"{hide_data.terrain}/5" if hide_data.terrain else "Not set", inline=True)
    embed.add_field(name="Container", value=hide_data.container or "Not set", inline=False)
    if getattr(hide_data, 'log_status', None) == True:
        embed.add_field(name="Logbook", value=hide_data.log or "Not set", inline=False)

    view = View()
    # Temporarily pass None for original_message, will update after send
    select = HideConfigureSelect(hide_data, interaction, None, hide_id=hide_id)
    view.add_item(select)
    sent_msg = await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    # If using followup, use: sent_msg = await interaction.followup.send(...)
    # Get the message object (for persistent views, use interaction.original_response())
    try:
        msg = await interaction.original_response()
    except Exception:
        msg = sent_msg  # fallback
    # Patch the view to use the real message reference
    view = View()
    select = HideConfigureSelect(hide_data, interaction, msg, hide_id=hide_id)
    view.add_item(select)
    await msg.edit(view=view)
    return msg

async def container_name_to_id(container_name: str) -> str:
    """
    Convert a container display name (e.g., 'Plastic Container XL Camo w/ Log (Plain Paper)')
    to its corresponding ID (e.g., '7.10.18L').
    """
    # Find if log is present
    log_match = re.search(r'w/ Log \((.*?)\)', container_name)
    log_id = ''
    if log_match:
        log_name = log_match.group(1)
        for k, v in ALT_INVENTORY.items():
            if v.lower().startswith('log') and log_name.lower() in v.lower():
                log_id = k
                break
        container_name = container_name[:log_match.start()].strip()

    parts = container_name.split()
    size_id = ''
    color_id = ''
    main_type = ''
    # Only use container size keys
    container_size_keys = {k for k, v in ALT_INVENTORY.items() if v in ['XS', 'S', 'M', 'L', 'XL']}
    container_color_keys = {k for k, v in ALT_INVENTORY.items() if k in ['.11', '.12', '.13', '.14', '.15', '.16', '.17', '.18']}
    container_colors = {ALT_INVENTORY[k]: k for k in container_color_keys}
    # Find size (XS, S, M, L, XL)
    for k in container_size_keys:
        v = ALT_INVENTORY[k]
        if parts and parts[-2] == v:
            size_id = k
            break
        elif parts and parts[-1] == v:
            size_id = k
            break
    # Find color (Red, Orange, Yellow, Green, Blue, Purple, Black, Camo) for containers only
    for color, k in container_colors.items():
        if parts and parts[-1] == color:
            color_id = k
            break
        elif len(parts) > 1 and parts[-2] == color:
            color_id = k
            break
    # Remove size and color from parts to get main type
    filtered_parts = [p for p in parts if p not in ['XS', 'S', 'M', 'L', 'XL'] and p not in container_colors]
    main_type = ' '.join(filtered_parts)
    main_id = ''
    for k, v in MAIN_INVENTORY.items():
        if v.lower() == main_type.lower():
            main_id = k
            break
    id_parts = [main_id]
    if size_id:
        id_parts.append(size_id)
    if color_id:
        id_parts.append(color_id)
    if log_id:
        id_parts.append(log_id)
    return ''.join(id_parts)

async def logbook_name_to_id(logbook_name: str) -> str:
    """
    Convert a logbook display name (e.g., 'Plain Paper', 'Small Notepad', 'Notebook')
    to its corresponding ID (e.g., '45', '46', '47').
    Accepts partial or case-insensitive matches. Only returns 45, 46, or 47.
    """
    logbook_name = logbook_name.strip().lower()
    valid_ids = {"45", "46", "47"}
    for k, v in MAIN_INVENTORY.items():
        if k in valid_ids and logbook_name in v.lower():
            return k
    for k, v in ALT_INVENTORY.items():
        if k in valid_ids and logbook_name in v.lower():
            return k
    # fallback: try exact match on value
    for k, v in MAIN_INVENTORY.items():
        if k in valid_ids and logbook_name == v.lower():
            return k
    for k, v in ALT_INVENTORY.items():
        if k in valid_ids and logbook_name == v.lower():
            return k
    return ''  # Not found

class WritingInstrumentSelect(View):
    def __init__(self, pen_options, on_select_callback, user_id, timeout=180):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.on_select_callback = on_select_callback
        self.add_item(self.WritingInstrumentDropdown(pen_options, self))

    class WritingInstrumentDropdown(Select):
        def __init__(self, pen_options, parent_view):
            options = [discord.SelectOption(label=pen, value=pen) for pen in pen_options]
            super().__init__(placeholder="Select a pen for your hide...", min_values=1, max_values=1, options=options)
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.parent_view.user_id:
                await interaction.response.send_message("You can't select a pen for someone else's hide!", ephemeral=True)
                return
            await self.parent_view.on_select_callback(interaction, self.values[0])