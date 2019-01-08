import datetime
from netaddr import IPAddress
from pymongo import MongoClient, ASCENDING

from modules.general import General


class FeedsStorage(General):
    def __init__(self):
        super().__init__()

        self.connection_string = "mongodb://%s:%s@%s/" \
                                 % (self.database_user, self.database_password, self.database_address)

        self.client = MongoClient(self.connection_string)
        self.db = self.client[self.database_name]
        self.feeds_collection = self.db["feeds"]

        self.document = {
            "ip": None,
            "timeline": [],
            "feed_meta": {
                "feed_name": None,
                "maintainer": None,
                "maintainer_url": None,
                "list_source_url": None,
                "source_file_date": None,
                "category": None,
                "entries": None
            }
        }

    def _create_index(self, collection):
        collection.create_index([("ip", ASCENDING),
                                 ("feed_meta.feed_name", ASCENDING)],
                                name="search")

        collection.create_index([("feed_meta.category", ASCENDING)],
                                name="metadata")

    def _save_added(self, current_time, ip_items, metadata):
        timeline = {
            "added": current_time,
            "removed": None
        }

        for ip in ip_items:
            ip_int = int(IPAddress(ip))

            self.feeds_collection.update_one(
                {
                    "ip": ip_int,
                    "feed_meta.feed_name": metadata.get("feed_name")
                },
                {
                    "$push": {
                        "timeline": timeline
                    },
                    "$set": {
                        "feed_meta": metadata
                    }
                },
                upsert=True
            )

    def _save_removed(self, current_time, ip_items, metadata):
        for ip in ip_items:
            ip_int = int(IPAddress(ip))

            self.feeds_collection.update_one(
                {
                    "ip": ip_int,
                    "feed_meta.feed_name": metadata.get("feed_name"),
                    "timeline.removed": None
                },
                {
                    "$set": {
                        "feed_meta": metadata,
                        "timeline.$.removed": current_time
                    }
                }
            )

    def save(self, feed_data):
        self._create_index(self.feeds_collection)

        current_time = datetime.datetime.now()

        self.logger.info(feed_data.get("feed_meta"))
        self.logger.info(feed_data.get("added_ip"))
        self.logger.info(feed_data.get("removed_ip"))

        if feed_data.get("added_ip"):
            for ip_added_group in self.group_by(n=100000, iterable=feed_data.get("added_ip")):
                self._save_added(current_time, ip_added_group, feed_data.get("feed_meta"))

        if feed_data.get("removed_ip"):
            for ip_removed_group in self.group_by(n=100000, iterable=feed_data.get("removed_ip")):
                self._save_removed(current_time, ip_removed_group, feed_data.get("feed_meta"))
