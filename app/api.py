import hug

from modules.db_firehol import db_search_data
from modules.general import General

General = General()


@hug.post("/search")
def search_api(body):
    input_list = body.split(",")
    for input_item in input_list:
        if General.validate_input_item(input_item):
            pass
        else:
            return "Data validation error in '%s'." % input_item
    net_list = list(set(input_list))
    return db_search_data(net_list)
