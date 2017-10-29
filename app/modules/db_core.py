from sqlalchemy import MetaData, Table, Column, DateTime, ForeignKey
from sqlalchemy import create_engine, exc
from sqlalchemy.dialects import postgresql
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from modules.general import General


class FeedAlchemy(General):
    def __init__(self):
        super().__init__()
        self.feeds_meta_table = "feeds_meta"
        self.connection_string = "postgresql://%s:%s@%s:5432/%s" % (self.database_user, self.database_password, self.server_address, self.database_name)
        self.engine = create_engine(self.connection_string, poolclass=NullPool)
        self.metadata = MetaData()

    def get_feed_table_object(self, table_name):
        if not database_exists(self.engine.url):
            create_database(self.engine.url)
        feed_table = Table(table_name, self.metadata,
            Column("ip", postgresql.INET, primary_key=True),
            Column("first_seen", DateTime(timezone=True), server_default=func.now()),
            Column("last_added", DateTime(timezone=True), server_default=func.now()),
            Column("feed_name", postgresql.TEXT, ForeignKey("feeds_meta.feed_name"))
        )
        feed_table.create(self.engine, checkfirst=True)
        return feed_table

    def get_meta_table_object(self):
        if not database_exists(self.engine.url):
            create_database(self.engine.url)
        meta_table = Table(self.feeds_meta_table, self.metadata,
            Column("feed_name", postgresql.TEXT, primary_key=True),
            Column("maintainer", postgresql.TEXT),
            Column("maintainer_url", postgresql.TEXT),
            Column("list_source_url", postgresql.TEXT),
            Column("source_file_date", postgresql.TEXT),
            Column("category", postgresql.TEXT),
            Column("entries", postgresql.TEXT),
            extend_existing=True
        )
        try:
            meta_table.create(self.engine, checkfirst=True)
        except exc.ProgrammingError:
            pass
        return meta_table

    def get_db_session(self):
        try:
            cursor = self.engine
            Session = sessionmaker(bind=cursor)
            return Session()
        except Exception:
            self.logger.exception("Error in database session creation occurred")
