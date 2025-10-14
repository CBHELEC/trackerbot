import discord
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path
from datetime import datetime, timedelta, timezone

DATABASE_URL = f"sqlite:///{Path(__file__).parent.resolve() / 'data' / 'locationprofile.db'}"

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

class UserProfile(Base):
    __tablename__ = "userprofile"
    user_id = Column(String, primary_key=True)
    country = Column(String)
    timezone = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_user_profile(user_id: str):
    with SessionLocal() as session:
        return session.get(UserProfile, user_id)

def update_user_profile(user_id: str, country: str, timezone: int):
    with SessionLocal() as session:
        profile = session.get(UserProfile, user_id)

        if profile:
            profile.country = country
            profile.timezone = timezone
        else:
            profile = UserProfile(user_id=user_id, country=country, timezone=timezone)
            session.add(profile)

        session.commit()
        return profile.country, profile.timezone
    
class CreateButton(discord.ui.View):
    def __init__(self, bot, interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.bot = bot
        self.interaction = interaction

    @discord.ui.button(label="Create Location Profile", style=discord.ButtonStyle.primary)
    async def create_profile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CreateProfile(self.bot, self.interaction)
        await interaction.response.send_modal(modal)

class CreateProfile(discord.ui.Modal, title="Create a Location Profile"):
    def __init__(self, bot, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction
        self.bot = bot

    country_input_label = discord.ui.Label(
        text="Enter Country",
        component=discord.ui.TextInput(
            style=discord.TextStyle.short,
            placeholder="eg. United States",
            required=True
        ),
        description="This is your country"
    )
    timezone_input_label = discord.ui.Label(
        text="Enter Timezone",
        component=discord.ui.TextInput(
            style=discord.TextStyle.short,
            placeholder="eg. GMT+1",
            required=True
        ),
        description="This is your timezone"
    )

    async def on_submit(self, modal_interaction: discord.Interaction):
        country = self.country_input_label.component.value
        timezone = self.timezone_input_label.component.value
        await modal_interaction.response.send_message(
            f"Location Profile Created! Country: {country}, Timezone: {timezone}", ephemeral=True
        )
        update_user_profile(str(self.interaction.user.id), country, timezone)

def time_in_tz(tz_string: str) -> datetime | None:
    if tz_string.startswith("GMT") and len(tz_string) > 3:
        try:
            offset_hours = int(tz_string[3:])
            return datetime.now(timezone(timedelta(hours=offset_hours)))
        except ValueError:
            return None
    return None