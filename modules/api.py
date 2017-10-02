from modules.firehol.firehol_feed import db_search
import hug


@hug.post("/search")
def search_net(body):
    net_string = body.readline().decode()
    net_list = net_string.split(",")
    return db_search(net_list)
