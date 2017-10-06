import os

from modules.general import load_cfg
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy_utils import database_exists, create_database

database_user = load_cfg("%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf/config.json")).get("pg_database_user")
database_password = load_cfg("%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf/config.json")).get("pg_database_password")
server_address = load_cfg("%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf/config.json")).get("pg_server_address")
database_name = load_cfg("%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf/config.json")).get("pg_database_name")
connection_string = "postgresql://%s:%s@%s:5432/%s" % (database_user, database_password, server_address, database_name)

Base = declarative_base()


class FeedTotal(Base):
    __tablename__ = "feed_total"
    ip = Column(postgresql.INET, primary_key=True)
    last_added = Column(DateTime(timezone=True), server_default=func.now())


def create_db():
    engine = create_engine(connection_string, pool_size=100, max_overflow=0)
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)
    cursor = engine.connect()
    Session = sessionmaker(bind=cursor)
    session = Session()
    return session
