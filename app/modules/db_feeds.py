import pytz
import netaddr
from datetime import datetime
from sqlalchemy import exc
from sqlalchemy.sql import select, update, exists
from sqlalchemy.dialects.postgresql import insert

from modules.db_core import Alchemy


class FeedsAlchemy(Alchemy):
    def __init__(self):
        super().__init__()

        self.db_session = self.get_db_session()
        self.meta_table = self.get_meta_table_object()

    def db_update_metatable(self, feed_data):
        feed_meta = feed_data.get("feed_meta")

        while True:
            try:
                insert_query = insert(self.meta_table).values(feed_meta) \
                    .on_conflict_do_update(index_elements=["feed_name"],
                                           set_=dict(maintainer=feed_meta.get("maintainer"),
                                                     maintainer_url=feed_meta.get("maintainer_url"),
                                                     list_source_url=feed_meta.get("list_source_url"),
                                                     source_file_date=feed_meta.get("source_file_date"),
                                                     category=feed_meta.get("category"),
                                                     entries=feed_meta.get("entries")))
                self.db_session.execute(insert_query)
                self.db_session.commit()

                break

            except exc.IntegrityError as e:
                self.logger.warning("Warning: {}".format(e))
                self.logger.info("Attempt to update meta table will be made in the next iteration of an infinite loop")
                self.db_session.rollback()

    def db_update_added(self, feed_data):
        feed_table_name = "feed_" + feed_data.get("feed_name")

        try:
            feed_table = self.get_feed_table_object(feed_table_name)
            for ip_group in self.group_by(n=100000, iterable=feed_data.get("added_ip")):
                current_time_db = datetime.now()
                current_time_json = current_time_db.isoformat()

                period = {
                    "added":    current_time_json,
                    "removed":  ""
                }

                for ip in ip_group:
                    if self.db_session.query((exists().where(feed_table.c.ip == ip))).scalar():
                        select_query = select([feed_table.c.timeline]).where(feed_table.c.ip == ip)
                        timeline = self.db_session.execute(select_query).fetchone()[0]
                        timeline.append(period)
                        update_query = update(feed_table).where(feed_table.c.ip == ip).values(last_added=current_time_db,
                                                                                              timeline=timeline)
                        self.db_session.execute(update_query)

                    else:
                        insert_query = insert(feed_table).values(ip=ip,
                                                                 first_seen=current_time_db,
                                                                 last_added=current_time_db,
                                                                 feed_name=feed_data.get("feed_name"),
                                                                 timeline=[period])
                        self.db_session.execute(insert_query)

                self.db_session.commit()

        except Exception as e:
            self.logger.error("Error: {}".format(e))
            self.logger.exception("Can't commit to DB. Rolling back changes...")
            self.db_session.rollback()

        finally:
            self.db_session.close()

    def db_update_removed(self, feed_data):
        feed_table_name = "feed_" + feed_data.get("feed_name")

        try:
            feed_table = self.get_feed_table_object(feed_table_name)

            for ip_group in self.group_by(n=100000, iterable=feed_data.get("removed_ip")):
                current_time_db = datetime.now()
                current_time_json = current_time_db.isoformat()

                for ip in ip_group:
                    if self.db_session.query((exists().where(feed_table.c.ip == ip))).scalar():
                        select_query = select([feed_table.c.timeline]).where(feed_table.c.ip == ip)
                        timeline = self.db_session.execute(select_query).fetchone()[0]
                        period = timeline.pop()
                        period["removed"] = current_time_json
                        timeline.append(period)
                        update_query = update(feed_table).where(feed_table.c.ip == ip).values(last_removed=current_time_db,
                                                                                              timeline=timeline)
                        self.db_session.execute(update_query)

                self.db_session.commit()

        except Exception as e:
            self.logger.error("Error: {}".format(e))
            self.logger.exception("Can't commit to DB. Rolling back changes...")
            self.db_session.rollback()

        finally:
            self.db_session.close()

    def db_search_data(self, net_list, feeds_available=0, requested_count=0, blacklisted_count=0):
        request_time = pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone("Europe/Moscow")).isoformat()
        results_total = dict()
        results_total_extended = dict()

        ignore_columns = [
            "id"
        ]

        try:
            self.metadata.reflect(bind=self.engine)
            feed_tables = [table for table in reversed(self.metadata.sorted_tables) if "feed_" in table.name]
            feeds_available = len(feed_tables)

            for net in net_list:
                results = list()
                requested_count += len(netaddr.IPNetwork(net))

                for feed_table in feed_tables:
                    sql_query = "SELECT * FROM {feed_table_name} f, {meta_table_name} m WHERE f.feed_name = m.feed_name AND f.ip<<='{net}'" \
                        .format(feed_table_name=feed_table.name, meta_table_name=self.meta_table.name, net=net)
                    raw_results = self.db_session.execute(sql_query).fetchall()

                    if raw_results:
                        for item in raw_results:
                            result_dict = dict(zip(item.keys(), item))

                            for column in ignore_columns:
                                result_dict.pop(column)

                            results.append(result_dict)

                results_grouped = self.group_dict_by_key(results, "ip")
                blacklisted_count += len(results_grouped.keys())
                results_grouped_extended = self.extend_result_data(results_grouped)

                results_total.update(results_grouped_extended)

        except Exception as e:
            self.logger.error("Error: {}".format(e))
            self.logger.exception("Error while searching occurred")

        finally:
            self.db_session.close()

        results_total_extended.setdefault("results", results_total)
        results_total_extended.update({
            "request_time":      request_time,
            "feeds_available":   feeds_available,
            "requested_count":   requested_count,
            "blacklisted_count": blacklisted_count
        })

        return results_total_extended
