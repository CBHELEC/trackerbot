import discord
import random
import os
from discord.ext import tasks, commands
import aiohttp
import sqlite3
from datetime import datetime, timedelta
from economy import *

class VoteChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn2 = sqlite3.connect('votes.db')
        self.c = self.conn2.cursor()
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                user_id TEXT PRIMARY KEY,
                voted_at TEXT
            )
        ''')
        self.conn2.commit()

    #    self.DBL_API_TOKEN = os.getenv("DBL_TOKEN")
    #    self.BOT_ID = os.getenv("DBL_ID")

        self.DBL_API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoxLCJpZCI6IjEzMjIzMDU2NjI5NzMxMTY0ODYiLCJpYXQiOjE3NDU2OTQ1Mzd9.crs7nNF3pyTLh4aPAsqXB706tvaMOAPh-Xi2ra0Yqq4"
        self.BOT_ID = "1322305662973116486"

    @tasks.loop(minutes=1)
    async def check_votes(self):
        if not self.DBL_API_TOKEN:
            print("Error: DBL_TOKEN not found. Please check your .env file.")
            return

        url = f"https://discordbotlist.com/api/v1/bots/{self.BOT_ID}/upvotes"
        headers = {
            "Authorization": self.DBL_API_TOKEN
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        print(f"Failed to fetch votes: {response.status}")
                        return
                    data = await response.json()

            votes = data.get('upvotes', [])

            new_votes = 0
            for user in votes:
                user_id = user.get('user_id')
                voted_at = user.get('timestamp')

                if not user_id or not voted_at:
                    continue

                self.c.execute('SELECT 1 FROM votes WHERE user_id = ?', (user_id,))
                if self.c.fetchone():
                    continue  

                self.c.execute('INSERT INTO votes (user_id, voted_at) VALUES (?, ?)', (user_id, voted_at))
                new_votes += 1

                try:
                    discord_user = await self.bot.fetch_user(int(user_id))
                    if discord_user:
                        amount = random.randint(10, 35)
                        embed = discord.Embed(
                            title="Thank you for voting! 🎉",
                            description=f"You voting helps a lot, so take {amount} G$ as your reward!\nThanks! <3",
                            colour=0xad7e66
                        )
                        async with Session() as session:
                            balance = await get_balance(session, user_id)
                            if balance == None:
                                await add_user_to_db(session, user_id)
                            balance = await get_balance(session, user_id)
                            new = balance + amount
                            await update_balance(session, user_id, new)
                        await discord_user.send(embed=embed)
                except Exception as e:
                    return

            self.conn2.commit()
        except Exception as e:
            return

    @tasks.loop(minutes=3)
    async def check_reminders(self):
        twelve_hours_ago = datetime.now() - timedelta(hours=12)

        self.c.execute('SELECT user_id, voted_at FROM votes')
        users = self.c.fetchall()

        reminder_count = 0
        for user_id, voted_at in users:
            voted_time = datetime.strptime(voted_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            if voted_time <= twelve_hours_ago:
                try:
                    discord_user = await self.bot.fetch_user(int(user_id))
                    if discord_user:
                        embed = discord.Embed(
                            title="Reminder to Vote! 🔔",
                            description="Heya... you can vote again! Vote @ https://discordbotlist.com/bots/tracker/upvote <:happy_tracker:1329914691656614042>",
                            colour=0xad7e66
                        )
                        await discord_user.send(embed=embed)
                        reminder_count += 1
                except Exception as e:
                    return

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_votes.is_running():
            self.check_votes.start()
            
        if not self.check_reminders.is_running():
            self.check_reminders.start()

async def setup(bot):
    await bot.add_cog(VoteChecker(bot))