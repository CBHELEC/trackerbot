import aiofiles
import datetime
from pathlib import Path

LOG_FILE_PATH = Path("logs/bot.log")
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

async def log(interaction, log: str):
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    full_message = f"[{timestamp}] | GUILD: {interaction.guild.id} | USER: {interaction.user.id} | {log}\n"
    async with aiofiles.open(LOG_FILE_PATH, mode='a') as f:
        await f.write(full_message)