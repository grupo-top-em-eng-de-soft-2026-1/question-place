from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import app.config

engine = create_engine(app.config.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
