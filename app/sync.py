import os
import time
import git
import unidiff
import requests
from subprocess import run, CalledProcessError

from modules.db_sync import FeedsStorage
from modules.general import General


FeedsStorage = FeedsStorage()


class SyncGit(General):
    def __init__(self):
        super().__init__()

        self.feed_data = {
            "added_ip":   [],
            "removed_ip": [],
            "feed_meta":  FeedsStorage.document["feed_meta"]
        }

    def check_network(self, is_available=False):
        url = "https://github.com"
        timeout = 5

        try:
            _ = requests.get(url, timeout=timeout)
            is_available = True

        except requests.ConnectionError:
            self.logger.error("github.com is not available due to network problems")

        finally:
            return is_available

    def clone_from_remote(self):
        SyncGit.logger.info("Cloning FireHOL repo from remote origin")

        try:
            run(["mkdir -p %s" % self.repo_path], shell=True, check=True)
            run(["git clone %s %s" % (self.firehol_ipsets_git, self.repo_path)], shell=True, check=True)
            run(["cd %s ; git checkout master" % self.repo_path], shell=True, check=True)
            self.logger.info("Successfully cloned FireHOL repo from remote origin")

        except CalledProcessError:
            self.logger.exception("CalledProcessError occurred")

    def fetch_diff(self):
        SyncGit.logger.info("Fetching diff from remote origin")

        try:
            firehol_repo = git.cmd.Git(self.repo_path)
            firehol_repo.checkout("master")
            firehol_repo.fetch("origin")
            diff_stdout = firehol_repo.execute(["git", "diff", "master", "origin/master"], True).split("\n")

            try:
                udiff = unidiff.PatchSet(diff_stdout)
                firehol_repo.execute(["git", "reset", "--hard", "origin/master"])
                firehol_repo.merge()
                self.logger.info("Successfully fetched diff from remote origin")

                return udiff

            except unidiff.UnidiffParseError:
                self.logger.exception("UnidiffParseError occurred")

        except git.GitCommandError:
            self.logger.exception("GitCommandError occurred")

    def validate_feed(self, feed_file_path):
        unique_ips_count = 0

        if not ".ipset" or ".netset" in feed_file_path:

            return False

        if not self.not_periodic_feed_re.search(feed_file_path):

            return False

        for data_string in self.read_file(feed_file_path):
            if self.uniq_ips_re.search(data_string):
                unique_ips_count = int(self.uniq_ips_re.search(data_string).group(1))

                break

            else:
                unique_ips_count = 0

        if unique_ips_count > self.unique_ips_limit:

            return False

        return True

    def get_meta_info(self, feed_path):
        feed_meta = FeedsStorage.document["feed_meta"]
        feed_strings = self.read_file(feed_path)

        for line_number, feed_string in enumerate(feed_strings):
            if "#" in feed_string:
                if line_number == 1:
                    feed_meta["feed_name"] = feed_string.split("# ")[1]

                if "Maintainer URL" in feed_string:
                    feed_meta["maintainer_url"] = feed_string.split(": ")[1]

                elif "Maintainer" in feed_string:
                    feed_meta["maintainer"] = feed_string.split(": ")[1]

                if "List source URL" in feed_string:
                    feed_meta["list_source_url"] = feed_string.split(": ")[1]

                if "Source File Date" in feed_string:
                    feed_meta["source_file_date"] = feed_string.split(": ")[1]

                if "Category" in feed_string:
                    feed_meta["category"] = feed_string.split(": ")[1]

                if "Entries" in feed_string:
                    feed_meta["entries"] = feed_string.split(": ")[1]

            else:

                break

        return feed_meta

    def parse_feed_file(self, feed_path):
        added_ip = list()

        feed_strings = self.read_file(feed_path)

        for line_number, feed_string in enumerate(feed_strings):
            ip_items = self.ip_re.search(feed_string)
            cidr_items = self.cidr_re.search(feed_string)

            if ip_items:
                added_ip.append(ip_items.group())
            elif cidr_items:
                added_ip.extend(self.iterate_cidr(cidr_items.group()))

        self.feed_data["added_ip"] = added_ip
        self.feed_data["feed_meta"] = self.get_meta_info(feed_path)

        return self.feed_data

    def get_diff_data(self, diff_data, file_path):
        added_ip = list()
        removed_ip = list()

        added_ip_items = self.added_ip_re.finditer(str(diff_data))
        added_cidr_items = self.added_cidr_re.finditer(str(diff_data))
        removed_ip_items = self.removed_ip_re.finditer(str(diff_data))
        removed_cidr_items = self.removed_cidr_re.finditer(str(diff_data))

        for ip_item in added_ip_items:
            added_ip.append(ip_item.group())

        for cidr_item in added_cidr_items:
            added_ip.extend(self.iterate_cidr(cidr_item.group()))

        for ip_item in removed_ip_items:
            removed_ip.append(ip_item.group())

        for cidr_item in removed_cidr_items:
            removed_ip.extend(self.iterate_cidr(cidr_item.group()))

        self.feed_data["added_ip"] = added_ip
        self.feed_data["removed_ip"] = removed_ip
        self.feed_data["feed_meta"] = self.get_meta_info(file_path)

        return self.feed_data


SyncGit = SyncGit()


def save_new(new_files_path):
    for path in new_files_path:
        if SyncGit.validate_feed(path):
            feed_data = SyncGit.parse_feed_file(path)
            added_ip_count = len(feed_data.get("added_ip"))

            if added_ip_count:
                SyncGit.logger.info("Found %d new IP(s) in new file %s" % (added_ip_count, path))

                FeedsStorage.save(feed_data)


def save_diff(git_diff):
    for git_modified_file in git_diff:
        modified_file_path = "%s/%s" % (SyncGit.repo_path, git_modified_file.target_file[2:])

        if SyncGit.validate_feed(modified_file_path):
            diff_feed_data = SyncGit.get_diff_data(git_modified_file, modified_file_path)
            added_ip_count = len(diff_feed_data.get("added_ip"))
            removed_ip_count = len(diff_feed_data.get("removed_ip"))

            if added_ip_count or removed_ip_count:
                SyncGit.logger.info("Found %d new IP(s) and %d removed data item(s) in diff for file %s"
                                    % (added_ip_count, removed_ip_count, modified_file_path))

            FeedsStorage.save(diff_feed_data)


if __name__ == "__main__":
    period = 3600 * int(SyncGit.sync_period_h)

    while True:
        SyncGit.logger.info("Syncing with remote repository")

        if SyncGit.check_network():
            if not os.path.exists(SyncGit.repo_path):
                SyncGit.clone_from_remote()
                feeds_path = SyncGit.list_dir(SyncGit.repo_path)

                if feeds_path:
                    SyncGit.logger.info("After cloning found %d new file(s)" % len(feeds_path))
                    save_new(feeds_path)

                else:
                    SyncGit.logger.warning("Local repository is empty")

            else:
                diff = SyncGit.fetch_diff()

                try:
                    if diff.added_files:
                        SyncGit.logger.info("After fetching found %d new file(s)" % len(diff.added_files))
                        feeds_path = ["%s/%s" % (SyncGit.repo_path, added_files.target_file[2:]) for added_files in diff.added_files]

                        save_new(feeds_path)
                        SyncGit.logger.info("Feeds processing finished")

                    if diff.modified_files:
                        SyncGit.logger.info("After fetching found %d modified file(s)" % len(diff.modified_files))

                        save_diff(diff.modified_files)
                        SyncGit.logger.info("Feeds processing finished")

                except AttributeError:
                    SyncGit.logger.exception("Diff data has an unrecognized structure")

        SyncGit.logger.info("Sleep for %d minute(s)" % (period / 60))
        time.sleep(period)
