import hug

from modules.db_firehol import db_search_data
from modules.general import General

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
        return db_search_data(list(set(request_list)))
    except AttributeError:
        return "Got an empty request"

