import sys
import git
import os
import traceback
import unidiff
import re
from modules.utils import load_cfg, read_file, limit_memory, normalize_ip4, net_is_local, remove_duplicate_dicts
from sqlalchemy import exists
from db_core import create_db, FeedTotal
from modules.firehol.db import add_column, get_columns, modify_field, add_record, search_net


added_ip_re = re.compile(r"(?<=\+)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?=\n)")
added_net_re = re.compile(r"(?<=\+)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})(?=\n)")
ip_re = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
net_re = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}")
not_periodic_feed_re = re.compile(r"^(?!.*_\d{1,3}d(\.ipset|\.netset)).*(\.ipset|\.netset)$")
uniq_ips_re = re.compile(r"(?<=\ )(\d*)(?= unique IPs)")

# config = load_cfg(os.path.join(os.path.dirname(__file__), "conf/config.json"))
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_path = "%s/%s" % (current_dir, "data/firehol")
firehol_ipsets_git = "https://github.com/firehol/blocklist-ipsets.git"
unique_ips_limit = 2000000


def sync_git_repo():
    if not os.path.exists(repo_path):
        diff_list = []
        os.makedirs(repo_path)
        git.Repo.clone_from(url=firehol_ipsets_git, to_path=repo_path)
        try:
            firehol_repo = git.cmd.Git(working_dir=repo_path)
            firehol_repo.checkout("master")
        except git.GitCommandError as e:
            traceback.print_exc()
            return "git error {}".format(e)
        for file_path in get_proper_feed_files(path_to_search=repo_path):
            diff = parse_feed_file(feed_file=file_path)
            if diff:
                diff_list.append(diff)
        sync_database_added(diff_list=diff_list)
        return
    else:
        try:
            firehol_repo = git.cmd.Git(working_dir=repo_path)
            firehol_repo.checkout("master")
        except git.GitCommandError as e:
            return "git error {}".format(e)
        try:
            firehol_repo.fetch("origin")
            diff_stdout_raw = firehol_repo.execute(command=["git", "diff", "master", "origin/master"],
                                                   stdout_as_string=True)
            diff_stdout = diff_stdout_raw.split("\n")
            try:
                parsed_diff = unidiff.PatchSet(diff_stdout)
            except unidiff.UnidiffParseError as e:
                return "diff parse error {}".format(e)
            firehol_repo.execute(command=["git", "reset", "--hard", "origin/master"])
            firehol_repo.merge()
            if parsed_diff.added_files:
                diff_list = []
                for added_file in parsed_diff.added_files:
                    filename_abs = "%s/%s" % (repo_path, added_file.target_file[2:])
                    if validate_feed(feed_file_abs=filename_abs, unique_ips_limit=unique_ips_limit):
                        diff = parse_feed_file(feed_file=filename_abs)
                        if diff:
                            diff_list.append(diff)
                sync_database_added(diff_list=diff_list)
            if parsed_diff.modified_files:
                diff_list = []
                for change_in_file in parsed_diff.modified_files:
                    filename_abs = "%s/%s" % (repo_path, change_in_file.target_file[2:])
                    if validate_feed(feed_file_abs=filename_abs, unique_ips_limit=unique_ips_limit):
                        diff = get_diff_data(dif_data=change_in_file, filename_abs=filename_abs)
                        if diff:
                            diff_list.append(diff)
                sync_database_added(diff_list=diff_list)
            return
        except git.GitCommandError as e:
            return "git error {}".format(e)


def parse_feed_file(feed_file):
    filename = feed_file.split('/').pop()
    added_ip = []
    removed_ip = []
    added_net = []
    removed_net = []
    data_strings = read_file(filename=feed_file)
    for data_string in data_strings:
        if "#" in data_string:
            pass
        else:
            ip_match = ip_re.search(data_string)
            net_match = net_re.search(data_string)
            if ip_match:
                added_ip.append(ip_match.group())
            if net_match:
                added_net.append(net_match.group())
    diff = {
        "filename": filename,
        "added_ip": added_ip,
        "removed_ip": removed_ip,
        "added_net": added_net,
        "removed_net": removed_net
    }
    return diff


def get_diff_data(dif_data, filename_abs):
    filename = filename_abs.split('/').pop()
    added_ip = []
    added_net = []
    added_ip_match = added_ip_re.findall(str(dif_data))
    added_net_match = added_net_re.findall(str(dif_data))
    if added_ip_match:
        added_ip.extend(added_ip_match)
    if added_net_match:
        added_net.extend(added_net_match)
    diff = {
        "filename": filename,
        "added_ip": added_ip,
        "added_net": added_net
    }
    return diff


def sync_database_added(diff_list):
    data_to_add = []
    for diff in diff_list:
        ip_list = normalize_ip4(ip_list_raw=diff.get("added_ip"))
        net_list = normalize_ip4(ip_list_raw=diff.get("added_net"))
        ip_list_total = ip_list + net_list
        if ip_list_total:
            diff_parsed = {
                "ips": ip_list_total,
                "feed_name": diff.get("filename")
            }
            data_to_add.append(diff_parsed)
    db_add_data(data=data_to_add)
    return


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
        return


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


def get_proper_feed_files(path_to_search):
    for file in os.listdir(path_to_search):
        file_path_abs = os.path.join(path_to_search, file)
        suitable_feed = validate_feed(feed_file_abs=file_path_abs, unique_ips_limit=unique_ips_limit)
        if suitable_feed:
            yield file_path_abs


def validate_feed(feed_file_abs, unique_ips_limit):
    suitable = False
    if "firehol_" in feed_file_abs:
        suitable = False
        return suitable
    not_periodic_feed = not_periodic_feed_re.search(feed_file_abs)
    if not not_periodic_feed:
        suitable = False
        return suitable
    data_strings = read_file(filename=feed_file_abs)
    for data_string in data_strings:
        unique_ips_count = uniq_ips_re.search(data_string)
        if unique_ips_count:
            if int(unique_ips_count.group(1)) > unique_ips_limit:
                suitable = False
            else:
                suitable = True
            break
        else:
            pass
    return suitable


if __name__ == "__main__":
    limit_memory(maxsize_g=12)
    sync_git_repo()
    sys.exit()
