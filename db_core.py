from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, create_engine
from sqlalchemy import Integer, DateTime
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from modules.utils import load_cfg


connection_string = load_cfg("config/config.json").get("pg_connection_string")
Base = declarative_base()


class FeedTotal(Base):
    __tablename__ = "feed_total"
    id = Column(Integer, primary_key=True)
    ip = Column(postgresql.INET, index=True)
    added = Column(DateTime(timezone=True), server_default=func.now())


def create_db():
    engine = create_engine(connection_string, pool_size=800)
    Base.metadata.create_all(engine)
    cursor = engine.connect()
    Session = sessionmaker(bind=cursor)
    session = Session()
    return session
