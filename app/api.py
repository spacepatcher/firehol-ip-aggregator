import hug

from modules.db_feeds import FeedsAlchemy
from modules.general import General


FeedsAlchemy = FeedsAlchemy()
General = General()


@hug.post("/search")
def search_api(body):
    try:
        request_list = body.split(",")
        for input_item in request_list:
            if General.validate_input_item(input_item):
                pass
            else:
                return "Data validation error in '%s'." % input_item
        return FeedsAlchemy.db_search_data(list(set(request_list)))
    except AttributeError:
        return "Got an empty request"
