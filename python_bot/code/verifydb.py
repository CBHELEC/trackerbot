from sqlalchemy import Column, BigInteger, Integer, String, MetaData, Table, select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pathlib import Path

DATABASE_URL = f"sqlite+aiosqlite:///{Path(__file__).parent.resolve() / 'data' / 'verifications.db'}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
metadata = MetaData()

def get_guild_table_class(guild_id: int):
    table_name = f"guild_{guild_id}"
    return Table(
        table_name,
        metadata,
        Column("user_id", BigInteger, nullable=False),
        Column("message_id", BigInteger, nullable=False),
        Column("verify_id", Integer, primary_key=True, autoincrement=True),
        Column("gc_username", String),
        Column("status", String, default="pending"),
        extend_existing=True
    )

async def ensure_table_exists(guild_id: int):
    table = get_guild_table_class(guild_id)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all, tables=[table])
    return table

async def add_verification(guild_id: int, user_id: int, message_id: int, gc_username: str):
    table = await ensure_table_exists(guild_id)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            table.insert().values(
                user_id=user_id,
                message_id=message_id,
                gc_username=gc_username,
                status="pending"
            ).returning(table.c.verify_id)
        )
        await session.commit()
        verify_id = result.scalar_one()
        return verify_id

async def find_gc_username(user_id: int, exclude_guild_id: int = None):
    """Find the gc_username for a user from approved verifications only."""
    async with engine.begin() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: sync_conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'guild_%'")
            ).fetchall()
        )
    
    async with AsyncSessionLocal() as session:
        for (table_name,) in tables:
            if exclude_guild_id is not None and table_name == f"guild_{exclude_guild_id}":
                continue
            
            try:
                guild_id_from_table = int(table_name.replace("guild_", ""))
            except ValueError:
                continue
            
            async with engine.begin() as check_conn:
                result = await check_conn.run_sync(
                    lambda sync_conn: sync_conn.execute(
                        text(f"PRAGMA table_info({table_name})")
                    ).fetchall()
                )
                columns = [col[1] for col in result]
                has_status = 'status' in columns
            
            columns_list = [
                Column("user_id", BigInteger),
                Column("message_id", BigInteger),
                Column("verify_id", Integer, primary_key=True),
                Column("gc_username", String),
            ]
            if has_status:
                columns_list.append(Column("status", String))
            
            table = Table(
                table_name,
                metadata,
                *columns_list,
                extend_existing=True
            )
            
            try:
                if has_status:
                    query = select(table.c.gc_username).where(
                        table.c.user_id == user_id,
                        table.c.status == "approved"
                    )
                else:
                    query = select(table.c.gc_username).where(
                        table.c.user_id == user_id
                    )
                
                result = await session.execute(query)
                row = result.first()
                if row:
                    return row[0]  
            except Exception as e:
                print(f"Error querying table {table_name} for user {user_id}: {e}")
                continue
    
    return None

async def fetch_verification(guild_id: int, verify_id: int):
    table = await ensure_table_exists(guild_id)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(table).where(table.c.verify_id == verify_id)
        )
        row = result.first()
        return dict(row._mapping) if row else None

async def has_pending_verification(guild_id: int, user_id: int):
    """Check if a user has a pending verification request in the specified guild."""
    table = await ensure_table_exists(guild_id)
    table_name = f"guild_{guild_id}"
    
    async with AsyncSessionLocal() as session:
        async with engine.begin() as conn:
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text(f"PRAGMA table_info({table_name})")
                ).fetchall()
            )
            columns = [col[1] for col in result]
            has_status = 'status' in columns
        
        if has_status:
            result = await session.execute(
                select(table).where(
                    table.c.user_id == user_id,
                    table.c.status == "pending"
                )
            )
        else:
            result = await session.execute(
                select(table).where(table.c.user_id == user_id)
            )
        row = result.first()
        return row is not None

async def update_verification_status(guild_id: int, verify_id: int, status: str):
    """Update the status of a verification record."""
    table = await ensure_table_exists(guild_id)
    table_name = f"guild_{guild_id}"
    
    async with AsyncSessionLocal() as session:
        async with engine.begin() as conn:
            result = await conn.run_sync(
                lambda sync_conn: sync_conn.execute(
                    text(f"PRAGMA table_info({table_name})")
                ).fetchall()
            )
            columns = [col[1] for col in result]
            
            if 'status' not in columns:
                await conn.run_sync(
                    lambda sync_conn: sync_conn.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN status TEXT DEFAULT 'pending'")
                    )
                )
                await conn.run_sync(
                    lambda sync_conn: sync_conn.execute(
                        text(f"UPDATE {table_name} SET status = 'pending' WHERE status IS NULL")
                    )
                )
        
        await session.execute(
            table.update().where(table.c.verify_id == verify_id).values(status=status)
        )
        await session.commit()

async def delete_verification(guild_id: int, verify_id: int):
    """Delete a verification record from the database."""
    table = await ensure_table_exists(guild_id)
    
    async with AsyncSessionLocal() as session:
        await session.execute(
            table.delete().where(table.c.verify_id == verify_id)
        )
        await session.commit()