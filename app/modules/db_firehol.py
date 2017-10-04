import traceback

from modules.db_core import create_db, FeedTotal
from modules.general import validate_input, remove_duplicate_dicts, grouper
from sqlalchemy import exists
from sqlalchemy.sql import func


def add_column(engine, table_name, column):
    sql = ("ALTER TABLE {table_name} ADD column {column} BOOLEAN DEFAULT FALSE")\
        .format(table_name=table_name, column=column)
    engine.execute(sql)


def get_columns(engine, table_name):
    sql = ("SELECT * FROM {table_name} LIMIT 0")\
        .format(table_name=table_name)
    columns = engine.execute(sql)._metadata.keys
    return columns


def modify_field(engine, table_name, ip, column):
    sql = ("UPDATE {table_name} SET {column} = TRUE, last_added = {last_added} WHERE ip = '{ip}' AND {column} = FALSE")\
        .format(table_name=table_name, last_added=func.now(), ip=ip, column=column)
    engine.execute(sql)


def add_record(engine, table_name, ip, column):
    sql = ("INSERT INTO {table_name} (ip, last_added, {column}) VALUES ('{ip}', {last_added}, TRUE)")\
        .format(table_name=table_name, column=column, ip=ip, last_added=func.now())
    engine.execute(sql)


def search_net(engine, table_name, net):
    sql = ("SELECT * FROM {table_name} WHERE ip <<= '{net}'")\
        .format(table_name=table_name, net=net)
    result = engine.execute(sql)
    search_results = []
    for row in result:
        feed_name = []
        for key in row.keys():
            if row[key] and key != "id" and key != "ip" and key != "last_added":
                feed_name.append(key)
        data = {
            "ip": row["ip"],
            "last_added": row["last_added"],
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
                if db_session.query((exists().where(FeedTotal.ip == ip))).scalar():
                    modify_field(db_session, FeedTotal.__tablename__, ip, valid_column_name)
                else:
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


def db_search(net_input):
    search_result_total = []
    search_result_unique = []
    net_input = list(set(net_input))
    try:
        db_session = create_db()
    except Exception as e:
        traceback.print_exc()
        return "Error while db init {}".format(e)
    try:
        for net in net_input:
            if validate_input(net):
                search_net_result = search_net(db_session, FeedTotal.__tablename__, net)
                if search_net_result:
                    search_result_total.extend(search_net_result)
        search_result_unique = remove_duplicate_dicts(search_result_total)
    except Exception as e:
        traceback.print_exc()
        return "Error: {}".format(e)
    finally:
        db_session.close()
        return search_result_unique
