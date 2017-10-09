import traceback

from modules.db_core import create_db, FeedTotal
from modules.general import grouper
from sqlalchemy.sql import func


def add_column(engine, table_name, column):
    sql = "ALTER TABLE {table_name} ADD column {column} BOOLEAN DEFAULT FALSE"\
        .format(table_name=table_name, column=column)
    engine.execute(sql)


def get_columns(engine, table_name):
    sql = "SELECT * FROM {table_name} LIMIT 0"\
        .format(table_name=table_name)
    columns = engine.execute(sql)._metadata.keys
    return columns


def add_record(db_session, table_name, ip, column):
    sql = "INSERT INTO {table_name} (ip, last_added, {column}) VALUES ('{ip}', {last_added}, TRUE) ON CONFLICT (ip) DO UPDATE SET {column} = TRUE, last_added = {last_added}"\
        .format(table_name=table_name, column=column, ip=ip, last_added=func.now())
    db_session.execute(sql)


def search_net(db_session, table_name, net):
    sql = "SELECT * FROM {table_name} WHERE ip <<= '{net}'"\
        .format(table_name=table_name, net=net)
    result = db_session.execute(sql)
    search_results = []
    for row in result:
        feed_name = []
        for key in row.keys():
            if row.get("key") and key != "id" and key != "ip" and key != "last_added":
                feed_name.append(key)
        data = {
            "ip": row.get("ip"),
            "last_added": row.get("last_added"),
            "feeds": feed_name
        }
        search_results.append(data)
    return search_results


def db_add_data(data_to_add):
    try:
        db_session = create_db()
    except Exception as e:
        traceback.print_exc()
        return "Error while db init {}".format(e)
    try:
        valid_column_name = data_to_add.get("feed_name").split(".")[0]
        if valid_column_name not in get_columns(db_session, FeedTotal.__tablename__):
            add_column(db_session, FeedTotal.__tablename__, valid_column_name)
            db_session.commit()
        for ip_group in grouper(n=100000, iterable=data_to_add.get("added_ip")):
            for ip in ip_group:
                add_record(db_session, FeedTotal.__tablename__, ip, valid_column_name)
            db_session.commit()
        return "Successfully"
    except Exception as e:
        traceback.print_exc()
        print("Error: {}".format(e))
        db_session.rollback()
        raise Exception("Can't commit to DB. Rolling back changes..")
    finally:
        db_session.close()


def db_search(net_list):
    search_result_total = []
    try:
        db_session = create_db()
    except Exception as e:
        traceback.print_exc()
        return "Error while db init {}".format(e)
    try:
        for net in net_list:
            search_net_result = search_net(db_session, FeedTotal.__tablename__, net)
            if search_net_result:
                search_result_total.extend(search_net_result)
    except Exception as e:
        traceback.print_exc()
        return "Error: {}".format(e)
    finally:
        db_session.close()
        return search_result_total
