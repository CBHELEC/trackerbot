from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

DATABASE_URL = f"sqlite:///{Path(__file__).parent.resolve() / 'data' / 'furry.db'}"
print(DATABASE_URL)

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

class Furry(Base):
    __tablename__ = "furry"
    user_id = Column(String, primary_key=True)
    last_url = Column(String)
    current = Column(Integer, default=1)
    best = Column(Integer, default=1)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_furry_streak(user_id: str):
    with SessionLocal() as session:
        return session.get(Furry, user_id)

def update_furry_streak(user_id: str, image_url: str):
    with SessionLocal() as session:
        furry = session.get(Furry, user_id)
        new_record_message = None

        if furry:
            if furry.last_url == image_url:
                furry.current += 1
            else:
                furry.current = 1
                furry.last_url = image_url

            if furry.current > furry.best:
                furry.best = furry.current
                if furry.current > 1:
                    new_record_message = f"🎉 New record streak: {furry.current} with the same image!"
        else:
            furry = Furry(user_id=user_id, last_url=image_url, current=1, best=1)
            session.add(furry)
            new_record_message = f"🎉 New record streak: 1 with the same image!"

        session.commit()
        return furry.current, furry.best, new_record_message