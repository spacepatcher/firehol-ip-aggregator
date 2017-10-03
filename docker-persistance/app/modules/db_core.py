import os

from modules.general import load_cfg
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy_utils import database_exists, create_database

connection_string = load_cfg("%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf/config.json")).get("pg_connection_string")
database_name = load_cfg("%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf/config.json")).get("feed")
Base = declarative_base()


class FeedTotal(Base):
    __tablename__ = "feed_total"
    id = Column(Integer, primary_key=True)
    ip = Column(postgresql.INET, index=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())


def create_db():
    engine = create_engine(connection_string, pool_size=10, max_overflow=5)
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)
    cursor = engine.connect()
    Session = sessionmaker(bind=cursor)
    session = Session()
    return session
