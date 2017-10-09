from sqlalchemy import Column, DateTime
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database
from modules.general import General

General = General()
Base = declarative_base()


class FeedTotal(Base):
    __tablename__ = "feed_total"
    ip = Column(postgresql.INET, primary_key=True)
    last_added = Column(DateTime(timezone=True), server_default=func.now())


def create_db_session(database_name):
    connection_string = "postgresql://%s:%s@%s:5432/%s" % (General.database_user, General.database_password, General.server_address, database_name)
    engine = create_engine(connection_string, poolclass=NullPool)
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)
    cursor = engine.connect()
    Session = sessionmaker(bind=cursor)
    session = Session()
    return session
