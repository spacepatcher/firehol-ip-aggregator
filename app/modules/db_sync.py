import datetime
import pytz
from netaddr import IPAddress, IPNetwork
from pymongo import MongoClient, ASCENDING

from modules.general import General


class FeedsStorage(General):
    def __init__(self):
        super().__init__()

        self.connection_string = "mongodb://%s:%s@%s/" \
                                 % (self.database_user, self.database_password, self.database_address)
        self.collection_name = "feeds"

        self.client = MongoClient(self.connection_string)
        self.db = self.client[self.database_name]
        self.feeds_collection = self.db[self.collection_name]

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
        collection.create_index(
            [
                ("ip", ASCENDING),
                ("feed_meta.feed_name", ASCENDING)
            ],
            name="search"
        )

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
                        "timeline.$.removed": current_time
                    }
                }
            )

    def _update_meta(self, metadata):
        self.feeds_collection.update_many(
            {
                "feed_meta.feed_name": metadata.get("feed_name")
            },
            {
                "$set": {
                    "feed_meta": metadata
                }
            }
        )

    def _process_result(self, found_items, blacklisted_count=0, currently_blacklisted_count=0):
        bunched = dict()
        processed_results = list()

        ignored_fields = ["_id"]

        for item in found_items:
            for field in ignored_fields:
                item.pop(field)

            first_seen = item.get("timeline")[0].get("added")
            last_added = item.get("timeline")[-1].get("added")
            last_removed = item.get("timeline")[-1].get("removed")

            if not last_removed:
                current_status = "present"

            else:
                current_status = "absent"

            extended_item = {
                "ip":               str(IPAddress(item.get("ip"))),
                "feed_name":        item.get("feed_meta").get("feed_name"),
                "category":         item.get("feed_meta").get("category"),
                "maintainer":       item.get("feed_meta").get("maintainer"),
                "maintainer_url":   item.get("feed_meta").get("maintainer_url"),
                "list_source_url":  item.get("feed_meta").get("list_source_url"),
                "source_file_date": item.get("feed_meta").get("source_file_date"),
                "entries":          item.get("feed_meta").get("entries"),
                "first_seen":       first_seen,
                "last_added":       last_added,
                "last_removed":     last_removed,
                "current_status":   current_status,
                "timeline":         item.get("timeline")
            }

            bunching_element = extended_item.pop("ip", None)
            bunched.setdefault(bunching_element, []).append(extended_item)

        for bunching_element, bunched_value in bunched.items():
            blacklisted_count += 1
            currently_blacklisted = False

            for item in bunched_value:
                if item.get("current_status", None) == "present":
                    currently_blacklisted = True
                    currently_blacklisted_count += 1

                    break

            processed_results.append(
                {
                    "ip": bunching_element,
                    "categories": list(set([dictionary.get("category") for dictionary in bunched[bunching_element]])),
                    "first_seen": sorted(list(set([dictionary.get("first_seen") for dictionary in bunched[bunching_element]])))[0],
                    "last_added": sorted(list(set([dictionary.get("last_added") for dictionary in bunched[bunching_element]])), reverse=True)[0],
                    "hits_count": len(bunched_value),
                    "currently_blacklisted": currently_blacklisted,
                    "hits": bunched.get(bunching_element, None)
                }
            )

        return processed_results, blacklisted_count, currently_blacklisted_count

    def save(self, feed_data):
        self._create_index(self.feeds_collection)

        current_time = datetime.datetime.now()

        if feed_data.get("added_ip"):
            for ip_added_group in self.group_by(n=100000, iterable=feed_data.get("added_ip")):
                self._save_added(current_time, ip_added_group, feed_data.get("feed_meta"))

        if feed_data.get("removed_ip"):
            for ip_removed_group in self.group_by(n=100000, iterable=feed_data.get("removed_ip")):
                self._save_removed(current_time, ip_removed_group, feed_data.get("feed_meta"))

        self._update_meta(feed_data.get("feed_meta"))

    def search(self, network_list, requested_count=0, blacklisted_count=0, currently_blacklisted_count=0):
        request_time = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(pytz.timezone("Europe/Moscow")).isoformat()
        result = dict()
        processed = list()

        collection_records = self.db.command("collstats", self.collection_name).get("count")

        for network in network_list:
            network_obj = IPNetwork(network)
            requested_count += len(network_obj)

            found_items = self.feeds_collection.find(
                {
                    "ip": {
                        "$gte": int(network_obj[0]),
                        "$lte": int(network_obj[-1])
                    }
                }
            )

            if found_items:
                processed, blacklisted_count, currently_blacklisted_count = self._process_result(found_items)

        result.update(
            {
                "request_time":                request_time,
                "records_count":               collection_records,
                "requested_count":             requested_count,
                "blacklisted_count":           blacklisted_count,
                "currently_blacklisted_count": currently_blacklisted_count,
                "results":                     processed
            }
        )

        return result
