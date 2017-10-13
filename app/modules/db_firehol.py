import traceback

from modules.db_core import create_db_session
from modules.general import General
from sqlalchemy.sql import func

General = General()


def db_add_data(data_to_add, feed_name):
    table_name = "feed_" + feed_name
    try:
        db_session = create_db_session("feeds", table_name)
    except Exception as e:
        traceback.print_exc()
        return "Error while db init {}".format(e)
    try:
        for ip_group in General.group_by(n=100000, iterable=data_to_add.get("added_ip")):
            for ip in ip_group:
                insert_sql_query = "INSERT INTO {table_name} (ip, first_seen) VALUES ('{ip}', {first_seen}) ON CONFLICT (ip) DO UPDATE SET last_added = {last_added}"\
                    .format(table_name=table_name, ip=ip, first_seen=func.now(), last_added=func.now())
                db_session.execute(insert_sql_query)
            db_session.commit()
    except Exception as e:
        traceback.print_exc()
        print("Error: {}".format(e))
        db_session.rollback()
        raise Exception("Can't commit to DB. Rolling back changes..")
    finally:
        db_session.close()
