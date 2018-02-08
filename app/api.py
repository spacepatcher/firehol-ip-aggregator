import hug

from modules.db_feeds import FeedsAlchemy
from modules.general import General


FeedsAlchemy = FeedsAlchemy()
General = General()


@hug.post("/search")
def search_api(body):
    try:
        request_list = body.split(",")

        for request in request_list:
            if General.validate_request(request):
                pass
            else:
                return "Data validation error in '%s'." % request

        return FeedsAlchemy.db_search_data(list(set(request_list)))

    except AttributeError:

        return "Got an empty request"
