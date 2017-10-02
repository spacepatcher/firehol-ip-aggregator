import traceback

from sqlalchemy.sql import func
from sqlalchemy import exists

from modules.db_core import create_db, FeedTotal
from modules.general import net_is_local, remove_duplicate_dicts


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
    sql = ("UPDATE {table_name} SET {column} = TRUE, added = {added} WHERE ip = '{ip}' AND {column} = FALSE")\
        .format(table_name=table_name, added=func.now(), ip=ip, column=column)
    engine.execute(sql)


def add_record(engine, table_name, ip, column):
    sql = ("INSERT INTO {table_name} (ip, added, {column}) VALUES ('{ip}', {added}, TRUE)")\
        .format(table_name=table_name, column=column, ip=ip, added=func.now())
    engine.execute(sql)


def search_net(engine, table_name, net):
    sql = ("SELECT * FROM {table_name} WHERE ip <<= '{net}'")\
        .format(table_name=table_name, net=net)
    result = engine.execute(sql)
    search_results = []
    for row in result:
        feed_name = []
        for key in row.keys():
            if row[key] and key != "id" and key != "ip" and key != "added":
                feed_name.append(key)
        data = {
            "ip": row["ip"],
            "added": row["added"],
            "feeds": feed_name
        }
        search_results.append(data)
    return search_results


def db_add_data(data):
    try:
        db_session = create_db()
    except Exception as e:
        traceback.print_exc()
        return "Error while db init {}".format(e)
    try:
        for diff_parsed in data:
            for ip in diff_parsed.get("ips"):
                valid_column_name = diff_parsed.get("feed_name").split(".")[0]
                if db_session.query((exists().where(FeedTotal.ip == ip))).scalar():
                    if valid_column_name in get_columns(db_session, FeedTotal.__tablename__):
                        pass
                    else:
                        add_column(db_session, FeedTotal.__tablename__, valid_column_name)
                    modify_field(db_session, FeedTotal.__tablename__, ip, valid_column_name)
                else:
                    if valid_column_name in get_columns(db_session, FeedTotal.__tablename__):
                        pass
                    else:
                        add_column(db_session, FeedTotal.__tablename__, valid_column_name)
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
            if not net_is_local(net):
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
