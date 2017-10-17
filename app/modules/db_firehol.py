from modules.db_core import FeedAlchemy
from modules.general import General
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert


General = General()
FeedAlchemy = FeedAlchemy()


def db_add_data(data_to_add):
    feed_table_name = "feed_" + data_to_add.get("feed_name")
    feed_meta_table_name = "meta_" + data_to_add.get("feed_name")
    feed_table = FeedAlchemy.get_feed_table_object(feed_table_name)
    feed_meta_table = FeedAlchemy.get_feed_meta_table_object(feed_meta_table_name)
    db_session = FeedAlchemy.get_db_session()
    try:
        delete_query = feed_meta_table.delete()
        insert_query = insert(feed_meta_table).values(data_to_add.get("feed_meta"))
        db_session.execute(delete_query)
        db_session.execute(insert_query)
        db_session.commit()
        for ip_group in General.group_by(n=100000, iterable=data_to_add.get("added_ip")):
            for ip in ip_group:
                insert_query = insert(feed_table).values(ip=ip, first_seen=func.now()).on_conflict_do_update(index_elements=["ip"], set_=dict(last_added=func.now()))
                db_session.execute(insert_query)
            db_session.commit()
    except Exception as e:
        General.logger.error("Error: {}".format(e))
        General.logger.exception("Can't commit to DB. Rolling back changes...")
        db_session.rollback()
    finally:
        db_session.close()
