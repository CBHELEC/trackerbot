import re
import discord
import random
import aiohttp
import sqlite3
from datetime import datetime, timedelta, timezone
from economy import *
from discord import app_commands
from functions import *
from discord.ext import tasks, commands

class VoteChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn2 = sqlite3.connect(f'{DATA_DIR}/votes.db')
        self.c = self.conn2.cursor()
        self.c.execute(''' 
            CREATE TABLE IF NOT EXISTS dbl_votes ( 
                user_id TEXT PRIMARY KEY, 
                voted_at TEXT, 
                vote_streak INTEGER DEFAULT 1, 
                reminded INTEGER DEFAULT 0,
                total_votes INTEGER DEFAULT 1
            ) 
        ''')
        self.conn2.commit()
        self.c.execute(''' 
            CREATE TABLE IF NOT EXISTS moneh ( 
                user_id TEXT PRIMARY KEY, 
                moneh INTEGER
            ) 
        ''')
        self.conn2.commit()

        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / ".env")
        self.DBL_API_TOKEN = os.getenv("DBL_TOKEN")
        self.BOT_ID = "1322305662973116486"

        self.reminded_users = load_reminded_users()

    @tasks.loop(minutes=0.75)
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

                self.c.execute('SELECT vote_streak, voted_at, reminded, total_votes FROM dbl_votes WHERE user_id = ?', (user_id,))
                row = self.c.fetchone()

                if row:
                    current_streak, last_voted_at, reminded, total_votes = row
                    if voted_at != last_voted_at:
                        new_streak = current_streak + 1
                        new_total = total_votes + 1
                        self.c.execute('UPDATE dbl_votes SET vote_streak = ?, voted_at = ?, total_votes = ? WHERE user_id = ?', (new_streak, voted_at, new_total, user_id))

                        if reminded == 1:
                            await self.send_vote_reward(user_id, new_streak, voted_at)
                            self.c.execute('UPDATE dbl_votes SET reminded = 0 WHERE user_id = ?', (user_id,))

                else:
                    self.c.execute('INSERT INTO dbl_votes (user_id, voted_at, vote_streak, total_votes) VALUES (?, ?, ?, ?)', (user_id, voted_at, 1, 1))
                    await self.send_vote_reward(user_id, 1, voted_at)

                new_votes += 1

            self.conn2.commit()

        except Exception as e:
            print(f"Error in checking votes: {e}")

    @tasks.loop(minutes=3)
    async def check_vote_reminders_dbl(self):
        now = datetime.utcnow()
        self.c.execute('SELECT user_id, voted_at, reminded FROM dbl_votes')
        users = self.c.fetchall()

        for user_id, voted_at_str, reminded in users:
            voted_at = datetime.fromisoformat(voted_at_str.replace('Z', ''))
            time_since_vote = now - voted_at

            if time_since_vote >= timedelta(hours=12) and reminded == 0:
                try:
                    discord_user = await self.bot.fetch_user(int(user_id))
                    if discord_user:
                        embed = discord.Embed(
                            title="Reminder to Vote! 🔔",
                            description="Heya... you can vote on DBL again! Vote @ https://discordbotlist.com/bots/tracker/upvote <:happy_tracker:1329914691656614042>",
                            colour=0xad7e66
                        )
                        await discord_user.send(embed=embed)

                        self.c.execute('UPDATE dbl_votes SET reminded = 1 WHERE user_id = ?', (user_id,))

                except Exception as e:
                    return

        self.conn2.commit()

    @tasks.loop(minutes=3)
    async def check_vote_reminders_tgg(self):
        channel_id = 1365079297919811725
        channel = self.bot.get_channel(channel_id)

        if not channel:
            print("Vote channel not found.")
            return

        now = datetime.now(timezone.utc)

        self.c.execute('SELECT user_id, reminded FROM topgg_votes')
        users = self.c.fetchall()

        for user_id, reminded in users:
            if reminded == 1:
                return
            else:
                user1 = await self.bot.fetch_user(int(user_id))
                channel_id = 1365079297919811725
                channel = self.bot.get_channel(channel_id) 
                
                if channel is None:
                    thetimething = None 

                async for message in channel.history(limit=None): 
                    if user1.mention in message.content:
                        thetimething = message.created_at

                time_since_vote = now - thetimething

                if time_since_vote >= timedelta(hours=12):
                    last_reminder = self.reminded_users.get(user_id)
                    if last_reminder and last_reminder >= thetimething:
                        continue 

                    try:
                        embed = discord.Embed(
                            title="Reminder to Vote! 🔔",
                            description="Heya... you can vote on top.gg again! Vote @ https://top.gg/bot/1322305662973116486/vote <:happy_tracker:1329914691656614042>",
                            colour=0xad7e66
                        )
                        await user1.send(embed=embed)
                        self.c.execute('UPDATE topgg_votes SET reminded = 1 WHERE user_id = ?', (user_id,))
                        self.conn2.commit()
                    except Exception as e:
                        print(f"Failed to DM user {user_id}: {e}")

    @tasks.loop(minutes=10)
    async def check_vote_streaks(self):
        now = datetime.now()
        self.c.execute('SELECT user_id, voted_at, vote_streak FROM dbl_votes')
        users = self.c.fetchall()

        for user_id, voted_at_str, vote_streak in users:
            voted_at = datetime.fromisoformat(voted_at_str.replace('Z', ''))
            time_since_vote = now - voted_at

            if time_since_vote >= timedelta(hours=24):
                if vote_streak != 1:
                    self.c.execute('UPDATE dbl_votes SET vote_streak = 1 WHERE user_id = ?', (user_id,))
                    print(f"Reset vote streak for user {user_id}")

        self.conn2.commit()

    async def send_vote_reward(self, user_id, new_streak, voted_at):
        try:
            discord_user = await self.bot.fetch_user(int(user_id))
            if discord_user:
               # amount = random.randint(10, 35)
                amount = random.randint(2, 5)
                embed = discord.Embed(
                    title="Thank you for voting on DBL! 🎉",
                    #description=f"You voting helps a lot, so take {amount} G$ as your reward!\nThanks! <3",
                    description=f"You voting helps a lot, so take {amount} Vote Crates as your reward!\nThanks! <3",
                    colour=0xad7e66,
                    timestamp=datetime.now()
                )
                embed.set_footer(text=f"Vote Streak: {new_streak}")

                async with Session() as session:
                    userinfo = await get_db_settings(session, user_id)
                    if userinfo is None:
                        await add_user_to_db(session, user_id)
                        userinfo1 = await get_db_settings(session, user_id)
                        balance = userinfo1.balance
                    else:
                        balance = userinfo.balance
                    new_balance = balance + amount
                    await update_balance(session, user_id, new_balance)
                    self.c.execute('SELECT moneh FROM moneh WHERE user_id = ?', (user_id,))
                    row1 = self.c.fetchone()
                    if row1:
                        moneh = row1[0]
                    else:
                        moneh = 0
                    new_moneh = moneh + amount
                    self.c.execute(
                        "INSERT INTO moneh (user_id, moneh) VALUES (?, ?) "
                        "ON CONFLICT(user_id) DO UPDATE SET moneh = excluded.moneh",
                        (str(user_id), new_moneh)
                    )
                    self.conn2.commit()

                await discord_user.send(embed=embed)
        except Exception as e:
            print(e)
            return

    @app_commands.command()
    async def vote(self, interaction: discord.Interaction):
        """Sends vote info."""
        self.c.execute('SELECT vote_streak, total_votes, voted_at FROM dbl_votes WHERE user_id = ?', (interaction.user.id,))
        row = self.c.fetchone()
        self.c.execute('SELECT moneh FROM moneh WHERE user_id = ?', (interaction.user.id,))
        row1 = self.c.fetchone()
        if row:
            vote_streak, total_votes, voted_at = row
        else:
            vote_streak = 0
            total_votes = 0
            voted_at = None
        if row1:
            moneh = row1[0]
        else:
            moneh = 0

        topggvotestreak = await get_current_vote_streak_topgg(interaction)
        if topggvotestreak == None:
            topggvotestreak = 0
        total_vote_total = total_votes + int(topggvotestreak)
        if vote_streak == None:
            vote_streak = 0
        embed = discord.Embed(title="Vote Info",
                      colour=0xad7e66)

        # top.gg Cooldown Check
        thisisavariable = await find_latest_topgg_vote(self.bot, interaction)

        if thisisavariable == None:
            embed.add_field(name="top.gg:",
                    value=f"You can vote!\n[Link: ***CLICK***](<https://top.gg/bot/1322305662973116486/vote>)\nVote Streak: {topggvotestreak}",
                    inline=True)
        else:
            variable_datetime = datetime.fromisoformat(str(thisisavariable))
            current_time = datetime.now(timezone.utc)

            if current_time - variable_datetime < timedelta(days=0.5):
                time_diff = current_time - variable_datetime
                hours_ago = int(time_diff.total_seconds() // 3600)
                
                next_vote_time = variable_datetime + timedelta(hours=12) 
                timestampthing = discord.utils.format_dt(next_vote_time, style="R")
                embed.add_field(name="top.gg:",
                        value=f"You can't vote!\nExpires {timestampthing}\n[Link: ***CLICK***](<https://top.gg/bot/1322305662973116486/vote>)\nVote Streak: {topggvotestreak}",
                        inline=True)
                
            else:
                embed.add_field(name="top.gg:",
                        value=f"You can vote!\n[Link: ***CLICK***](<https://top.gg/bot/1322305662973116486/vote>)\nVote Streak: {topggvotestreak}",
                        inline=True)
            
        # DBL Cooldown Check
        if voted_at is not None:
            voted_at = datetime.fromisoformat(str(voted_at).replace("Z", "+00:00")) 
            current_time = datetime.now(tz=discord.utils.utcnow().tzinfo)  
            time_diff = current_time - voted_at

        if voted_at is None:
            timestampthing = "Never Voted"
            embed.add_field(name="DBL:",
                                value=f"You can vote!\n[Link: ***CLICK***](<https://discordbotlist.com/bots/tracker/upvote>)\nVote Streak: {vote_streak}",
                                inline=True)
        else:
            if time_diff < timedelta(hours=12):
                timestampthing = discord.utils.format_dt(voted_at + timedelta(hours=12), style="R")

                embed.add_field(name="DBL:",
                                value=f"You can't vote!\nExpires {timestampthing}\n[Link: ***CLICK***](<https://discordbotlist.com/bots/tracker/upvote>)\nVote Streak: {vote_streak}",
                                inline=True)
            else:
                embed.add_field(name="DBL:",
                                value=f"You can vote!\n[Link: ***CLICK***](<https://discordbotlist.com/bots/tracker/upvote>)\nVote Streak: {vote_streak}",
                                inline=True)
        embed.add_field(name="Stats:",
                       # value=f"Your Total Votes: {total_vote_total}\nTotal Earned from Voting: G${moneh}",
                        value=f"Your Total Votes: {total_vote_total}\nTotal Vote Crates Earned: {moneh}",
                        inline=False)
        await interaction.response.send_message(embed=embed)  

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_votes.is_running():
            self.check_votes.start()

        if not self.check_vote_reminders_dbl.is_running():
            self.check_vote_reminders_dbl.start()

        if not self.check_vote_streaks.is_running():
            self.check_vote_streaks.start()

        if not self.check_vote_reminders_tgg.is_running():
            self.check_vote_reminders_tgg.start()

async def setup(bot):
    await bot.add_cog(VoteChecker(bot))