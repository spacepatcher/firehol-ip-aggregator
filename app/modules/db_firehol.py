from modules.db_core import FeedAlchemy
from modules.general import General
from sqlalchemy import exc
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert


General = General()
FeedAlchemy = FeedAlchemy()


def db_add_data(data_to_add):
    feed_meta = data_to_add.get("feed_meta")
    feed_table_name = "feed_" + data_to_add.get("feed_name")
    db_session = FeedAlchemy.get_db_session()
    while True:
        try:
            meta_table = FeedAlchemy.get_meta_table_object()
            insert_query = insert(meta_table).values(feed_meta)\
                .on_conflict_do_update(index_elements=["feed_name"], set_=dict(maintainer=feed_meta.get("maintainer"),
                                                                               maintainer_url=feed_meta.get("maintainer_url"),
                                                                               list_source_url=feed_meta.get("list_source_url"),
                                                                               source_file_date=feed_meta.get("source_file_date"),
                                                                               category=feed_meta.get("category"),
                                                                               entries=feed_meta.get("entries")))
            db_session.execute(insert_query)
            db_session.commit()
            break
        except exc.IntegrityError as e:
            General.logger.warning("Warning: {}".format(e))
            General.logger.info("Attempt to update meta table will be made in the next iteration of an infinite loop")
            db_session.rollback()
    try:
        feed_table = FeedAlchemy.get_feed_table_object(feed_table_name)
        for ip_group in General.group_by(n=100000, iterable=data_to_add.get("added_ip")):
            for ip in ip_group:
                insert_query = insert(feed_table).values(ip=ip, first_seen=func.now(), feed_name=data_to_add.get("feed_name"))\
                    .on_conflict_do_update(index_elements=["ip"], set_=dict(last_added=func.now()))
                db_session.execute(insert_query)
            db_session.commit()
    except Exception as e:
        General.logger.error("Error: {}".format(e))
        General.logger.exception("Can't commit to DB. Rolling back changes...")
        db_session.rollback()
    finally:
        db_session.close()


def db_search_data(net_list):
    search_result_by_ip = dict()
    db_session = FeedAlchemy.get_db_session()
    try:
        FeedAlchemy.metadata.reflect(bind=FeedAlchemy.engine)
        meta_table = FeedAlchemy.metadata.tables[FeedAlchemy.feeds_meta_table]
        feed_tables = [table for table in reversed(FeedAlchemy.metadata.sorted_tables) if "feed_" in table.name]
        for net in net_list:
            search_result = list()
            for feed_table in feed_tables:
                search_query = "SELECT * FROM {feed_table_name} f, {meta_table_name} m WHERE f.feed_name = m.feed_name AND f.ip<<='{net}'"\
                    .format(feed_table_name=feed_table.name, meta_table_name=meta_table.name, net=net)
                search_result_raw = db_session.execute(search_query).fetchall()
                search_result.extend([dict(zip(search_result_item.keys(), search_result_item))
                                           for search_result_item in search_result_raw if search_result_raw])
            search_result_grouped = General.group_dict_by_key(search_result, "ip")
            search_result_extended = General.extend_result_data(search_result_grouped, len(feed_tables))
            search_result_by_ip.update(search_result_extended)
        return search_result_by_ip
    except Exception as e:
        General.logger.error("Error: {}".format(e))
        General.logger.exception("Error while searching occurred")
    finally:
        db_session.close()
