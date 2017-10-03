import hug

from app.modules.db_firehol import db_search


@hug.post("/search")
def search_net(body):
    net_string = body
    net_list = net_string.split(",")
    return db_search(net_list)
