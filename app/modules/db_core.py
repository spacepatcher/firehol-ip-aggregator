from sqlalchemy import MetaData, Table, Column, DateTime
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database
from modules.general import General

General = General()


def get_feed_table_object(table_name):
    metadata = MetaData()
    Table(table_name, metadata,
          Column("ip", postgresql.INET, primary_key=True),
          Column("first_seen", DateTime(timezone=True), server_default=func.now()),
          Column("last_added", DateTime(timezone=True), server_default=func.now()))
    return metadata


def create_db_session(database_name, table_name):
    connection_string = "postgresql://%s:%s@%s:5432/%s" % (General.database_user, General.database_password, General.server_address, database_name)
    engine = create_engine(connection_string, poolclass=NullPool)
    if not database_exists(engine.url):
        create_database(engine.url)
    get_feed_table_object(table_name).create_all(engine)
    cursor = engine.connect()
    Session = sessionmaker(bind=cursor)
    return Session()
