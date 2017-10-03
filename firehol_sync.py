import os
import sys
import traceback

import git
import unidiff

from modules.general import read_file, limit_memory, normalize_net4, load_cfg
from modules.general import added_ip_re, added_net_re, ip_re, net_re, not_periodic_feed_re, uniq_ips_re
from modules.db_firehol import db_add_data


repo_path = "%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "git_data/firehol")
firehol_ipsets_git = load_cfg("conf/config.json").get("firehol_ipsets_git")
unique_ips_limit = load_cfg("conf/config.json").get("unique_ips_limit")


def sync_git_repo():
    if not os.path.exists(repo_path):
        os.makedirs(repo_path)
        git.Repo.clone_from(url=firehol_ipsets_git, to_path=repo_path)
        try:
            firehol_repo = git.cmd.Git(working_dir=repo_path)
            firehol_repo.checkout("master")
        except git.GitCommandError as e:
            traceback.print_exc()
            return "git error {}".format(e)
        for filename_abs in get_proper_feed_files(path_to_search=repo_path):
            new_data = parse_feed_file(feed_file=filename_abs)
            if new_data:
                db_add_data(new_data)
    else:
        try:
            firehol_repo = git.cmd.Git(working_dir=repo_path)
            firehol_repo.checkout("master")
        except git.GitCommandError as e:
            traceback.print_exc()
            return "git error {}".format(e)
        try:
            firehol_repo.fetch("origin")
            diff_stdout = firehol_repo.execute(command=["git", "diff", "master", "origin/master"],
                                               stdout_as_string=True).split("\n")
            try:
                parsed_diff = unidiff.PatchSet(diff_stdout)
            except unidiff.UnidiffParseError as e:
                return "diff parse error {}".format(e)
            firehol_repo.execute(command=["git", "reset", "--hard", "origin/master"])
            firehol_repo.merge()
            if parsed_diff.added_files:
                for added_file in parsed_diff.added_files:
                    filename_abs = "%s/%s" % (repo_path, added_file.target_file[2:])
                    if validate_feed(feed_file_abs=filename_abs, unique_ips_limit=unique_ips_limit):
                        new_data = parse_feed_file(feed_file=filename_abs)
                        if new_data:
                            db_add_data(new_data)
            if parsed_diff.modified_files:
                for change_in_file in parsed_diff.modified_files:
                    print(change_in_file)
                    print(type(change_in_file))
                    filename_abs = "%s/%s" % (repo_path, change_in_file.target_file[2:])
                    if validate_feed(feed_file_abs=filename_abs, unique_ips_limit=unique_ips_limit):
                        diff_data = get_diff_data(diff_data=change_in_file, filename_abs=filename_abs)
                        if diff_data:
                            db_add_data(diff_data)
        except git.GitCommandError as e:
            return "git error {}".format(e)


def parse_feed_file(feed_file):
    feed_name = feed_file.split('/').pop()
    added_ip = []
    added_net = []
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
                added_net.extend(normalize_net4(net_match.group()))
    diff = {
        "feed_name": feed_name,
        "added_ip": added_ip + added_net
    }
    return diff


def get_diff_data(diff_data, filename_abs):
    feed_name = filename_abs.split('/').pop()
    added_ip = []
    added_net = []
    added_ip_match = added_ip_re.findall(str(diff_data))
    added_net_match = added_net_re.findall(str(diff_data))
    if added_ip_match:
        added_ip.extend(added_ip_match)
    if added_net_match:
        for added_net_item in added_net_match:
            added_net.extend(normalize_net4(added_net_item))
    diff = {
        "feed_name": feed_name,
        "added_ip": added_ip + added_net
    }
    return diff


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
