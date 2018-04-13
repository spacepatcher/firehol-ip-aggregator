import hug

from modules.db_feeds import FeedsAlchemy
from modules.general import General


FeedsAlchemy = FeedsAlchemy()
General = General()

General.logger.info("API instance successfully started")


@hug.post("/search")
def search_api(body):
    payload = body.read().decode("utf-8")

    try:
        request_list = payload.split(",")

        for request in request_list:
            if General.validate_request(request):
                pass
            else:
                return {"errors": "Data validation error in '%s'" % request}

        return FeedsAlchemy.db_search(list(set(request_list)))

    except AttributeError:

        return {"errors": "Error while searching occurred"}


@hug.get("/feeds", output=hug.output_format.json, version=1)
def feeds():
    """Retrieve all information about feeds"""

    return FeedsAlchemy.db_feeds()


@hug.get("/feeds/categories", output=hug.output_format.json, version=1)
def feeds_categories():
    """Retrieve all feed categories"""

    return FeedsAlchemy.db_feeds_categories()


@hug.get("/feeds/maintainers", output=hug.output_format.json, version=1)
def feeds_maintainers():
    """Retrieve all feed maintainers"""

    return FeedsAlchemy.db_feeds_maintainers()


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
def maintainers_by_category(category: hug.types.text):
    """Retrieve all maintainers by category"""

    category = category.lower()

    return FeedsAlchemy.db_maintainers_by_category(category)


@hug.get("/ip/bulk/by_category", output=hug.output_format.json, examples="category=reputation", version=1)
def ip_bulk_by_category(category: hug.types.text):
    """Retrieve all IP addresses that are in feeds by feed category"""

    category_lower = category.lower()

    return FeedsAlchemy.db_ip_bulk_by_category(category_lower)
