from dotenv import load_dotenv
load_dotenv(verbose=True, override=True)

from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = CODE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

import os
import discord

BOT_PREFIX = os.getenv("BOT_PREFIX")

GEOCACHING_USERNAME = os.getenv("GEOCACHING_USERNAME")
GEOCACHING_PASSWORD = os.getenv("GEOCACHING_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CX_ID = os.getenv('GOOGLE_SEARCH_ID')
GOOGLE_NORMAL_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
GOOGLE_NORMAL_SEARCH_ID = os.getenv("GOOGLE_SEARCH_NORMAL_ID")

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

GC_LINK_SEARCH = r"https?://(www\.)?(geocaching\.com|coord\.info)"