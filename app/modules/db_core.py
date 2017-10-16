from sqlalchemy import MetaData, Table, Column, DateTime
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.sql import func
from modules.general import General


class FeedAlchemy(General):
    def __init__(self):
        super().__init__()
        self.connection_string = "postgresql://%s:%s@%s:5432/%s" % (self.database_user, self.database_password, self.server_address, self.database_name)
        self.engine = create_engine(self.connection_string, poolclass=NullPool)
        if not database_exists(self.engine.url):
            create_database(self.engine.url)

    def get_table_access(self, table_name):
        metadata = MetaData()
        feed_table = Table(table_name, metadata,
            Column("ip", postgresql.INET, primary_key=True),
            Column("first_seen", DateTime(timezone=True), server_default=func.now()),
            Column("last_added", DateTime(timezone=True), server_default=func.now())
        )
        metadata.create_all(self.engine)
        return self.create_db_session(self.engine), feed_table
