from sqlalchemy import create_engine
from economy import Base, DBSettings, Hide  # Import your models

DATABASE_URL = "sqlite:///economygame.db"  # Use the correct path here

# Create a synchronous engine for manual initialization
engine = create_engine(DATABASE_URL, echo=True)

def init_db_manually():
    with engine.begin() as conn:
        # Manually create only DBSettings and Hide tables
        Base.metadata.create_all(conn, tables=[DBSettings.__table__, Hide.__table__])

    print("DBSettings and Hide tables created!")

init_db_manually()