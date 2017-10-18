import os
import traceback
import time
from multiprocessing import Pool
import pickle

import git
import unidiff
from modules.db_firehol import db_add_data
from modules.general import General


class SyncGit(General):
    def __init__(self):
        super().__init__()

    def clone_from_remote(self):
        self.logger.info("Cloning Firehol repo from remote origin")
        os.makedirs(self.repo_path)
        git.Repo.clone_from(self.firehol_ipsets_git, self.repo_path)
        try:
            firehol_repo = git.cmd.Git(self.repo_path)
            firehol_repo.checkout("master")
        except git.GitCommandError as e:
            self.logger.exception("GitCommandError occurred")
        self.logger.info("Successfully cloned Firehol repo from remote origin")
        return "Successfully"

    def fetch_diff(self):
        self.logger.info("Fetching diff from remote origin")
        try:
            firehol_repo = git.cmd.Git(self.repo_path)
            firehol_repo.checkout("master")
        except git.GitCommandError as e:
            self.logger.exception("GitCommandError occurred")
        try:
            firehol_repo.fetch("origin")
            diff_stdout = firehol_repo.execute(["git", "diff", "master", "origin/master"], True).split("\n")
            try:
                diff = unidiff.PatchSet(diff_stdout)
            except unidiff.UnidiffParseError as e:
                self.logger.exception("UnidiffParseError occurred")
            firehol_repo.execute(["git", "reset", "--hard", "origin/master"])
            firehol_repo.merge()
        except git.GitCommandError as e:
            self.logger.exception("GitCommandError occurred")
        self.logger.info("Successfully fetched diff from remote origin")
        return diff

    def validate_feed(self, feed_file_path):
        unique_ips_count = None
        if not ".ipset" or ".netset" in feed_file_path:
            return False
        if not self.not_periodic_feed_re.search(feed_file_path):
            return False
        for data_string in self.read_file(feed_file_path):
            if self.uniq_ips_re.search(data_string):
                unique_ips_count = int(self.uniq_ips_re.search(data_string).group(1))
                break
            else:
                unique_ips_count = None
        if unique_ips_count and unique_ips_count > self.unique_ips_limit:
            return False
        return True

    def get_meta_info(self, feed_path):
        meta = dict()
        data_strings = self.read_file(feed_path)
        for index, data_string in enumerate(data_strings):
            if "#" in data_string:
                if index == 1:
                    meta.update({"feed_name": data_string.split("# ")[1]})
                if "Maintainer URL" in data_string:
                    meta.update({"maintainer_url": data_string.split(": ")[1]})
                elif "Maintainer" in data_string:
                    meta.update({"maintainer": data_string.split(": ")[1]})
                if "List source URL" in data_string:
                    meta.update({"list_source_url": data_string.split(": ")[1]})
                if "Source File Date" in data_string:
                    meta.update({"source_file_date": data_string.split(": ")[1]})
                if "Category" in data_string:
                    meta.update({"category": data_string.split(": ")[1]})
                if "Entries" in data_string:
                    meta.update({"entries": data_string.split(": ")[1]})
            else:
                break
        return meta

    def parse_feed_file(self, feed_path):
        new_ip = list()
        new_net = list()
        meta = self.get_meta_info(feed_path)
        data_strings = self.read_file(feed_path)
        for index, data_string in enumerate(data_strings):
            if self.ip_re.search(data_string):
                new_ip.append(self.ip_re.search(data_string).group())
            elif self.net_re.search(data_string):
                new_net.extend(self.normalize_net4(self.net_re.search(data_string).group()))
        feed_data = {
            "feed_name": meta.get("feed_name"),
            "added_ip": new_ip + new_net,
            "feed_meta": meta
        }
        return feed_data

    def get_diff_data(self, diff_data, modified_feed_path):
        added_ip = list()
        meta = self.get_meta_info(modified_feed_path)
        for ip_item in self.added_ip_re.finditer(str(diff_data)):
            added_ip.append(ip_item.group())
        for net_item in self.added_net_re.finditer(str(diff_data)):
            added_ip.extend(self.normalize_net4(net_item.group()))
        feed_diff_data = {
            "feed_name": meta.get("feed_name"),
            "added_ip": added_ip,
            "feed_meta": meta
        }
        return feed_diff_data


SyncGit = SyncGit()


def sync_with_db_new(feed_path):
    if SyncGit.validate_feed(feed_path):
        feed_data = SyncGit.parse_feed_file(feed_path)
        if feed_data.get("added_ip"):
            SyncGit.logger.info("Found %d new data item(s) in new file %s" % (len(feed_data.get("added_ip")), feed_path))
            db_add_data(feed_data)


def sync_with_db_diff(diff_serialized):
    diff = pickle.loads(diff_serialized)
    modified_feed_path = "%s/%s" % (SyncGit.repo_path, diff.target_file[2:])
    if SyncGit.validate_feed(modified_feed_path):
        feed_diff_data = SyncGit.get_diff_data(diff, modified_feed_path)
        if feed_diff_data.get("added_ip"):
            SyncGit.logger.info("Found %d new data item(s) in diff for file %s" % (len(feed_diff_data.get("added_ip")), modified_feed_path))
            db_add_data(feed_diff_data)


if __name__ == "__main__":
    period = 3600 * int(SyncGit.sync_period_h)
    while True:
        SyncGit.logger.info("Started sync_git_repo()")
        repo_path_exists = os.path.exists(SyncGit.repo_path)
        if not repo_path_exists:
            return_value = SyncGit.clone_from_remote()
            if not return_value:
                SyncGit.logger.warning("Something went wrong with git synchronisation")
                continue
            feed_files_path_list = SyncGit.get_files(SyncGit.repo_path)
            try:
                pool = Pool(SyncGit.get_cpu_count())
                pool.map(sync_with_db_new, feed_files_path_list)
                pool.close()
                pool.join()
            except Exception as e:
                SyncGit.logger.exception("Error in multiprocessing occurred")
        else:
            diff = SyncGit.fetch_diff()
            if not diff:
                SyncGit.logger.warning("Something went wrong with git synchronisation")
                continue
            if diff.added_files:
                SyncGit.logger.info("After fetching found %d new file(s)" % len(diff.added_files))
                new_feeds_path = ["%s/%s" % (SyncGit.repo_path, added_files.target_file[2:]) for added_files in diff.added_files]
                try:
                    pool = Pool(SyncGit.get_cpu_count())
                    pool.map(sync_with_db_new, new_feeds_path)
                    pool.close()
                    pool.join()
                except Exception as e:
                    SyncGit.logger.exception("Error in multiprocessing occurred")
            if diff.modified_files:
                SyncGit.logger.info("After fetching found %d modified file(s)" % len(diff.modified_files))
                modified_feeds_serialized = [pickle.dumps(modified_files) for modified_files in diff.modified_files]
                try:
                    pool = Pool(SyncGit.get_cpu_count())
                    pool.map(sync_with_db_diff, modified_feeds_serialized)
                    pool.close()
                    pool.join()
                except Exception as e:
                    SyncGit.logger.exception("Error in multiprocessing occurred")
        SyncGit.logger.info("Sleep for %d hour(s)" % (period / 3600))
        time.sleep(period)
