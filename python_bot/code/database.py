from sqlalchemy import create_engine, Column, BigInteger, Boolean, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Database Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'bot_settings.db')}"

Base = declarative_base()

class GuildSettings(Base):
    __tablename__ = "guild_settings"

    guild_id = Column(BigInteger, primary_key=True)
    mod_role_ids = Column(String, default="")  # Store multiple IDs as CSV
    perm_role_ids = Column(String, default="")  # Store multiple IDs as CSV
    log_channel_id = Column(BigInteger, nullable=True)
    skullboard_status = Column(Boolean, default=False)
    skullboard_channel_id = Column(BigInteger, nullable=True)
    detection_status = Column(Boolean, default="1")
    link_embed_status = Column(Boolean, default="1")

# Database setup
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_guild_settings(guild_id):
    """Fetch guild settings, create entry if missing."""
    with Session() as session:
        settings = session.query(GuildSettings).filter_by(guild_id=guild_id).first()
        if not settings:
            settings = GuildSettings(guild_id=guild_id)
            session.add(settings)
            session.commit()
        session.close()
        return settings

def update_guild_settings(guild_id, **kwargs):
    """Update guild settings dynamically."""
    with Session() as session:
        settings = session.query(GuildSettings).filter_by(guild_id=guild_id).first()
        if not settings:
            settings = GuildSettings(guild_id=guild_id, **kwargs)
            session.add(settings)
        else:
            for key, value in kwargs.items():
                setattr(settings, key, value)
        session.commit()
        session.close()
        
def get_log_channel(guild, bot):
    """Fetches the log channel for a guild from the database and returns a discord.TextChannel object."""
    settings = get_guild_settings(guild.id) 
    if settings.log_channel_id:
        return bot.get_channel(settings.log_channel_id)  
    return None
