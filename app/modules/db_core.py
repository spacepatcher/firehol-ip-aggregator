from time import sleep
from sys import exit

from sqlalchemy import MetaData, Table, Column, DateTime, ForeignKey, Integer
from sqlalchemy import create_engine, exc
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.dialects.postgresql import INET, TEXT, JSONB

from modules.general import General


class Alchemy(General):
    def __init__(self):
        super().__init__()

        self.meta_table_name = "feeds_meta"
        self.aggregated_table_name = "feeds_aggregated"
        self.connection_string = "postgresql://%s:%s@%s:5432/%s" \
                                 % (self.database_user, self.database_password, self.server_address, self.database_name)
        self.metadata = MetaData()

        self.engine = self.get_engine_object(connection_string=self.connection_string, poolclass=NullPool)

    def get_engine_object(self, connection_string, poolclass):
        attempt = 1
        attempts_count = 10
        attempt_period = 2

        while attempt <= attempts_count:
            try:
                engine = create_engine(connection_string, poolclass=poolclass)

                if not database_exists(engine.url):
                    create_database(engine.url)

                self.logger.info("Successfully connected to the database")

                return engine

            except OperationalError:
                self.logger.warning("Connection to the database failed... Sleep for {} seconds. Attempts remaining: {}"
                                    .format(attempt_period, attempts_count - attempt))

                attempt += 1
                sleep(attempt_period)

        self.logger.error("Unable to connect to the database after {} attempts. Exiting..."
                          .format(attempts_count))

        exit(1)

    def get_feed_table_object(self, table_name):
        feed_table = Table(table_name, self.metadata,
            Column("id", Integer, primary_key=True),
            Column("ip", INET, index=True, unique=True),
            Column("first_seen", DateTime(timezone=True)),
            Column("last_added", DateTime(timezone=True)),
            Column("last_removed", DateTime(timezone=True), nullable=True),
            Column("timeline", JSONB, default=[]),
            Column("feed_name", TEXT, ForeignKey("feeds_meta.feed_name")),
            extend_existing=True
        )
        feed_table.create(self.engine, checkfirst=True)

        return feed_table

    def get_meta_table_object(self):
        meta_table = Table(self.meta_table_name, self.metadata,
            Column("feed_name", TEXT, primary_key=True),
            Column("maintainer", TEXT),
            Column("maintainer_url", TEXT),
            Column("list_source_url", TEXT),
            Column("source_file_date", TEXT),
            Column("category", TEXT),
            Column("entries", TEXT),
            extend_existing=True
        )

        try:
            meta_table.create(self.engine, checkfirst=True)
        except exc.ProgrammingError:
            pass

        return meta_table

    def get_aggregated_table_object(self, table_name):
        aggregated_table = Table(table_name, self.metadata,
            Column("id", Integer, primary_key=True),
            Column("ip", INET, index=True, unique=False),
            Column("first_seen", DateTime(timezone=True)),
            Column("last_added", DateTime(timezone=True)),
            Column("last_removed", DateTime(timezone=True), nullable=True),
            Column("timeline", JSONB, default=[]),
            Column("feed_name", TEXT, ForeignKey("feeds_meta.feed_name")),
            extend_existing=True
        )
        aggregated_table.create(self.engine, checkfirst=True)

        return aggregated_table

    def get_db_session(self):
        try:
            cursor = self.engine
            Session = sessionmaker(bind=cursor)

            return Session()

        except Exception:
            self.logger.exception("Error in database session creation occurred")
