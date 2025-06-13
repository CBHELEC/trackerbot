import pycaching
import json
import operator
from google_images_search import GoogleImagesSearch
from googleapiclient.discovery import build
import discord
from discord import app_commands
import os
import psutil
from pathlib import Path
from datetime import datetime

from database import get_guild_settings, get_log_channel

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CX_ID = os.getenv('GOOGLE_SEARCH_ID')
GOOGLE_NORMAL_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
GOOGLE_NORMAL_SEARCH_ID = os.getenv('GOOGLE_SEARCH_NORMAL_ID')
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

YOUCANTDOTHIS = discord.Embed(title="<:denied:1336100920039313448> | You can't do this!",
                      colour=0xff0000)
YOUCANTDOTHIS.set_footer(text="!dev_cmds | !perm_cmds for info.")

NOPERMISSIONS = discord.Embed(title="<:denied:1336100920039313448> | I don't have permission to do this!",
                      colour=0xff0000)

RANDOMERROR = discord.Embed(title="<:denied:1336100920039313448> | An error occured! The Dev has been notified.",
                      colour=0xff0000)

YOUCANTUSETHIS = discord.Embed(title="<:denied:1336100920039313448> | You can't use this!",
                      colour=0xff0000)

GOD_LOG_ID = 1341819097591185479 
LOG_CHANNEL_ID = True
DEV_USER_ID = 820297275448098817
ERROR_LOG_ID = 1341107185777643573

def is_mod():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        mod_role_ids = {int(role) for role in settings.mod_role_ids.split(",") if role}

        if interaction.user.id == 820297275448098817 or any(role.id in mod_role_ids for role in interaction.user.roles):
            return True

        return False
    
    return app_commands.check(predicate)

def is_perm():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        perm_role_ids = {int(role) for role in settings.perm_role_ids.split(",") if role} 

        if interaction.user.id == 820297275448098817 or any(role.id in perm_role_ids for role in interaction.user.roles):
            return True
        
        return False
    
    return app_commands.check(predicate)

def is_perm_mod():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        mod_role_ids = {int(role) for role in settings.mod_role_ids.split(",") if role}
        perm_role_ids = {int(role) for role in settings.perm_role_ids.split(",") if role}

        if interaction.user.id == 820297275448098817 or \
           any(role.id in mod_role_ids for role in interaction.user.roles) or \
           any(role.id in perm_role_ids for role in interaction.user.roles):
            return True

        return False
    
    return app_commands.check(predicate)

def is_dev():
    async def predicate(interaction: discord.Interaction):
        dev_id = 820297275448098817
        
        if interaction.user.id != dev_id:  
            return False  
        
        return True
    
    return app_commands.check(predicate)

async def log_message(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the guild's log channel and the global log channel."""
    log_channel = get_log_channel(guild, bot)  
    global_log_channel = bot.get_channel(1341819097591185479)  

    if log_channel:
        await log_channel.send(f"{command_name} | {message}") 

    if global_log_channel:
        await global_log_channel.send(f"God Log - Guild: {guild.name}, ID: {guild.id} | {command_name} | {message}") 
        
async def master_log_message(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the guild's log channel and the global log channel."""
    master_log_channel = bot.get_channel(1341819097591185479)  

    if master_log_channel:
        await master_log_channel.send(f"{guild.name} ({guild.id}) | {command_name} | {message}") 
        
async def log_error(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the error channel."""
    log_channel = bot.get_channel(1341107185777643573)

    if log_channel:
        await log_channel.send(f"Error Log - Guild: {guild.name}, ID: {guild.id} | {command_name} | {message}") 

def is_moderator():
    async def predicate(interaction: discord.Interaction):
        staff_roles = [1368981000687845517, 1368978303381405791, 1368979240699166803, 1368979304595062956]
        user_role_ids = [role.id for role in interaction.user.roles]
        
        if not any(role_id in user_role_ids for role_id in staff_roles):
            await interaction.response.send_message(
                "<:denied:1336100920039313448> | You do not have permission to execute this command!", 
                ephemeral=True
            )
            return False  
        
        return True
    
    return app_commands.check(predicate)

operators = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv
}

eightball_answers = [
    "Yes.",
    "No.",
    "Maybe.",
    "I don't know.",
    "Definitely.",
    "Absolutely not.",
    "Could be.",
    "Probably.",
    "I'm not sure."
]

funny_eightball_answers = [
    "woof",
    "rawr",
    "potato",
    "uwu :3",
    "GIB FOOD",
    "i will send you to the basement.",
    "dinoshark has gf",
    "D5/T5 nano on a cliff",
    "i am superior.",
    "you know what else is massive <:devious:1341566707206197340> - Buckeye",
    ":Blobfish:",  
    "i love wet logs - said nobody ever",  
    "I dont care about answering your question, BUT do you also use multi million dollar satellites to find tupperware in the woods?",  
    "im in your walls, i know everything",  
    "free shavacado",  
    "1000 ammo can power trail",  
    "if you want a random persons license plate number contact @sharkanddino or @NightFlyer33",  
    "I dId NoT fInD tHe GeOcAcHe BuT i MaRkEd FoUnD bEcAuSe I aM lAzY",  
    "sigma",
    "furries are cool",
    "i am a furry",
    "cbh furry fr",
    "mikaboo is gullible"
]

class ImageSearchView(discord.ui.View):
    """View with buttons to navigate image search results."""
    def __init__(self, images, query, timeout: float = 50.0):
        super().__init__(timeout=timeout)
        self.images = images
        self.index = 0
        self.query = query
        self.msg = None
        self.update_buttons()

    async def on_timeout(self):
        """Disable all buttons when the view times out."""
        for button in self.children:
            button.disabled = True  
        if self.msg:
            await self.msg.edit(view=self)

    def update_buttons(self):
        """Update the state of navigation buttons."""
        for button in self.children:
            if button.custom_id == "first":
                button.disabled = self.index == 0
            elif button.custom_id == "previous":
                button.disabled = self.index == 0
            elif button.custom_id == "next":
                button.disabled = self.index >= len(self.images) - 1
            elif button.custom_id == "last":
                button.disabled = self.index >= len(self.images) - 1

    async def update_message(self, interaction: discord.Interaction):
        """Updates the embed with the new image result."""
        embed = discord.Embed(colour=0xad7e66)
        embed.set_footer(text=f"Image {self.index + 1} / 15 | {self.query} | Tracker",
        icon_url="https://i.imgur.com/kNe7FRh.png")
        embed.set_image(url=self.images[self.index])
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:first:1338154194640699442>", style=discord.ButtonStyle.primary, custom_id="first", disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the first image."""
        self.index = 0
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:previous:1338154278589825114>", style=discord.ButtonStyle.primary, custom_id="previous", disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the previous image."""
        if self.index > 0:
            self.index -= 1
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:next:1338154251121332246>", style=discord.ButtonStyle.primary, custom_id="next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the next image."""
        if self.index < len(self.images) - 1:
            self.index += 1
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:last:1338154217923416105>", style=discord.ButtonStyle.primary, custom_id="last")
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the last image."""
        self.index = len(self.images) - 1
        await self.update_message(interaction)
        
    @discord.ui.button(label="🔢", style=discord.ButtonStyle.primary)
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to a specified image."""
        
        class JumpModal(discord.ui.Modal, title="Jump to Page"):
            page_input = discord.ui.TextInput(
                label="Enter a page number 1-15",
                style=discord.TextStyle.short,
                required=True,
                min_length=1,
                max_length=2,
                placeholder="1-15"
            )

            async def on_submit(modal_self, modal_interaction: discord.Interaction):
                """Handles the submission of the page number."""
                try:
                    page = int(modal_self.page_input.value)
                    if 1 <= page <= 15:
                        self.index = page - 1
                        await self.update_message(modal_interaction)
                    else:
                        await modal_interaction.response.send_message("Invalid page number! Enter 1-15.", ephemeral=True)
                except ValueError:
                    await modal_interaction.response.send_message("Please enter a valid number.", ephemeral=True)

        await interaction.response.send_modal(JumpModal())
        
gis = GoogleImagesSearch(GOOGLE_API_KEY, GOOGLE_CX_ID)
    
def google_search(query):
    service = build("customsearch", "v1", developerKey=GOOGLE_NORMAL_API_KEY)
    res = service.cse().list(q=query, cx=GOOGLE_NORMAL_SEARCH_ID).execute()
    return res.get('items', [])

class GoogleSearchView(discord.ui.View):
    def __init__(self, results, query):
        super().__init__(timeout=300)
        self.results = results
        self.query = query
        self.index = 0
        self.update_buttons()

    def update_buttons(self):
        """Update button states based on current index."""
        self.first.disabled = self.index == 0
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index == len(self.results) - 1
        self.last.disabled = self.index == len(self.results) - 1

    async def update_message(self, interaction: discord.Interaction):
        """Update the embed message and buttons."""
        result = self.results[self.index]
        embed = discord.Embed(
            title=result['title'],
            url=result['link'],
            description=result.get('snippet', ''),
            color=0xad7e66,
        )
        embed.set_footer(text=f"Result {self.index + 1} / {len(self.results)} | {self.query} | Tracker", 
                         icon_url="https://i.imgur.com/kNe7FRh.png")
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="<:first:1338154194640699442>", style=discord.ButtonStyle.primary, disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to first result."""
        self.index = 0
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:previous:1338154278589825114>", style=discord.ButtonStyle.primary, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous result."""
        self.index = max(0, self.index - 1)
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:next:1338154251121332246>", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next result."""
        self.index = min(len(self.results) - 1, self.index + 1)
        await self.update_message(interaction)

    @discord.ui.button(emoji="<:last:1338154217923416105>", style=discord.ButtonStyle.primary)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to last result."""
        self.index = len(self.results) - 1
        await self.update_message(interaction)

    @discord.ui.button(label="🔢", style=discord.ButtonStyle.primary)
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Jump to a specified result."""
        class JumpModal(discord.ui.Modal, title="Jump to Page"):
            page_input = discord.ui.TextInput(
                label="Enter a page number",
                style=discord.TextStyle.short,
                required=True,
                min_length=1,
                max_length=2,
                placeholder=f"1-{len(self.results)}"
            )

            async def on_submit(modal_self, modal_interaction: discord.Interaction):
                try:
                    page = int(modal_self.page_input.value)
                    if 1 <= page <= len(self.results):
                        self.index = page - 1
                        await self.update_message(modal_interaction)
                    else:
                        await modal_interaction.response.send_message("Invalid page number!", ephemeral=True)
                except ValueError:
                    await modal_interaction.response.send_message("Please enter a valid number.", ephemeral=True)

        await interaction.response.send_modal(JumpModal())
        
class BadgeInfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

        self.badge_embed = discord.Embed(title="What do the badges mean?",
                      description="Badges in the BadgeGen system have eight quality levels, from Bronze to Diamond, representing the user’s achievements. After reaching Diamond, users can unlock \"loops\" (additional levels) and \"Addons\" (extra mini-badges). Addons are often challenging, rewarding experienced Geocachers with special achievements, such as completing a calendar or attending specific events. Some badges also have specific loops and addon requirements, making them harder to achieve. \n\n**Full details on each badge can be found [here](https://project-gc.com/w/BadgeGen).**",
                      colour=0xad7e66)
        self.belt_embed = discord.Embed(title="What do the belts mean?",
                      description="**The Belt system is based on points, which are awarded based on various criteria. The sum of all points determines the user's overall belt level. There are 36 possible belts.**\n\nIf the user has fewer than 30 points, they will receive the White belt.\nAt 30 points, a Yellow belt will be awarded.\nEvery ten/twelve points after that will give the user an extra stripe on their belt.\nAfter 220 points, 12 points are required per level\nAfter 4 stripes, the user will be awarded a new colour belt.\nWith the exception of the black belt.\nAt 400 points, the Golden Black Belt (the highest ranking) is awarded.\n\n**Points are awarded based on the following conditions**:\n1 point per 100 caches found.\n2 points per event hosted, maximum of 30 points.\n0.5 points per difficulty/terrain combination found in excess of 40 combinations.\n10 points for completing the Difficulty/Terrain matrix.\n20 points for either finding caches in 15 distinct states or 5 distinct countries. 40 points are not awarded if both conditions are satisfied.\n10 points per 50 caches found on day with most finds, maximum of 40 points.\n0.5 points per 7 consecutive days with finds in largest streak. 10 point bonus at 366 days.\n0.1 points per favorite point on owned caches.\n2 points per distinct cache type on day with most distinct types found.\n2 points per distinct cache type hidden.\n2 points per distinct cache size hidden.\n0.5 points per FTF, maximum of 30 points.\n1 point per 5/5 Difficulty/Terrain cache found, maximum 5 points.\n1 point per gemstone badge (excluding country badges). [1]\n2 points for every year since the user's first cache find.\n0.08 points per calendar day cached on. No points awarded if distinct days is less than 100. The year is irrelevant.\n0.05 points per Trackable moved/discovered (maximum 25 points).\n0.1 points per photo uploaded to found logs (maximum 25 points).\n\n**For more info, [click here](<https://project-gc.com/w/BadgeGen_Belts>).**",
                      colour=0xad7e66)

    @discord.ui.button(label="Badge", style=discord.ButtonStyle.primary)
    async def badge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the Badge button click."""
        await interaction.response.edit_message(embed=self.badge_embed, view=BadgeInfoView())

    @discord.ui.button(label="Belt", style=discord.ButtonStyle.success)
    async def belt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handles the Belt button click."""
        await interaction.response.edit_message(embed=self.belt_embed, view=BadgeInfoView())
        
STAR_EMOJIS = {"💀"}  
REACTION_THRESHOLD = 3 
SKULLBOARD_DATA_FILE = "skullboarded_messages.json"  

def load_skullboarded_messages():
    try:
        with open(SKULLBOARD_DATA_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return list(data.keys())  
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_skullboarded_messages(message_ids):
    with open(SKULLBOARD_DATA_FILE, "w") as f:
        json.dump(message_ids, f)

skullboarded_messages = load_skullboarded_messages()

gcblacklist = ["GC", "GCHQ"]
tbblacklist = ["TB", "TBF", "TBH", "TBS"]

POLL_JSON_FILE = "poll_dates.json"

def load_poll_date():
    """Load the last poll date from a JSON file."""
    try:
        with open(POLL_JSON_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_poll_date", None)
    except FileNotFoundError:
        return None 

def save_poll_date(date):
    """Save the current poll date to a JSON file."""
    with open(POLL_JSON_FILE, "w") as f:
        json.dump({"last_poll_date": date}, f)

last_poll_date = load_poll_date()


def get_cache_basic_info(geocache_codes=[], tb_codes=[]):
    final_message = []
    geocaching = pycaching.login(
        EMAIL, PASSWORD
    )
    for code in geocache_codes:
        try:
            cache = geocaching.get_cache(code)
            cache.load_quick()

            name = cache.name
            size = cache.size
            fps = cache.favorites
            difficulty = cache.difficulty
            terrain = cache.terrain
            author = cache.author
            pmo = cache.pm_only
            cache_type = cache.type
            state = cache.state
            status = cache.status

            if status == 0:
                prefix = None
            elif status == 1:
                prefix = "<:Disabled:1369009017552371902>"
            elif status == 2:
                prefix = "<:Archive:1369015619231420497>"

                # emoji_name = f"{cache_type.name if cache_type.name != 'lost_and_found_event' else 'community_celebration'}{'-disabled' if (not state) else ''}"
            emoji_name = f"{cache_type.name if cache_type.name != 'lost_and_found_event' else 'community_celebration'}"

            script_dir = os.path.dirname(__file__)
            file_path = os.path.join(script_dir, "name-icon.json")
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                emoji_text = data.get(emoji_name, {}).get("emoji", None)

            emoji_text = f"{prefix if prefix else ''}{emoji_text}"

            final_message.append(f"""{'<:Premium:1368989525405335552>' if pmo else ''}{emoji_text} [{code}](<https://coord.info/{code}>) - {name} | {author}
:light_blue_heart: {fps} | :mag_right: D{difficulty} - T{terrain} :mountain_snow: | <:tub:1327698135710957609> {size.value.capitalize()}""")

        except Exception as e:
            print(e)
            final_message.append(f"<:DNF:1368989100220092516> **That Geocache doesn't exist!**")

    for trackable in tb_codes:
        try:
            tb = geocaching.get_trackable(trackable)
            tb.load()

            name = tb.name
            owner = tb.owner

            final_message.append(
                f"""<:TravelBug:1368989710818480169> [{trackable}](<https://coord.info/{trackable}>) - {name} | {owner}"""
            )

        except Exception as e:
            final_message.append(f"<:DNF:1368989100220092516> **That Trackable doesn't exist!**")

    final_message = "\n\n".join(final_message)
    return final_message

def escape_markdown(text: str) -> str:
    """Escapes markdown characters in a string."""
    return text.replace("*", "\\*").replace("_", "\\_").replace("~", "\\~").replace("|", "\\|")

def get_formatted_ram_usage():
    mem = psutil.virtual_memory()
    used_gb = mem.used / 1024 / 1024 / 1024
    total_gb = mem.total / 1024 / 1024 / 1024
    percent = mem.percent
    return f"<:ram:1363597677912264966> | RAM: **{used_gb:.1f} / {total_gb:.1f} GB ({percent}%)**"

def get_formatted_cpu_usage():
    cpu_percent = psutil.cpu_percent(interval=1)

    cpu_temp = None
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read().strip()
            cpu_temp = int(temp_str) / 1000  
    except FileNotFoundError:
        pass  

    if cpu_temp is not None:
        return f"<:cpu:1363599094395834430> | CPU: **{cpu_percent}% @ {cpu_temp:.1f}°C**"
    else:
        return f"<:cpu:1363599094395834430> | CPU: **{cpu_percent}%**"
    
def get_formatted_storage_usage():
    disk = psutil.disk_usage('/')
    used_gb = disk.used / 1024 / 1024 / 1024
    total_gb = disk.total / 1024 / 1024 / 1024
    return f"<:ssd:1363600388959506585> | Storage: **{used_gb:.1f} / {total_gb:.1f} GB**"

async def get_current_vote_streak_topgg(interaction):
    channel = interaction.client.get_channel(1365079297919811725)
    if not isinstance(channel, discord.TextChannel):
        return None

    async for message in channel.history(limit=100):  # Search last 100 messages
        if interaction.user in message.mentions:
            for embed in message.embeds:
                if embed.fields:
                    for field in embed.fields:
                        if field.name.strip() == "Current Vote Streak:":
                            return field.value
    return None

async def find_latest_topgg_vote(bot, interaction):
    channel_id = 1365079297919811725
    channel = bot.get_channel(channel_id) 
    
    if channel is None:
        return "Channel not found."

    async for message in channel.history(limit=None): 
        if interaction.user.mention in message.content:
            return message.created_at

    return None

REMINDER_FILE = Path("reminded_users.json")
def load_reminded_users():
    if REMINDER_FILE.exists():
        with open(REMINDER_FILE, "r") as f:
            data = json.load(f)
            # Convert timestamp strings back to datetime objects
            return {int(k): datetime.fromisoformat(v) for k, v in data.items()}
    return {}

def save_reminded_users(cache):
    with open(REMINDER_FILE, "w") as f:
        # Convert datetime objects to ISO strings
        json.dump({str(k): v.isoformat() for k, v in cache.items()}, f, indent=2)