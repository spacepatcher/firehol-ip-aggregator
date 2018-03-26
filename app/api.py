import hug
from falcon import HTTP_500

from modules.db_feeds import FeedsAlchemy
from modules.general import General


FeedsAlchemy = FeedsAlchemy()
General = General()

General.logger.info("API instance successfully started")


@hug.post("/search", output=hug.output_format.json, version=1)
def search(body):
    """Search IP in all available feeds. Input: a string containing IP addresses separated by commas in HTTP POST body"""

    payload = body.read().decode("utf-8")

    try:
        request_list = payload.split(",")

        for request in request_list:
            if General.validate_request(request):
                pass
            else:
                return {"errors": "Data validation error in '%s'" % request}

        return FeedsAlchemy.db_search_data(list(set(request_list)))

    except AttributeError:

        return {"errors": "Error while searching occurred"}


@hug.get("/feeds", output=hug.output_format.json, version=1)
def categories():
    """Retrieve all information about feeds"""

    return FeedsAlchemy.db_feeds()


@hug.get("/feeds/categories", output=hug.output_format.json, version=1)
def categories():
    """Retrieve all feed categories"""

    return FeedsAlchemy.db_categories()


@hug.get("/feeds/maintainers", output=hug.output_format.json, version=1)
def maintainers():
    """Retrieve all feed maintainers"""

    return FeedsAlchemy.db_all_maintainers()


@hug.get("/feed/info", output=hug.output_format.json, examples="feed_name=hphosts_psh", version=1)
def feed_info(feed_name: hug.types.text):
    """Retrieve all available information about the feed by its name"""

    feed_name_lower = feed_name.lower()

    return FeedsAlchemy.db_feed_info(feed_name_lower)


@hug.get("/maintainer/info", output=hug.output_format.json, examples="maintainer=hpHosts", version=1)
def maintainer_info(maintainer: hug.types.text):
    """Retrieve all available information about the maintainer by its name"""

    maintainer_lower = maintainer.lower()

    return FeedsAlchemy.db_maintainer_info(maintainer_lower)


@hug.get("/maintainers/by_category", output=hug.output_format.json, examples="category=spam", version=1)
def maintainer_info(category: hug.types.text):
    """Retrieve all maintainers by category"""

    category = category.lower()

    return FeedsAlchemy.db_maintainers(category)


@hug.get("/ip/bulk/by_category", output=hug.output_format.json, examples="category=reputation", version=1)
def ip_bulk(category: hug.types.text):
    """Retrieve all IP addresses that are in feeds by feed category"""

    category_lower = category.lower()

    return FeedsAlchemy.db_ip_bulk(category_lower)


# @hug.get("/ip/bulk/by_category/current", output=hug.output_format.json, examples="category=abuse", version=1)
# def ip_bulk_current(category: hug.types.text):
#     """Retrieve all IP addresses that are currently in feeds by feed category"""
#
#     category_lower = category.lower()
#
#     return FeedsAlchemy.db_ip_bulk_current(category_lower)
