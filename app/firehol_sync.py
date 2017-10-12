import os
import traceback
import time
from multiprocessing import Pool
import logging
import pickle

import git
import unidiff
from modules.db_firehol import db_add_data
from modules.general import General

General = General()

logger = logging.getLogger(__name__)
formatter = logging.basicConfig(filename=General.log_path, level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(filename)s] %(funcName)s: %(message)s")


class SyncGit():
    def clone_from_remote(self):
        logger.info("Cloning Firehol repo from remote origin")
        os.makedirs(General.repo_path)
        git.Repo.clone_from(url=General.firehol_ipsets_git, to_path=General.repo_path)
        try:
            firehol_repo = git.cmd.Git(working_dir=General.repo_path)
            firehol_repo.checkout("master")
        except git.GitCommandError as e:
            traceback.print_exc()
            return "git error {}".format(e)
        logger.info("Successfully cloned Firehol repo from remote origin")

    def fetch_diff(self):
        logger.info("Fetching diff from remote origin")
        try:
            firehol_repo = git.cmd.Git(working_dir=General.repo_path)
            firehol_repo.checkout("master")
        except git.GitCommandError as e:
            traceback.print_exc()
            return "git error {}".format(e)
        try:
            firehol_repo.fetch("origin")
            diff_stdout = firehol_repo.execute(command=["git", "diff", "master", "origin/master"], stdout_as_string=True).split("\n")
            try:
                diff = unidiff.PatchSet(diff_stdout)
            except unidiff.UnidiffParseError as e:
                return "diff parse error {}".format(e)
            firehol_repo.execute(command=["git", "reset", "--hard", "origin/master"])
            firehol_repo.merge()
        except git.GitCommandError as e:
            return "git error {}".format(e)
        logger.info("Successfully fetched diff from remote origin")
        return diff

    def get_feed_files(self):
        feed_files = list()
        for feed_file in os.listdir(General.repo_path):
            feed_files.append(os.path.join(General.repo_path, feed_file))
        return feed_files

    def validate_feed(self, feed_file_path):
        unique_ips_count = None
        if not ".ipset" or ".netset" in feed_file_path:
            return False
        if not General.not_periodic_feed_re.search(feed_file_path):
            return False
        for data_string in General.read_file(feed_file_path):
            if General.uniq_ips_re.search(data_string):
                unique_ips_count = int(General.uniq_ips_re.search(data_string).group(1))
                break
            else:
                unique_ips_count = None
        if unique_ips_count and unique_ips_count > General.unique_ips_limit:
            return False
        return True

    def parse_feed_file(self, feed_file):
        feed_name = feed_file.split('/').pop()
        new_ip = []
        new_net = []
        data_strings = General.read_file(filename=feed_file)
        for data_string in data_strings:
            if "#" in data_string:
                pass
            else:
                if General.ip_re.search(data_string):
                    new_ip.append(General.ip_re.search(data_string).group())
                elif General.net_re.search(data_string):
                    new_net.extend(General.normalize_net4(General.net_re.search(data_string).group()))
        new_data = {
            "feed_name": feed_name,
            "added_ip": new_ip + new_net
        }
        return new_data

    def get_diff_data(self, diff_data, filename_path):
        feed_name = filename_path.split('/').pop()
        added_ip = []
        for ip_item in General.added_ip_re.finditer(str(diff_data)):
            added_ip.append(ip_item.group())
        for net_item in General.added_net_re.finditer(str(diff_data)):
            added_ip.extend(General.normalize_net4(net_item.group()))
        diff_data = {
            "feed_name": feed_name,
            "added_ip": added_ip
        }
        return diff_data


SyncGit = SyncGit()


def sync_with_db_new(feed_path):
    if SyncGit.validate_feed(feed_path):
        new_data = SyncGit.parse_feed_file(feed_path)
        if new_data.get("added_ip"):
            logger.info("Found %d new data item(s) in new file %s" % (len(new_data.get("added_ip")), feed_path))
            db_add_data(new_data, new_data.get("feed_name"))


def sync_with_db_diff(diff_serialized):
    diff = pickle.loads(diff_serialized)
    modified_feed_path = "%s/%s" % (General.repo_path, diff.target_file[2:])
    if SyncGit.validate_feed(modified_feed_path):
        diff_data = SyncGit.get_diff_data(diff, modified_feed_path)
        if diff_data.get("added_ip"):
            logger.info("Found %d new data item(s) in diff for file %s" % (len(diff_data.get("added_ip")), modified_feed_path))
            db_add_data(diff_data, diff_data.get("feed_name"))


if __name__ == "__main__":
    period = 3600 * int(General.sync_period_h)
    while True:
        logger.info("Started sync_git_repo()")
        repo_path_exists = os.path.exists(General.repo_path)
        if not repo_path_exists:
            SyncGit.clone_from_remote()
            feed_files_path_list = SyncGit.get_feed_files()
            try:
                pool = Pool(processes=General.get_cpu_count())
                pool.map(sync_with_db_new, feed_files_path_list)
                pool.close()
                pool.join()
            except Exception as e:
                logger.exception("Error in multiprocessing occurred")
        else:
            diff = SyncGit.fetch_diff()
            if diff.added_files:
                logger.info("After fetching found %d new file(s)" % len(diff.added_files))
                new_feeds_path = ["%s/%s" % (General.repo_path, added_files.target_file[2:]) for added_files in diff.added_files]
                try:
                    pool = Pool(processes=General.get_cpu_count())
                    pool.map(sync_with_db_new, new_feeds_path)
                    pool.close()
                    pool.join()
                except Exception as e:
                    logger.exception("Error in multiprocessing occurred")
            if diff.modified_files:
                logger.info("After fetching found %d modified file(s)" % len(diff.modified_files))
                modified_feeds_serialized = [pickle.dumps(modified_files) for modified_files in diff.modified_files]
                try:
                    pool = Pool(processes=General.get_cpu_count())
                    pool.map(sync_with_db_diff, modified_feeds_serialized)
                    pool.close()
                    pool.join()
                except Exception as e:
                    logger.exception("Error in multiprocessing occurred")
        logger.info("Sleep for %d hour(s)" % (period / 3600))
        time.sleep(period)
