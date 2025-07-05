import discord
from datetime import datetime, timedelta, timezone
from discord import app_commands
from functions import *
from votefunctions import *
from discord.ext import commands

class VoteChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def vote(self, interaction: discord.Interaction):
        """Sends vote info."""
        topgg_vote_streak = await get_type_streak(interaction.user.id, "topgg")
        dbl_vote_streak = await get_type_streak(interaction.user.id, "dbl")
        total_votes = await get_total(interaction.user.id)
        embed = discord.Embed(title="Vote Info",
                      colour=0xad7e66)

        # top.gg Cooldown Check
        topgg_last_vote = await get_last_type_vote(interaction.user.id, "topgg")
        if not isinstance(topgg_last_vote, datetime):
            topgg_last_vote = datetime.fromisoformat(str(topgg_last_vote))

        if is_12h_or_more_ago(topgg_last_vote):
            topgg_can_vote = True
            topgg_cannot_vote = False
            topgg_can_vote_timestamp = "Now"
        else:
            topgg_can_vote = False
            topgg_cannot_vote = True
            topgg_can_vote_unix = (topgg_last_vote + timedelta(hours=12)).timestamp()
            topgg_can_vote_timestamp = "<t:"+str(int(topgg_can_vote_unix))+":R>"

        if topgg_can_vote:
            embed.add_field(name="top.gg:",
                    value=f"You can vote!\n[Link: ***CLICK***](<https://top.gg/bot/1322305662973116486/vote>)\nVote Streak: {topgg_vote_streak}",
                    inline=True)
        if topgg_cannot_vote:
            embed.add_field(name="top.gg:",
                    value=f"You can't vote!\nExpires {topgg_can_vote_timestamp}\n[Link: ***CLICK***](<https://top.gg/bot/1322305662973116486/vote>)\nVote Streak: {topgg_vote_streak}",
                    inline=True)
            
        # DBL Cooldown Check
        dbl_last_vote = await get_last_type_vote(interaction.user.id, "dbl")
        if not isinstance(dbl_last_vote, datetime):
            dbl_last_vote = datetime.fromisoformat(str(dbl_last_vote))

        if is_12h_or_more_ago(dbl_last_vote):
            dbl_can_vote = True
            dbl_cannot_vote = False
            dbl_can_vote_timestamp = "Now"
        else:
            dbl_can_vote = False
            dbl_cannot_vote = True
            dbl_can_vote_unix = (dbl_last_vote + timedelta(hours=12)).timestamp()
            dbl_can_vote_timestamp = "<t:"+str(int(dbl_can_vote_unix))+":R>"

        if dbl_can_vote:
            embed.add_field(name="DBL:",
                                value=f"You can vote!\n[Link: ***CLICK***](<https://discordbotlist.com/bots/tracker/upvote>)\nVote Streak: {dbl_vote_streak}",
                                inline=True)
        if dbl_cannot_vote:
            embed.add_field(name="DBL:",
                            value=f"You can't vote!\nExpires {dbl_can_vote_timestamp}\n[Link: ***CLICK***](<https://discordbotlist.com/bots/tracker/upvote>)\nVote Streak: {dbl_vote_streak}",
                            inline=True)

        embed.add_field(name="Stats:",
                        value=f"Your Total Votes: {total_votes}\nTotal Vote Crates Earned: {await get_rewardtotal(interaction.user.id)}",
                        inline=False)
        await interaction.response.send_message(embed=embed)  

async def setup(bot):
    await bot.add_cog(VoteChecker(bot))