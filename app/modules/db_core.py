from sqlalchemy import MetaData, Table, Column, DateTime
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from modules.general import General


class FeedAlchemy(General):
    def __init__(self):
        super().__init__()
        self.connection_string = "postgresql://%s:%s@%s:5432/%s" % (self.database_user, self.database_password, self.server_address, self.database_name)
        self.engine = create_engine(self.connection_string, poolclass=NullPool)
        if not database_exists(self.engine.url):
            create_database(self.engine.url)

    def get_feed_table_object(self, table_name):
        metadata = MetaData()
        feed_table = Table(table_name, metadata,
            Column("ip", postgresql.INET, primary_key=True),
            Column("first_seen", DateTime(timezone=True), server_default=func.now()),
            Column("last_added", DateTime(timezone=True), server_default=func.now())
        )
        metadata.create_all(self.engine)
        return feed_table

    def get_feed_meta_table_object(self, table_name):
        metadata = MetaData()
        feed_meta_table = Table(table_name, metadata,
            Column("name", postgresql.TEXT),
            Column("maintainer", postgresql.TEXT),
            Column("maintainer_url", postgresql.TEXT),
            Column("list_source_url", postgresql.TEXT),
            Column("source_file_date", postgresql.TEXT),
            Column("category", postgresql.TEXT),
            Column("entries", postgresql.TEXT)
        )
        metadata.create_all(self.engine)
        return feed_meta_table

    def get_db_session(self):
        try:
            cursor = self.engine.connect()
            Session = sessionmaker(bind=cursor)
            return Session()
        except Exception:
            self.logger.exception("Error in creation DB session")
