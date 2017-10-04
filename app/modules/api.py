import hug

from modules.db_firehol import db_search
from modules.general import validate_input_item


@hug.post("/search")
def search_api(body):
    input_list = body.split(",")
    for item in input_list:
        if validate_input_item(item):
            pass
        else:
            return "Wrong input"
    net_list = list(set(input_list))
    return db_search(net_list)
