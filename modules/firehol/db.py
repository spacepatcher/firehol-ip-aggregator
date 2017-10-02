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
