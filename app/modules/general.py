import json
import itertools
import re
import os
import netaddr
import logging


class General:
    def __init__(self):
        # Regular expressions
        self.added_ip_re = re.compile(r"(?<=\+)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(?=(?!/)\D|$)")
        self.added_cidr_re = re.compile(r"(?<=\+)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2])){1}(?=\D|$)")
        self.removed_ip_re = re.compile(r"(?<=-)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(?=(?!/)\D|$)")
        self.removed_cidr_re = re.compile(r"(?<=-)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2])){1}(?=\D|$)")
        self.ip_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
        self.cidr_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2]))$")
        self.not_periodic_feed_re = re.compile(r"^(?!.*_\d{1,3}d(\.ipset|\.netset)).*(\.ipset|\.netset)$")
        self.uniq_ips_re = re.compile(r"(?<=\ )(\d*)(?= unique IPs)")

        self.config = self.load_config("%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf/app.conf"))

        # Database configuration
        self.database_user = self.config.get("mongo_user")
        self.database_password = self.config.get("mongo_password")
        self.database_name = self.config.get("mongo_db_name")
        self.database_address = self.config.get("mongo_address")

        # Application configuration
        self.firehol_ipsets_git = self.config.get("firehol_ipsets_git")
        self.sync_period_h = self.config.get("sync_period_h")
        self.unique_ips_limit = self.config.get("unique_ips_limit")

        # FireHOL repo path
        self.repo_path = "%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "git/firehol")

        # Logger configuration
        self.log_path = "%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log/run.log")
        self.logger = logging.getLogger(__name__)
        self.formatter = logging.basicConfig(filename=self.log_path, level=logging.INFO,
                                             format="%(asctime)s [%(levelname)s] [%(filename)s] %(funcName)s: %(message)s")

    def load_config(self, config):
        with open(config) as file_obj:
            return json.load(file_obj)

    def read_file(self, filename):
        with open(filename) as f:
            for line in f:
                yield line.strip("\n")

    def group_by(self, n, iterable):
        it = iter(iterable)

        while True:
            chunk = tuple(itertools.islice(it, n))
            if not chunk:
                return
            yield chunk

    def iterate_cidr(self, cidr):
        for ip in netaddr.IPNetwork(cidr).iter_hosts():
            yield str(ip)

    def validate_request(self, request):
        if self.cidr_re.match(request) or self.ip_re.match(request):

            return True

    def list_dir(self, directory):
        files = list()

        for file in os.listdir(directory):
            files.append(os.path.join(directory, file))

        return files
