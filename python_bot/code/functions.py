from dotenv import load_dotenv
load_dotenv(verbose=True, override=True)

from pathlib import Path

CODE_DIR = Path(__file__).parent
DATA_DIR = CODE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

import asyncio
import re
import pycaching
import json
import operator
import os
import psutil
import discord
import re
import requests
from google_images_search import GoogleImagesSearch
from googleapiclient.discovery import build
from discord import app_commands
from datetime import datetime, date, time
from typing import Iterable
from database import get_guild_settings, get_log_channel

BOT_PREFIX = os.getenv("BOT_PREFIX")

GEOCACHING_USERNAME = os.getenv("GEOCACHING_USERNAME")
GEOCACHING_PASSWORD = os.getenv("GEOCACHING_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CX_ID = os.getenv('GOOGLE_SEARCH_ID')
GOOGLE_NORMAL_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
GOOGLE_NORMAL_SEARCH_ID = os.getenv("GOOGLE_SEARCH_NORMAL_ID")
BOTLISTME_API = os.getenv("BOTLISTME_API")

YOUCANTDOTHIS = discord.Embed(title="<:denied:1336100920039313448> | You can't do this!",
                      colour=0xff0000)
YOUCANTDOTHIS.set_footer(text=f"{BOT_PREFIX}dev_cmds | {BOT_PREFIX}perm_cmds for info.")

NOPERMISSIONS = discord.Embed(title="<:denied:1336100920039313448> | I don't have permission to do this!",
                      colour=0xff0000)

RANDOMERROR = discord.Embed(title="<:denied:1336100920039313448> | An error occured! The Dev has been notified.",
                      colour=0xff0000)

YOUCANTUSETHIS = discord.Embed(title="<:denied:1336100920039313448> | You can't use this!",
                      colour=0xff0000)

GOD_LOG_ID = int(os.getenv("GOD_LOG_ID"))
DEV_USER_ID = int(os.getenv("DEV_USER_ID"))
ERROR_LOG_ID = int(os.getenv("ERROR_LOG_ID"))
TOPGG_LOG_ID = 1365079297919811725

GC_LINK_SEARCH = r"https?://(www\.)?(geocaching\.com|coord\.info)"

def is_mod():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        mod_role_ids = {int(role) for role in settings.mod_role_ids.split(",") if role}

        if interaction.user.id == DEV_USER_ID or any(role.id in mod_role_ids for role in interaction.user.roles):
            return True

        return False
    
    return app_commands.check(predicate)

def is_perm():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        perm_role_ids = {int(role) for role in settings.perm_role_ids.split(",") if role} 

        if interaction.user.id == DEV_USER_ID or any(role.id in perm_role_ids for role in interaction.user.roles):
            return True
        
        return False
    
    return app_commands.check(predicate)

def is_perm_mod():
    async def predicate(interaction: discord.Interaction):
        settings = get_guild_settings(interaction.guild.id)
        mod_role_ids = {int(role) for role in settings.mod_role_ids.split(",") if role}
        perm_role_ids = {int(role) for role in settings.perm_role_ids.split(",") if role}

        if interaction.user.id == DEV_USER_ID or \
           any(role.id in mod_role_ids for role in interaction.user.roles) or \
           any(role.id in perm_role_ids for role in interaction.user.roles):
            return True

        return False
    
    return app_commands.check(predicate)

def is_dev():
    return app_commands.check(lambda interaction: interaction.user.id == DEV_USER_ID)

async def log_message(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the guild's log channel and the global log channel."""
    log_channel = get_log_channel(guild, bot)  
    global_log_channel = bot.get_channel(GOD_LOG_ID)  

    if log_channel:
        await log_channel.send(f"{command_name} | {message}") 

    if global_log_channel:
        await global_log_channel.send(f"God Log - Guild: {guild.name}, ID: {guild.id} | {command_name} | {message}") 

async def master_log_message(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the guild's log channel and the global log channel."""
    master_log_channel = bot.get_channel(GOD_LOG_ID)  

    if master_log_channel:
        await master_log_channel.send(f"{guild.name} ({guild.id}) | {command_name} | {message}") 

async def log_error(guild: discord.Guild, bot: discord.Client, command_name: str, message: str):
    """Logs a message to the error channel."""
    log_channel = bot.get_channel(ERROR_LOG_ID)

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
SKULLBOARD_DATA_FILE = DATA_DIR / "skullboarded_messages.json"  

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

GC_BLACKLIST = ["GC", "GCHQ", "GCFAQ", "GCC"]
TL_BLACKLIST = ["TL"]
GL_BLACKLIST = ["GL"]
PR_BLACKLIST = ["PR"]
TB_BLACKLIST = ["TB", "TBF", "TBH", "TBS", "TBDISCOVER", "TBDROP", "TBGRAB", "TBMISSING", "TBRETRIEVE", "TBVISIT"]
GT_BLACKLIST = ["GT"]

POLL_JSON_FILE = DATA_DIR / "poll_dates.json"

def load_poll_date() -> date:
    """Load the last poll date from a JSON file."""
    try:
        with open(POLL_JSON_FILE, "r") as f:
            data = json.load(f)
            if "last_poll_date" in data:
                return date.fromisoformat(data["last_poll_date"])
            return None
    except FileNotFoundError:
        return None

def save_poll_date(date: date):
    """Save the current poll date to a JSON file."""
    with open(POLL_JSON_FILE, "w") as f:
        json.dump({"last_poll_date": date.isoformat()}, f)

last_poll_date = load_poll_date()

INVITE_REGEX = re.compile(
    r'(https?:\/\/)?(www\.)?(discord\.gg|discord\.com\/invite)\/([A-Za-z0-9-]+)',
    re.IGNORECASE
)

def redact_discord_invites(text: str) -> str:
    return INVITE_REGEX.sub(
        lambda m: f"https​:/​/​discord​.gg​/rеdаctеd",
        text
    )

with (DATA_DIR / 'name-icon.json').open("r", encoding="utf-8") as file:
    emoji_names: dict[str, dict[str, str]] = json.load(file)

def get_emoji_from_name(emoji_name: str) -> str:
    global emoji_names
    return emoji_names.get(emoji_name, {}).get("emoji", "")

def find_gc_tb_codes(s: str) -> tuple[bool, set[str], set[str]]:
    """Find GC and TB codes in a string.

    Args:
        s (str): string to find gc and tb codes in

    Returns:
        tuple[bool, set[str], set[str]]: a tuple of whether codes were found, the gc code list, and the tb code list
    """
    gc_matches: list[str] = re.findall(r'(?<!:)\b(GC[A-Z0-9]{1,5})(?:\b|_)', s, re.IGNORECASE)
    tb_matches: list[str] = re.findall(r'(?<!:)\b(TB[A-Z0-9]{1,5})(?:\b|_)', s, re.IGNORECASE)

    gc_codes = {item.upper() for item in gc_matches if item.upper() not in GC_BLACKLIST}
    tb_codes = {item.upper() for item in tb_matches if item.upper() not in TB_BLACKLIST}

    if len(gc_codes) == 0 and len(tb_codes) == 0:
        return False, set(), set()

    return True, gc_codes, tb_codes

async def find_pr_codes(s: str) -> set[str]:
    """Find PR codes in a string.

    Args:
        s (str): string to find pr codes in

    Returns:
        set[str]: a set of pr codes found
    """
    pr_matches: list[str] = re.findall(r'(?<!:)\b(PR[A-Z0-9]{1,5})(?:\b|_)', s, re.IGNORECASE)

    pr_codes = {item.upper() for item in pr_matches if item.upper() not in PR_BLACKLIST}

    return pr_codes

async def find_gt_codes(s: str) -> set[str]:
    """Find PR codes in a string.

    Args:
        s (str): string to find pr codes in

    Returns:
        set[str]: a set of pr codes found
    """
    gt_matches: list[str] = re.findall(r'(?<!:)\b(GT[A-Z0-9]{1,3})(?:\b|_)', s, re.IGNORECASE)

    gt_codes = {item.upper() for item in gt_matches if item.upper() not in GT_BLACKLIST}

    return gt_codes

async def find_gl_tl_codes(s: str) -> tuple[set[str], set[str]]:
    """Find GL/TL codes in a string.

    Args:
        s (str): string to find GL/TL codes in

    Returns:
        tuple[set[str], set[str]]: a tuple of gl codes and tl codes found
    """
    gl_matches: list[str] = re.findall(r'\bGL[A-Za-z0-9]{1,9}\b', s, re.IGNORECASE)
    tl_matches: list[str] = re.findall(r'\bTL[A-Za-z0-9]{1,9}\b', s, re.IGNORECASE)
    gl_codes = {item.upper() for item in gl_matches if item.upper() not in GL_BLACKLIST}
    tl_codes = {item.upper() for item in tl_matches if item.upper() not in TL_BLACKLIST}

    return gl_codes, tl_codes

g_obj = pycaching.login(GEOCACHING_USERNAME, GEOCACHING_PASSWORD)

async def get_gt_code_info(gt_codes: Iterable[str]):
    messages = []

    for code in list(gt_codes)[:3]:
        try:
            gt = g_obj.get_geotour(code)
            name = gt['name']
            fp_count = gt['fp_count']
            location_name = gt['location_name']
            messages.append(f"<:geotour:1457794800714514707> {name} | 🩵 {fp_count} |📍 {location_name}")
        except Exception as e:
            messages.append(f"<:DNF:1368989100220092516> **That GeoTour doesn't exist!**")

    return "\n".join(messages)  

async def get_gl_tl_code_info(gl_codes: Iterable[str], tl_codes: Iterable[str]):
    messages = []

    for code, code_type in [(c, "GL") for c in list(gl_codes)[:3]] + [(c, "TL") for c in list(tl_codes)[:3]]:
        try:
            log = g_obj.get_log(code)

            author = log.author or "Unknown"
            logtype = log.type.name if log.type else "Unknown"
            date = log.visited.strftime('%Y-%m-%d') if log.visited else "Unknown"
            text = log.text or "Unknown"

            if code_type == "GL":
                display_code = log.geocache_code
            else:
                display_code = log.trackable_code

            # Map log type to emoji
            logtype_map = {
                "discovered_it": "<:TBDiscover:1369015617176207421>",
                "announcement": "📢",
                "archive": "<:Archive:1369015619231420497>",
                "attended": "<:Attended:1369015554257719334>",
                "didnt_find_it": "<:DNF:1368989100220092516>",
                "enable_listing": "<:Enabled:1369010377815494708>",
                "found_it": "<:Found:1368989281909215302>",
                "grabbed_it": "<:TBGrab:1369015569151430687>",
                "marked_missing": "<:TBMissing:1369015565171298335>",
                "needs_archive": "<:NeedsArchive:1369015557323755730>",
                "needs_maintenance": "<:NeedsMaintenence:1369010381774651504>",
                "note": "<:WriteNote:1369010379815911565>",
                "oc_team_comment": "💬",
                "owner_maintenance": "<:OwnerMaintenence:1369010374631751832>",
                "placed_it": "<:TBDrop:1369015563388584017>",
                "post_reviewer_note": "<:ReviewerNote:1369015567062667404>",
                "publish_listing": "<:Upload:1369010376662056970>",
                "retract": "<:ReviewerDeny:1369015615561666560>",
                "retrieved_it": "<:TBRetrieve:1369015561660399620>",
                "submit_for_review": "<:ReviewerNote:1369015567062667404>",
                "temp_disable_listing": "<:Disabled:1369009017552371902>",
                "unarchive": "<:Unarchive:1369015555570270409>",
                "update_coordinates": "<:Relocate:1369015572183908462>",
                "visit": "<:TBVisit:1369016734161309706>",
                "webcam_photo_taken": "<:LogImage:1369015560662417500>",
                "will_attend": "<:WillAttend:1369015558909071411>"
            }

            logtype_display = logtype_map.get(logtype, logtype)

            messages.append(
                f"[{code}](<https://coord.info/{code}>) - {logtype_display} | {author}\n"
                f"🗓️ {date} | {display_code}\n"
                f"Log Contents: {redact_discord_invites(text)}"
            )

        except Exception as e:
            return

    return "\n\n".join(messages)

async def get_pr_code_info(pr_codes: Iterable[str], bot):
    messages = []
    for code in list(pr_codes)[:3]:
        try:
            try:
                profile = g_obj.get_user(pr_code=code)
            except AttributeError as e:
                g_obj.logout()
                g_obj.login(GEOCACHING_USERNAME, GEOCACHING_PASSWORD)
                profile = g_obj.get_user(pr_code=code) 
            except Exception as e:
                raise e

            name = profile.name
            joined_date = profile.joined_date
            location = profile.location
            profile_picture_url = profile.profile_picture_url
            membership_status = profile.membership_status
            favorite_points_received = profile.favorite_points_received
            finds_count = profile.found_count
            hides_count = profile.hidden_count
            last_visited_date = profile.last_visited_date

            joined_ts = int(datetime.combine(joined_date, time.min).timestamp())
            last_visited_ts = int(datetime.combine(last_visited_date, time.min).timestamp())

            emoji_guild = bot.get_guild(int(os.getenv("EMOJI_GUILD_ID")) if os.getenv("EMOJI_GUILD_ID") else None)
            emoji = None
            if emoji_guild:
                emoji2 = await emoji_guild.create_custom_emoji(name=f"PR_{name}", image=requests.get(profile_picture_url).content)
                emoji = await emoji_guild.fetch_emoji(emoji2.id)

            pmo = "<:Premium:1368989525405335552>" if str(membership_status) == "MembershipStatus.premium" else ""
            emoji_str = f"<:{emoji.name}:{emoji.id}>" if emoji else f"👤"

            finalmessage = f"""<:user:1453018988362731601> {code} | {pmo} {emoji_str} [{name}](<https://geocaching.com/p/?u={name}>)
<:join:1453020390803898438> <t:{joined_ts}:R> | 🛂 <t:{last_visited_ts}:R>
📍 {location} | <:Found:1368989281909215302> {finds_count} | <:OwnedCache:1368989502281875536> {hides_count} | 🩵 {favorite_points_received}"""
            
            if emoji:
                async def delete_emoji_later():
                    await asyncio.sleep(60)
                    try:
                        await emoji.delete()
                    except:
                        pass 
                asyncio.create_task(delete_emoji_later())

            messages.append(finalmessage)

        except Exception as e:
            return
    
    return "\n\n".join(messages)

def get_cache_basic_info(guild_id: int, geocache_codes: Iterable[str]=[], tb_codes: Iterable[str]=[]):
    deadcode = False
    global g_obj
    final_message = []
    for code in list(geocache_codes)[:3]:
        try:
            try:
                cache = g_obj.get_cache(code)
                cache.load_quick()
            except AttributeError as e:
                g_obj.logout()
                g_obj.login(GEOCACHING_USERNAME, GEOCACHING_PASSWORD)

                cache = g_obj.get_cache(code)
                cache.load_quick()
            except Exception as e:
                raise e

            name = cache.name
            size = cache.size
            fps = cache.favorites
            difficulty = cache.difficulty
            terrain = cache.terrain
            author = cache.author
            pmo = cache.pm_only
            cache_type = cache.type
            status = cache.status

            if status == 0:
                prefix = ""
            elif status == 1:
                prefix = "<:Disabled:1369009017552371902>"
            elif status == 2:
                prefix = "<:Archive:1369015619231420497>"
            elif status == 3:
                raise Exception(f"found an unpublished cache: {code}")
            elif status == 4:
                prefix = ":lock:"

            emoji_name = f"{cache_type.name if cache_type.name != 'lost_and_found_event' else 'community_celebration'}"
            emoji_text = f"{prefix}{get_emoji_from_name(emoji_name)}"

            final_message.append(f"""{'<:Premium:1368989525405335552>' if pmo else ''}{emoji_text} [{code}](<https://coord.info/{code}>) - {name} | {author}
:light_blue_heart: {fps} | :mag_right: D{difficulty} - T{terrain} :mountain_snow: | <:tub:1327698135710957609> {size.value.capitalize()}""")

        except Exception as e:
            if guild_id == 0:
                final_message.append(f"<:DNF:1368989100220092516> **That Geocache doesn't exist!**")
            else:
                gsettings = get_guild_settings(guild_id)
                if gsettings.deadcode == 1:
                    final_message.append(f"<:DNF:1368989100220092516> **That Geocache doesn't exist!**")
                else:
                    deadcode = True
                    return final_message, deadcode

    for trackable in list(tb_codes)[:3]:
        try:
            tb = g_obj.get_trackable(trackable)
            tb.load()

            name = tb.name
            owner = tb.owner

            final_message.append(
                f"""<:TravelBug:1368989710818480169> [{trackable}](<https://coord.info/{trackable}>) - {name} | {owner}"""
            )

        except Exception as e:
            if guild_id == 0:
                final_message.append(f"<:DNF:1368989100220092516> **That Trackable doesn't exist!**")
            else:
                gsettings = get_guild_settings(guild_id)
                if gsettings.deadcode == 1:
                    final_message.append(f"<:DNF:1368989100220092516> **That Trackable doesn't exist!**")
                else:
                    deadcode = True
                    return final_message, deadcode

    if len(geocache_codes) - 3 > 0:
        final_message.append(f"**(... {len(geocache_codes) - 3} truncated)**")
    if len(tb_codes) - 3 > 0:
        final_message.append(f"**(... {len(tb_codes) - 3} truncated)**")
    final_message = "\n".join(final_message)
    return final_message, deadcode

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

REMINDER_FILE = DATA_DIR / "reminded_users.json"
def load_reminded_users():
    if REMINDER_FILE.exists():
        with open(REMINDER_FILE, "r") as f:
            data = json.load(f)
            return {int(k): datetime.fromisoformat(v) for k, v in data.items()}
    return {}

def save_reminded_users(cache):
    with open(REMINDER_FILE, "w") as f:
        json.dump({str(k): v.isoformat() for k, v in cache.items()}, f, indent=2)

def get_command_counts(bot):
    pc = {c.qualified_name for c in bot.commands}
    sc = set()

    def collect(cmds):
        for c in cmds:
            sc.add(c.qualified_name)
            if hasattr(c, "commands"):
                collect(c.commands)

    collect(bot.tree.get_commands())
    return len(pc | sc), len(pc), len(sc)


class FullModal(discord.ui.Modal, title="Suggest or Report"):
    def __init__(self, bot, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction
        self.bot = bot
    select_label = discord.ui.Label(
        text="Pick an option",
        component=discord.ui.Select(
            placeholder="Bug Report or Feature Suggestion",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Suggest a Feature"),
                discord.SelectOption(label="Report a Bug"),
            ],
            required=True
        ),
        description="Select an option to proceed"
    )

    text_input_label = discord.ui.Label(
        text="Your Report/Suggestion",
        component=discord.ui.TextInput(
            style=discord.TextStyle.short,
            placeholder="Type something here...",
            required=True
        ),
        description="This is your suggestion or bug report content"
    )

    async def on_submit(self, modal_interaction: discord.Interaction):
        select_value = self.select_label.component.values[0]
        text_value = self.text_input_label.component.value
        msg = "suggestion" if select_value == "Suggest a Feature" else "bug report"
        msg2 = "Suggestion" if select_value == "Suggest a Feature" else "Bug Report"
        await modal_interaction.response.send_message(
            f"Thank you for your {msg}! The Dev will review it ASAP.", ephemeral=True
        )
        embed = discord.Embed(title=f"New {msg}!",
                description=f"User: {self.interaction.user.mention}\nType: {msg2}\nContent: {text_value}",
                colour=0xad7e66)
        await self.bot.get_channel(int(os.getenv('SUGGEST_REPORT_CHANNEL_ID'))).send(f"<@{os.getenv('DEV_USER_ID')}> New Suggestion/Bug Report!", embed=embed)