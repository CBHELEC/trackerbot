from dotenv import load_dotenv
load_dotenv(verbose=True, override=True)

import random
import os
import discord
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, BigInteger, Integer, String, select
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

VOTE_LOG_ID = 1391169156530962553

# Database Path
DATABASE_URL = f"sqlite:///{Path(__file__).parent.resolve() / 'data' / 'votes.db'}"

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class topgg_votes(Base):
    __tablename__ = "topgg_votes"

    user_id = Column(BigInteger, primary_key=True)
    voted_at = Column(String, nullable=False)  
    streak = Column(BigInteger, default=0)  
    total_votes = Column(BigInteger, default=0) 

class dbl_votes(Base):
    __tablename__ = "dbl_votes"

    user_id = Column(BigInteger, primary_key=True)
    voted_at = Column(String, nullable=False)
    streak = Column(BigInteger, default=0)  
    total_votes = Column(BigInteger, default=0) 

class rewards(Base):
    __tablename__ = "rewards"

    user_id = Column(BigInteger, primary_key=True)
    topgg_reward_amount = Column(Integer, nullable=False, default=0)
    dbl_reward_amount = Column(Integer, nullable=False, default=0)
    last_streak_bonus = Column(Integer, default=0, nullable=False)

class reminders(Base):
    __tablename__ = "reminders"

    user_id = Column(BigInteger, primary_key=True)
    topgg_reminded = Column(Integer, default=0, nullable=False)
    dbl_reminded = Column(Integer, default=0, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)

async def get_type_total(user_id, type: str):
    if type == "topgg":
        with Session() as session:
            vote = session.query(topgg_votes).filter_by(user_id=user_id).first()
            if vote:
                return vote.total_votes
            else:
                return 0
    elif type == "dbl":
        with Session() as session:
            vote = session.query(dbl_votes).filter_by(user_id=user_id).first()
            if vote:
                return vote.total_votes
            else:
                return 0

async def get_total(user_id):
    topgg_total = await get_type_total(user_id, "topgg")
    dbl_total = await get_type_total(user_id, "dbl")
    return topgg_total + dbl_total

async def get_last_type_vote(user_id, type: str):
    if type == "topgg":
        with Session() as session:
            vote = session.query(topgg_votes).filter_by(user_id=user_id).first()
            if vote:
                return vote.voted_at
            else:
                return None
    elif type == "dbl":
        with Session() as session:
            vote = session.query(dbl_votes).filter_by(user_id=user_id).first()
            if vote:
                return vote.voted_at
            else:
                return None
    
async def get_last_vote(user_id):
    topgg_last = await get_last_type_vote(user_id, "topgg")
    dbl_last = await get_last_type_vote(user_id, "dbl")
    
    if topgg_last and dbl_last:
        return max(topgg_last, dbl_last)
    elif topgg_last:
        return topgg_last
    elif dbl_last:
        return dbl_last
    else:
        return None
    
async def get_type_streak(user_id, type: str):
    if type == "topgg":
        with Session() as session:
            vote = session.query(topgg_votes).filter_by(user_id=user_id).first()
            if vote:
                return vote.streak
            else:
                return 0
    elif type == "dbl":
        with Session() as session:
            vote = session.query(dbl_votes).filter_by(user_id=user_id).first()
            if vote:
                return vote.streak
            else:
                return 0
            
async def get_streak(user_id):
    topgg_streak = await get_type_streak(user_id, "topgg")
    dbl_streak = await get_type_streak(user_id, "dbl")
    
    return topgg_streak + dbl_streak

async def get_type_rewardtotal(user_id, type: str):
    with Session() as session:
        if type == "topgg":
            reward = session.query(rewards).filter_by(user_id=user_id).first()
            if reward:
                return reward.topgg_reward_amount
            else:
                return 0
        elif type == "dbl":
            reward = session.query(rewards).filter_by(user_id=user_id).first()
            if reward:
                return reward.dbl_reward_amount
            else:
                return 0
            
async def get_rewardtotal(user_id):
    topgg_reward = await get_type_rewardtotal(user_id, "topgg")
    dbl_reward = await get_type_rewardtotal(user_id, "dbl")
    
    return topgg_reward + dbl_reward

async def get_last_streak_bonus(user_id):
    with Session() as session:
        reward = session.query(rewards).filter_by(user_id=user_id).first()
        if reward:
            return reward.last_streak_bonus
        else:
            return 0
        
async def update_type_total(user_id, type: str):
    with Session() as session:
        if type == "topgg":
            vote = session.query(topgg_votes).filter_by(user_id=user_id).first()
            if vote:
                vote.total_votes += 1
            else:
                vote = topgg_votes(user_id=user_id, voted_at=datetime.now().isoformat(), total_votes=1)
                session.add(vote)
        elif type == "dbl":
            vote = session.query(dbl_votes).filter_by(user_id=user_id).first()
            if vote:
                vote.total_votes += 1
            else:
                vote = dbl_votes(user_id=user_id, voted_at=datetime.now().isoformat(), total_votes=1)
                session.add(vote)
        session.commit()

async def update_last_type_vote(user_id, type: str):
    with Session() as session:
        if type == "topgg":
            vote = session.query(topgg_votes).filter_by(user_id=user_id).first()
            if vote:
                vote.voted_at = datetime.now().isoformat()
            else:
                vote = topgg_votes(user_id=user_id, voted_at=datetime.now().isoformat())
                session.add(vote)
        elif type == "dbl":
            vote = session.query(dbl_votes).filter_by(user_id=user_id).first()
            if vote:
                vote.voted_at = datetime.now().isoformat()
            else:
                vote = dbl_votes(user_id=user_id, voted_at=datetime.now().isoformat())
                session.add(vote)
        session.commit()

async def update_type_streak(user_id, type: str):
    with Session() as session:
        if type == "topgg":
            vote = session.query(topgg_votes).filter_by(user_id=user_id).first()
            if vote:
                vote.streak += 1
            else:
                vote = topgg_votes(user_id=user_id, voted_at=datetime.now().isoformat(), streak=1)
                session.add(vote)
        elif type == "dbl":
            vote = session.query(dbl_votes).filter_by(user_id=user_id).first()
            if vote:
                vote.streak += 1
            else:
                vote = dbl_votes(user_id=user_id, voted_at=datetime.now().isoformat(), streak=1)
                session.add(vote)
        session.commit()

async def update_type_rewardtotal(user_id, type: str, amount: int):
    with Session() as session:
        if type == "topgg":
            reward = session.query(rewards).filter_by(user_id=user_id).first()
            if reward:
                reward.topgg_reward_amount += amount
            else:
                reward = rewards(user_id=user_id, topgg_reward_amount=amount)
                session.add(reward)
        elif type == "dbl":
            reward = session.query(rewards).filter_by(user_id=user_id).first()
            if reward:
                reward.dbl_reward_amount += amount
            else:
                reward = rewards(user_id=user_id, dbl_reward_amount=amount)
                session.add(reward)
        session.commit()

async def update_last_streak_bonus(user_id, amount: int):
    with Session() as session:
        reward = session.query(rewards).filter_by(user_id=user_id).first()
        if reward:
            reward.last_streak_bonus = amount
        else:
            reward = rewards(user_id=user_id, last_streak_bonus=amount)
            session.add(reward)
        session.commit()

async def toggle_reminded(user_id, type: str):
    with Session() as session:
        reminder = session.query(reminders).filter_by(user_id=user_id).first()
        if not reminder:
            reminder = reminders(user_id=user_id)
            session.add(reminder)

        if type == "topgg":
            if reminder.topgg_reminded == 0:
                reminder.topgg_reminded = 1
            else:
                reminder.topgg_reminded = 0
        elif type == "dbl":
            if reminder.dbl_reminded == 0:
                reminder.dbl_reminded = 1
            else:
                reminder.dbl_reminded = 0
        session.commit()

async def is_type_reminded(user_id, type: str):
    with Session() as session:
        reminder = session.query(reminders).filter_by(user_id=user_id).first()
        if not reminder:
            return False

        if type == "topgg":
            return reminder.topgg_reminded
        elif type == "dbl":
            return reminder.dbl_reminded
        else:
            return False

async def notify_vote(user_id, type: str, bot):
    milestoneembed = None
    if type == "topgg":
        reward_amount = random.randint(2, 5)
        await update_type_streak(user_id, "topgg")
        await update_type_total(user_id, "topgg")
        await update_last_type_vote(user_id, "topgg")
        await update_type_rewardtotal(user_id, "topgg", reward_amount)
        topgg_type_streak = await get_type_streak(user_id, "topgg")
        new_streak_update = False
        if topgg_type_streak in [10, 25, 50, 75, 100, 150, 250, 500, 1000]:
            if topgg_type_streak == 10:
                topgg_streak_amount = 10
                bonus_reward_amount = 5
            elif topgg_type_streak == 25:
                topgg_streak_amount = 25
                bonus_reward_amount = 10
            elif topgg_type_streak == 50:
                topgg_streak_amount = 50
                bonus_reward_amount = 25
            elif topgg_type_streak == 75:
                topgg_streak_amount = 75
                bonus_reward_amount = 45
            elif topgg_type_streak == 100:
                topgg_streak_amount = 100
                bonus_reward_amount = 50
            elif topgg_type_streak == 150:
                topgg_streak_amount = 150
                bonus_reward_amount = 75
            elif topgg_type_streak == 250:
                topgg_streak_amount = 250
                bonus_reward_amount = 100
            elif topgg_type_streak == 500:
                topgg_streak_amount = 500
                bonus_reward_amount = 150
            elif topgg_type_streak == 1000:
                topgg_streak_amount = 1000
                bonus_reward_amount = 250
            else:
                print("Oh Noes! We appear to have someone that has a funky wunky streak uwu! User_ID:" + str(user_id))
            await update_last_streak_bonus(user_id, topgg_streak_amount)
            await update_type_rewardtotal(user_id, "topgg", bonus_reward_amount)
            new_streak_update = True
        user = bot.get_user(user_id)
        if user:
            embed = discord.Embed(
                title="Thank you for voting on top.gg! 🎉",
                description=f"You voting helps a lot, so take {reward_amount} Vote Crates as your reward!\nThanks! <3",
                colour=0xad7e66
            )
            embed.set_footer(text=f"Vote Streak: {topgg_type_streak} | /vote for more info")
            if new_streak_update:
                milestoneembed = discord.Embed(
                    title="Oh?",
                    description=f"It appears you have reached a total of {topgg_type_streak} total top.gg votes!\nTo reward that, you have been given an additional {bonus_reward_amount} Vote Crates.\nThank you for the support and happy voting!",
                    colour=0xad7e66
                )
            try:
                embeds_to_send = [embed]
                if milestoneembed is not None:
                    embeds_to_send.append(milestoneembed)

                await user.send(embeds=embeds_to_send)
                await toggle_reminded(user_id, "topgg")
                await bot.get_channel(VOTE_LOG_ID).send(f"<@{user_id}> just voted on top.gg!")
            except discord.Forbidden:
                print(f"Discord User ID {user_id} has DMs disabled, so I was unable to notify them of their vote.")
                return
    elif type == "dbl":
        reward_amount = random.randint(2, 5)
        await update_type_streak(user_id, "dbl")
        await update_type_total(user_id, "dbl")
        await update_last_type_vote(user_id, "dbl")
        await update_type_rewardtotal(user_id, "dbl", reward_amount)
        dbl_type_streak = await get_type_streak(user_id, "dbl")
        new_streak_update = False
        if dbl_type_streak in [10, 25, 50, 75, 100, 150, 250, 500, 1000]:
            if dbl_type_streak == 10:
                dbl_streak_amount = 10
                bonus_reward_amount = 5
            elif dbl_type_streak == 25:
                dbl_streak_amount = 25
                bonus_reward_amount = 10
            elif dbl_type_streak == 50:
                dbl_streak_amount = 50
                bonus_reward_amount = 25
            elif dbl_type_streak == 75:
                dbl_streak_amount = 75
                bonus_reward_amount = 45
            elif dbl_type_streak == 100:
                dbl_streak_amount = 100
                bonus_reward_amount = 50
            elif dbl_type_streak == 150:
                dbl_streak_amount = 150
                bonus_reward_amount = 75
            elif dbl_type_streak == 250:
                dbl_streak_amount = 250
                bonus_reward_amount = 100
            elif dbl_type_streak == 500:
                dbl_streak_amount = 500
                bonus_reward_amount = 150
            elif dbl_type_streak == 1000:
                dbl_streak_amount = 1000
                bonus_reward_amount = 250
            else:
                print("Oh Noes! We appear to have someone that has a funky wunky streak uwu! User_ID:" + str(user_id))
            await update_last_streak_bonus(user_id, dbl_streak_amount)
            await update_type_rewardtotal(user_id, "dbl", bonus_reward_amount)
        user = bot.get_user(user_id)
        if user:
            embed = discord.Embed(
                title="Thank you for voting on DBL! 🎉",
                description=f"You voting helps a lot, so take {reward_amount} Vote Crates as your reward!\nThanks! <3",
                colour=0xad7e66
            )
            embed.set_footer(text=f"Vote Streak: {dbl_type_streak} | /vote for more info")
            if new_streak_update:
                milestoneembed = discord.Embed(
                    title="Oh?",
                    description=f"It appears you have reached a total of {dbl_type_streak} total DBL votes!\nTo reward that, you have been given an additional {bonus_reward_amount} Vote Crates.\nThank you for the support and happy voting!",
                    colour=0xad7e66
                )
            try:
                embeds_to_send = [embed]
                if milestoneembed is not None:
                    embeds_to_send.append(milestoneembed)

                await user.send(embeds=embeds_to_send)
                await toggle_reminded(user_id, "dbl")
                await bot.get_channel(VOTE_LOG_ID).send(f"<@{user_id}> just voted on DBL!")
            except discord.Forbidden:
                print(f"Discord User ID {user_id} has DMs disabled, so I was unable to notify them of their vote.")
                return
        else:
            print("no.")
            
async def send_vote_reminders(bot):
    with Session() as session:
        with session.begin():
            topgg_users = session.execute(
                select(topgg_votes.user_id).distinct()
            )
            topgg_user_ids = set(row[0] for row in topgg_users.all())

            dbl_users = session.execute(
                select(dbl_votes.user_id).distinct()
            )
            dbl_user_ids = set(row[0] for row in dbl_users.all())

            all_user_ids = topgg_user_ids.union(dbl_user_ids)
            now = datetime.now()

            for user_id in all_user_ids:
                user = bot.get_user(user_id)
                if not user:
                    continue

                result_topgg = session.execute(
                    select(topgg_votes)
                    .where(topgg_votes.user_id == user_id)
                    .order_by(topgg_votes.voted_at.desc())
                    .limit(1)
                )
                topgg_vote = result_topgg.scalar_one_or_none()
                topgg_time = topgg_vote.voted_at if topgg_vote else None
                result_dbl = session.execute(
                    select(dbl_votes)
                    .where(dbl_votes.user_id == user_id)
                    .order_by(dbl_votes.voted_at.desc())
                    .limit(1)
                )
                dbl_vote = result_dbl.scalar_one_or_none()
                dbl_time = dbl_vote.voted_at if dbl_vote else None

                if topgg_time:
                    if await is_type_reminded(user_id, "topgg"):
                        return
                    hours_since_topgg = (now - datetime.fromisoformat(topgg_time)).total_seconds() / 3600
                    if hours_since_topgg >= 12:
                        try:
                            embed = discord.Embed(title="Reminder to Vote! ⏰",
                                description="I noticed you can vote on top.gg again, and it would be a shame to watch that streak disappear. Vote @ https://top.gg/bot/1322305662973116486/vote",
                                colour=0xad7e66)
                            await user.send(embed=embed)
                            await toggle_reminded(user_id, "topgg")
                        except discord.Forbidden:
                            pass

                if dbl_time:
                    if await is_type_reminded(user_id, "dbl"):
                        return
                    hours_since_dbl = (now - datetime.fromisoformat(dbl_time)).total_seconds() / 3600
                    if hours_since_dbl >= 12:
                        try:
                            embed = discord.Embed(title="Reminder to Vote! ⏰",
                                description="I noticed you can vote on DBL again, and it would be a shame to watch that streak disappear. Vote @ https://discordbotlist.com/bots/tracker/upvote",
                                colour=0xad7e66)
                            await user.send(embed=embed)
                            await toggle_reminded(user_id, "dbl")
                        except discord.Forbidden:
                            pass

def is_12h_or_more_ago(timestamp: datetime) -> bool:
    return datetime.now() - timestamp >= timedelta(hours=12)