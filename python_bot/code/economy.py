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
    cacher_name = Column(String, nullable=True)
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
    location_lat = Column(Float, nullable=True)  # Latitude
    location_lon = Column(Float, nullable=True)  # Longitude
    description = Column(String, nullable=True)  # Description of the hide
    difficulty = Column(String, nullable=True)  # Difficulty level (1-5)
    terrain = Column(String, nullable=True) # Terrain level (1-5)
    hidden_at = Column(DateTime, nullable=True)  # Time hidden
    size = Column(String, nullable=True)  # Size of the hide (eg. micro, small, regular, large)
    location_name = Column(String, nullable=True)  # Place name
    published = Column(Integer, default=0)  # Published status (0: not published, 1: published)
    container = Column(String, nullable=True)  # Container ID
    logbook = Column(String, nullable=True)  # Logbook (if applicable)
    pen = Column(String, nullable=True)  # Pen (if applicable)
    writing_instrument_id = Column(String, nullable=True)  # Writing instrument ID (if applicable)

class Inventory(Base):
    __tablename__ = "inventory"

    user_id = Column(BigInteger, primary_key=True)  # Who
    item_id = Column(String, nullable=False)  # What
    
class Finds(Base):
    __tablename__ = "finds"

    user_id = Column(BigInteger, primary_key=True)  # Who
    cache_id = Column(String, nullable=False)  # What
    log_content = Column(String, nullable=False)  # Log content
    fp_status = Column(Integer, default=0)  # FP status (0: not given, 1: given)
    
class Trackables(Base):
    __tablename__ = "trackables"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Auto-incrementing primary key
    user_id = Column(BigInteger, nullable=False)  # User ID (who owns the trackable)
    public_code = Column(String, nullable=False)  # Public code for the trackable
    private_code = Column(String, nullable=False)  # Private code for the trackable
    activated = Column(Integer, nullable=False, default=0)  # Activation status (0: not activated, 1: activated)
    tb_id = Column(Integer, nullable=False)  # What TB the TB is
    activated_time = Column(String, nullable=True) # Time of activation

class TBDiscover(Base):
    __tablename__ = "tb_discover"

    user_id = Column(BigInteger, nullable=False, primary_key=True)  # User ID who discovered the trackable
    tb_private_code = Column(String, nullable=False, primary_key=True)  # Private code of the trackable
    discover_date = Column(String, nullable=False)  # Date of discovery
    discover_log = Column(String, nullable=True)  # Log for the discovery

class DailyLogin(Base):
    __tablename__ = "dailylogin"

    user_id = Column(Integer, primary_key=True, nullable=False)
    last_withdraw = Column(String, nullable=False)

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

async def get_lastclaim(session: AsyncSession, user_id: int):
    result = await session.execute(select(DailyLogin).where(DailyLogin.user_id == user_id))
    last_claim = result.scalars().first()
    return last_claim

async def set_lastclaim(session, user_id: int, last_withdraw: str):
    """
    Set the last claim date for a user. If the user already exists, update the record.
    """
    async with session.begin():
        result = await session.execute(
            select(DailyLogin).where(DailyLogin.user_id == user_id)
        )
        existing_record = result.scalars().first()

        if existing_record:
            existing_record.last_withdraw = last_withdraw
        else:
            new_record = DailyLogin(user_id=user_id, last_withdraw=last_withdraw)
            session.add(new_record)

async def add_trackable(session: AsyncSession, user_id: int, public_code: str, private_code: str, tb_id: int):
    new_trackable = Trackables(
        user_id=user_id,
        public_code=public_code,
        private_code=private_code,
        activated=0,  # Default to not activated
        tb_id=tb_id
    )
    session.add(new_trackable)
    await session.commit()
    return new_trackable

async def get_trackables_by_user(session: AsyncSession, user_id: int):
    result = await session.execute(select(Trackables).where(Trackables.user_id == user_id))
    return result.scalars().all()

async def activate_trackable(session: AsyncSession, user_id: int, private_code: str):
    """
    Activate a trackable based on the private code if the user owns it and it is not already activated.

    Args:
        session (AsyncSession): The database session.
        user_id (int): The ID of the user attempting to activate the trackable.
        private_code (str): The private code of the trackable to activate.

    Returns:
        Trackables: The activated trackable object if successful, or None if not.
    """
    # Retrieve the trackable based on the private code
    result = await session.execute(
        select(Trackables).where(Trackables.private_code == private_code)
    )
    trackable = result.scalars().first()

    # Check if the trackable exists, the user owns it, and it is not already activated
    if trackable and trackable.user_id == user_id:
        if trackable.activated == 1:
            # Trackable is already activated
            return "already_activated"
        else:
            # Activate the trackable
            trackable.activated = 1
            trackable.activated_time = datetime.now()
            await session.commit()
            return trackable

    # Return None if the trackable doesn't exist or the user doesn't own it
    return None

async def add_tb_discovery(session: AsyncSession, user_id: int, tb_private_code: str, discover_date: str, discover_log: str = None):
    new_discovery = TBDiscover(
        user_id=user_id,
        tb_private_code=tb_private_code,
        discover_date=discover_date,
        discover_log=discover_log
    )
    session.add(new_discovery)
    await session.commit()
    return new_discovery

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

async def get_cacher_name(session: AsyncSession, user_id: int):
    return (await get_db_settings(session, user_id)).cacher_name

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
    
async def add_hide(session: AsyncSession, cache_id: str, user_id: int, name: str, lat: float, lon: float, description: str, difficulty: int, terrain: int, hidden_at: str, size: str, location_name: str):
    new_hide = Hide(
        id=cache_id,
        user_id=user_id,
        name=name,
        location_lat=lat,
        location_lon=lon,
        description=description,
        difficulty=difficulty,
        terrain=terrain,
        hidden_at=hidden_at,
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
            cacher_name=cacher_name  # Default cacher name if not provided
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
    return db_settings

async def find(session: AsyncSession, user_id: int, hide_id: str, log_content: str = "", fp_status: int = 0):
    # Check if the hide exists
    hide = await get_hide_by_id(session, hide_id)
    if not hide:
        return False  # Hide does not exist

    # Check if the user has already logged this find
    existing_find = await session.execute(
        select(Finds).where(Finds.user_id == user_id, Finds.cache_id == hide_id)
    )
    if existing_find.scalars().first():
        return False  # Find already logged

    # Log the find in the Finds table
    new_find = Finds(
        user_id=user_id,
        cache_id=hide_id,
        log_content=log_content,
        fp_status=fp_status,
    )
    session.add(new_find)

    # Update the user's finds count in DBSettings
    db_settings = await get_db_settings(session, user_id)
    if db_settings:
        db_settings.finds += 1
        await session.commit()
        return True

    return False  # User does not exist in the database

async def get_finds_for_cache(session: AsyncSession, cache_id: str) -> list:
    """
    Retrieve all finds for a specific cache.

    Args:
        session (AsyncSession): The database session.
        cache_id (str): The ID of the cache to retrieve finds for.

    Returns:
        list: A list of Finds objects for the specified cache.
    """
    result = await session.execute(select(Finds).where(Finds.cache_id == cache_id))
    return result.scalars().all()

async def update_hide_name(session: AsyncSession, hide_id: str, name: str):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.name = name
        await session.commit()
        return True
    return False

async def update_hide_location(session: AsyncSession, hide_id: str, lat: float, lon: float):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.location_lat = lat
        hide.location_lon = lon
        await session.commit()
        return True
    return False

async def update_hide_description(session: AsyncSession, hide_id: str, description: str):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.description = description
        await session.commit()
        return True
    return False

async def update_hide_difficulty(session: AsyncSession, hide_id: str, difficulty: int):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.difficulty = difficulty
        await session.commit()
        return True
    return False

async def update_hide_terrain(session: AsyncSession, hide_id: str, terrain: int):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.terrain = terrain
        await session.commit()
        return True
    return False

async def update_hide_size(session: AsyncSession, hide_id: str, size: str):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.size = size
        await session.commit()
        return True
    return False

async def update_hide_location_name(session: AsyncSession, hide_id: str, location_name: str):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.location_name = location_name
        await session.commit()
        return True
    return False

async def update_hide_published(session: AsyncSession, hide_id: str, published: int):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.published = published
        await session.commit()
        return True
    return False

async def update_hide_containerid(session: AsyncSession, hide_id: str, containerid: str):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.container = containerid  # FIX: should update 'size', not 'container'
        await session.commit()
        return True
    return False

async def update_hide_logbook(session: AsyncSession, hide_id: str, logbook: str):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.logbook = logbook
        await session.commit()
        return True
    return False

async def update_hide_hidden_at(session: AsyncSession, hide_id: str, hidden_at: datetime):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.hidden_at = hidden_at
        await session.commit()
        return True
    return False

async def update_hide_pen(session: AsyncSession, hide_id: str, pen: str):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.pen = pen
        await session.commit()
        return True
    return False

async def update_hide_writing_instrument(session: AsyncSession, hide_id: str, writing_instrument_id: str):
    result = await session.execute(select(Hide).where(Hide.id == hide_id))
    hide = result.scalars().first()
    if hide:
        hide.writing_instrument_id = writing_instrument_id
        await session.commit()
        return True
    return False

async def start_hide(session: AsyncSession, hide_id: str, user_id: int):
    # Check for existing unpublished hide for this user
    result = await session.execute(select(Hide).where(Hide.user_id == user_id, Hide.published == 0))
    existing_hide = result.scalars().first()
    if existing_hide:
        return existing_hide
    # Otherwise, create a new hide
    new_hide = Hide(
        id=hide_id,
        user_id=user_id,
    )
    session.add(new_hide)
    await session.commit()
    await session.refresh(new_hide)
    return new_hide