import pytz
from datetime import datetime
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
    request_time = pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone("Europe/Moscow")).isoformat()
    feed_tables = list()
    results_total = dict()
    results_total_extended = dict()
    db_session = FeedAlchemy.get_db_session()
    try:
        FeedAlchemy.metadata.reflect(bind=FeedAlchemy.engine)
        meta_table = FeedAlchemy.metadata.tables[FeedAlchemy.feeds_meta_table]
        feed_tables = [table for table in reversed(FeedAlchemy.metadata.sorted_tables) if "feed_" in table.name]
        for net in net_list:
            results = list()
            for feed_table in feed_tables:
                sql_query = "SELECT * FROM {feed_table_name} f, {meta_table_name} m WHERE f.feed_name = m.feed_name AND f.ip<<='{net}'"\
                    .format(feed_table_name=feed_table.name, meta_table_name=meta_table.name, net=net)
                raw_results = db_session.execute(sql_query).fetchall()
                results.extend([dict(zip(item.keys(), item)) for item in raw_results if raw_results])
            results_grouped = General.group_dict_by_key(results, "ip")
            results_grouped_extended = General.extend_result_data(results_grouped)
            results_total.update(results_grouped_extended)
    except Exception as e:
        General.logger.error("Error: {}".format(e))
        General.logger.exception("Error while searching occurred")
    finally:
        db_session.close()
    results_total_extended.setdefault("results", results_total)
    results_total_extended.update({"request_time": request_time, "feeds_available": len(feed_tables)})
    return results_total_extended

