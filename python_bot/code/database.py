from sqlalchemy import create_engine, Column, BigInteger, Boolean, String, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text
from pathlib import Path
from sqlalchemy.types import TypeDecorator, Integer

DATABASE_URL = f"sqlite:///{Path(__file__).parent.resolve() / 'data' / 'bot_settings.db'}"

Base = declarative_base()

class BoolInt(TypeDecorator):
    impl = Integer

    def process_bind_param(self, value, dialect):
        return int(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return bool(value) if value is not None else None

class GuildSettings(Base):
    __tablename__ = "guild_settings"

    guild_id = Column(BigInteger, primary_key=True)
    mod_role_ids = Column(String, default="")
    perm_role_ids = Column(String, default="")
    log_channel_id = Column(BigInteger, nullable=True)
    skullboard_status = Column(Boolean, default=False)
    skullboard_channel_id = Column(BigInteger, nullable=True)
    detection_status = Column(BoolInt, default=True)
    link_embed_status = Column(BoolInt, default=True)
    message_set = Column(Integer, default=True)
    tb_set = Column(BoolInt, default=True)
    fun_set = Column(Integer, default=True)
    game_set = Column(BoolInt, default=True)
    deadcode = Column(BoolInt, default=True)
    verify_channel_id = Column(BigInteger, nullable=True)
    verify_verified_role_id = Column(BigInteger, nullable=True)
    verify_unverified_role_id = Column(BigInteger, nullable=True)
    verify_admin_role_id = Column(String, default="")
    verify_fasttrack_status = Column(BoolInt, default=True)
    verify_muggle_role_id = Column(BigInteger, nullable=True)
    verification_status = Column(BoolInt, default=False) 

engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def migrate_database():
    """Add verification_status column to existing databases if it doesn't exist."""
    try:
        inspector = inspect(engine)
        if 'guild_settings' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('guild_settings')]
            if 'verification_status' not in columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE guild_settings ADD COLUMN verification_status INTEGER DEFAULT 0"))
                print("Migration: Added 'verification_status' column to guild_settings table")
    except Exception as e:
        print(f"Migration warning: Could not add verification_status column: {e}")

migrate_database()

def get_guild_settings(guild_id):
    """Fetch guild settings, create entry if missing."""
    with Session() as session:
        settings = session.query(GuildSettings).filter_by(guild_id=guild_id).first()
        if not settings:
            settings = GuildSettings(guild_id=guild_id)
            session.add(settings)
            session.commit()
            session.refresh(settings)  

        _ = settings.detection_status

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
        session.refresh(settings)  
        session.close()
        
def get_log_channel(guild, bot):
    """Fetches the log channel for a guild from the database and returns a discord.TextChannel object."""
    settings = get_guild_settings(guild.id) 
    if settings.log_channel_id:
        return bot.get_channel(settings.log_channel_id)  
    return None
