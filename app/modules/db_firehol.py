from modules.db_feed import FeedAlchemy
from modules.general import General
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert


General = General()
FeedAlchemy = FeedAlchemy()


def db_add_data(data_to_add, feed_name):
    table_name = "feed_" + feed_name
    db_session, feed_table = FeedAlchemy.get_table_access(table_name)
    try:
        for ip_group in General.group_by(n=100000, iterable=data_to_add.get("added_ip")):
            for ip in ip_group:
                stmt = insert(feed_table).values(ip=ip, first_seen=func.now()).on_conflict_do_update(index_elements=["ip"], set_=dict(last_added=func.now()))
                db_session.execute(stmt)
            db_session.commit()
    except Exception as e:
        General.logger.error("Error: {}".format(e))
        General.logger.exception("Can't commit to DB. Rolling back changes...")
        db_session.rollback()
    finally:
        db_session.close()
