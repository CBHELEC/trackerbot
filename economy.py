from sqlalchemy import Column, BigInteger, Integer, String, Float, DateTime, text
from sqlalchemy.orm import declarative_base
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from datetime import datetime

# Database Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'economygame.db')}"

Base = declarative_base()

class DBSettings(Base):
    __tablename__ = "db_settings"

    user_id = Column(BigInteger, primary_key=True)
    cacher_name = Column(String, nullable=False)
    balance = Column(Integer, default=100)
    hides = Column(Integer, default=0)
    finds = Column(BigInteger, default=0)
    fav_points_owned = Column(Integer, default=10)
    fav_points_recieved = Column(Integer, default=0)
    fake_finds_owned = Column(Integer, default=10)
    fake_finds_recieved = Column(Integer, default=0)
    logs_recieved = Column(Integer, default=0)
    logs_created = Column(Integer, default=0)
    trackables_owned = Column(Integer, default=0)
    trackables_activated = Column(Integer, default=0)
    trackables_discovered = Column(Integer, default=0)
    events_hosted = Column(Integer, default=0)
    events_attended = Column(Integer, default=0)
    souvenirs_recieved = Column(Integer, default=0)
    caches_damaged = Column(Integer, default=0)
    cache_damage_recieved = Column(Integer, default=0)
    cache_damage_balance = Column(Integer, default=0)

class Hide(Base):
    __tablename__ = "hides"

    id = Column(String, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)  # Who hid it
    name = Column(String, nullable=False)  # Name of the hide
    location_lat = Column(Float, nullable=False)  # Latitude
    location_lon = Column(Float, nullable=False)  # Longitude
    description = Column(String, nullable=True)  # Description of the hide
    difficulty = Column(Integer, default=1)  # Difficulty level (1-5)
    terrain = Column(Integer, default=1) # Terrain level (1-5)
    hidden_at = Column(DateTime, default=datetime.now)  # Time hidden
    size = Column(String, nullable=False)  # Size of the hide (eg. micro, small, regular, large)
    location_name = Column(String, nullable=False)  # Place name

class Inventory(Base):
    __tablename__ = "inventory"

    user_id = Column(BigInteger, primary_key=True)  # Who
    item_id = Column(String, nullable=False)  # What

# Database setup
engine = create_async_engine(DATABASE_URL, echo=False, isolation_level=None)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  

async def get_db_settings(session: AsyncSession, user_id: int) -> DBSettings:
    """Retrieve DBSettings for a user, creating one if it doesn't exist."""
    result = await session.execute(select(DBSettings).where(DBSettings.user_id == user_id))
    db_settings = result.scalars().first()
    return db_settings

async def set_cacher_name(session: AsyncSession, user_id: int, cacher_name: str):
    db_settings = await get_db_settings(session, user_id)
    if not db_settings.cacher_name:
        db_settings.cacher_name = cacher_name
        await session.commit()

async def get_inventory(session: AsyncSession, user_id: int) -> list:
    """Retrieve all inventory items for a user."""
    result = await session.execute(select(Inventory).where(Inventory.user_id == user_id))
    inventory = result.scalars().first()
    if inventory:
        return inventory.item_id.split(',')  # Split the comma-separated string into a list
    return []  # Return an empty list if no inventory exists

async def remove_inv_item(session: AsyncSession, user_id: int, item_id: str):
    """Remove an item from the user's inventory."""
    result = await session.execute(select(Inventory).where(Inventory.user_id == user_id))
    inventory = result.scalars().first()
    if inventory:
        current_items = inventory.item_id.split(',')
        if item_id in current_items:
            current_items.remove(item_id)
            inventory.item_id = ','.join(current_items)  # Update the column with the new list
            await session.commit()
            return True
    return False

async def get_balance(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).balance

async def get_hides(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).hides

async def get_finds(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).finds

async def get_fav_points_owned(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).fav_points_owned

async def get_fav_points_recieved(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).fav_points_recieved

async def get_fake_finds_owned(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).fake_finds_owned

async def get_fake_finds_recieved(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).fake_finds_recieved

async def get_logs_recieved(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).logs_recieved

async def get_logs_created(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).logs_created

async def get_trackables_owned(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).trackables_owned

async def get_trackables_activated(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).trackables_activated

async def get_trackables_discovered(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).trackables_discovered

async def get_events_hosted(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).events_hosted

async def get_events_attended(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).events_attended

async def get_souvenirs_recieved(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).souvenirs_recieved

async def get_caches_damaged(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).caches_damaged

async def get_cache_damage_recieved(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).cache_damage_recieved

async def get_cache_damage_balance(session: AsyncSession, user_id: int) -> int:
    return (await get_db_settings(session, user_id)).cache_damage_balance

async def update_balance(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.balance = value
    await session.commit()

async def add_inv_item(session: AsyncSession, user_id: int, item_id: str):
    """Add an item to the user's inventory."""
    result = await session.execute(select(Inventory).where(Inventory.user_id == user_id))
    inventory = result.scalars().first()
    if inventory:
        # Split the current inventory into a list
        current_items = [item.strip() for item in inventory.item_id.split(',') if item.strip()]
        
        # Add the new item(s) to the list, avoiding duplicates
        if item_id not in current_items:
            current_items.append(item_id)
        
        # Rejoin the list into a comma-separated string
        inventory.item_id = ','.join(current_items)
    else:
        # Create a new inventory entry if none exists
        inventory = Inventory(user_id=user_id, item_id=item_id)
        session.add(inventory)
    await session.commit()

async def update_hides(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.hides = value
    await session.commit()

async def update_finds(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.finds = value
    await session.commit()

async def update_fav_points_owned(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.fav_points_owned = value
    await session.commit()

async def update_fav_points_recieved(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.fav_points_recieved = value
    await session.commit()

async def update_fake_finds_owned(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.fake_finds_owned = value
    await session.commit()

async def update_fake_finds_recieved(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.fake_finds_recieved = value
    await session.commit()

async def update_logs_recieved(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.logs_recieved = value
    await session.commit()

async def update_logs_created(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.logs_created = value
    await session.commit()

async def update_trackables_owned(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.trackables_owned = value
    await session.commit()

async def update_trackables_activated(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.trackables_activated = value
    await session.commit()

async def update_trackables_discovered(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.trackables_discovered = value
    await session.commit()

async def update_events_hosted(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.events_hosted = value
    await session.commit()

async def update_events_attended(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.events_attended = value
    await session.commit()

async def update_souvenirs_recieved(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.souvenirs_recieved = value
    await session.commit()

async def update_caches_damaged(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.caches_damaged = value
    await session.commit()

async def update_cache_damage_recieved(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.cache_damage_recieved = value
    await session.commit()

async def update_cache_damage_balance(session: AsyncSession, user_id: int, value: int):
    db_settings = await get_db_settings(session, user_id)
    db_settings.cache_damage_balance = value
    await session.commit()
    
async def add_hide(session: AsyncSession, cache_id: str, user_id: int, name: str, lat: float, lon: float, description: str, difficulty: int, terrain: int, size: str, location_name: str):
    new_hide = Hide(
        id=cache_id,
        user_id=user_id,
        name=name,
        location_lat=lat,
        location_lon=lon,
        description=description,
        difficulty=difficulty,
        terrain=terrain,
        size=size,
        location_name=location_name,
    )
    session.add(new_hide)
    await session.commit()
    await session.refresh(new_hide)
    return new_hide

async def get_hides_by_user(session: AsyncSession, user_id: int):
    result = await session.execute(select(Hide).where(Hide.user_id == user_id))
    return result.scalars().all()

async def get_hide_by_id(session: AsyncSession, hide_id: int):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    return result.scalars().first()

async def delete_hide(session: AsyncSession, hide_id: int):
    hide = await get_hide_by_id(session, hide_id)
    if hide:
        await session.delete(hide)
        await session.commit()
        return True
    return False

async def get_all_hide_ids(session: AsyncSession):
    result = await session.execute(text("SELECT id FROM hides"))  # Raw SQL query for efficiency
    return [row[0] for row in result.fetchall()]  # Extracting only the ID values

async def add_user_to_db(session: AsyncSession, user_id: int, cacher_name: str = None):
    db_settings = await get_db_settings(session, user_id)
    if not db_settings:
        new_user = DBSettings(
            user_id=user_id,
            cacher_name=cacher_name or f"User_{user_id}"  # Default cacher name if not provided
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
    return db_settings