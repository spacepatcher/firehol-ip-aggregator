import json
import itertools
import re
import os
import netaddr
import logging
from multiprocessing import Semaphore, cpu_count
from sqlalchemy.orm import sessionmaker


class General:
    def __init__(self):
        self.added_ip_re = re.compile(r"(?<=\+)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(?=\D)")
        self.added_net_re = re.compile(r"(?<=\+)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2])){1}(?=\D)")
        self.ip_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
        self.net_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2]))$")
        self.not_periodic_feed_re = re.compile(r"^(?!.*_\d{1,3}d(\.ipset|\.netset)).*(\.ipset|\.netset)$")
        self.uniq_ips_re = re.compile(r"(?<=\ )(\d*)(?= unique IPs)")

        self.repo_path = "%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "git_data/firehol")
        self.log_path = "%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "log/run.log")

        self.config = self.load_config("%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf/config.json"))
        self.database_user = self.config.get("pg_database_user")
        self.database_password = self.config.get("pg_database_password")
        self.database_name = self.config.get("pg_database_name")
        self.server_address = self.config.get("pg_server_address")
        self.firehol_ipsets_git = self.config.get("firehol_ipsets_git")
        self.sync_period_h = self.config.get("sync_period_h")
        self.unique_ips_limit = self.config.get("unique_ips_limit")

        self.logger = logging.getLogger(__name__)
        self.formatter = logging.basicConfig(filename=self.log_path, level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(filename)s] %(funcName)s: %(message)s")

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

    def normalize_net4(self, net_raw):
        for ip in netaddr.IPNetwork(net_raw).iter_hosts():
            yield str(ip)

    def validate_input_item(self, input):
        if self.net_re.match(input) or self.ip_re.match(input):
            ip_network = input
            if not netaddr.IPNetwork(ip_network).is_private():
                return True

    def get_cpu_count(self):
        return Semaphore(cpu_count()).get_value()

    def get_files(self, directory):
        files = list()
        for file in os.listdir(directory):
            files.append(os.path.join(directory, file))
        return files

    def create_db_session(self, engine):
        try:
            cursor = engine.connect()
            Session = sessionmaker(bind=cursor)
            return Session()
        except Exception:
            self.logger.exception("Error in creation DB session")
