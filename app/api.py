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
                return "Data validation error in '%s'." % request

        return FeedsAlchemy.db_search_data(list(set(request_list)))

    except AttributeError:

        return "Got an empty request"
