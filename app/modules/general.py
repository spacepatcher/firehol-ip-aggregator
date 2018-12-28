import json
import itertools
import re
import os
import netaddr
import logging
from multiprocessing import Semaphore, cpu_count


class General:
    def __init__(self):
        # Regular expressions
        self.added_ip_re = re.compile(r"(?<=\+)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(?=(?!/)\D|$)")
        self.added_net_re = re.compile(r"(?<=\+)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2])){1}(?=\D|$)")
        self.removed_ip_re = re.compile(r"(?<=-)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(?=(?!/)\D|$)")
        self.removed_net_re = re.compile(r"(?<=-)(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2])){1}(?=\D|$)")
        self.ip_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
        self.net_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2]))$")
        self.not_periodic_feed_re = re.compile(r"^(?!.*_\d{1,3}d(\.ipset|\.netset)).*(\.ipset|\.netset)$")
        self.uniq_ips_re = re.compile(r"(?<=\ )(\d*)(?= unique IPs)")

        # Application configuration
        self.config = self.load_config("%s/%s" % (os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conf/app.conf"))
        self.database_user = self.config.get("pg_database_user")
        self.database_password = self.config.get("pg_database_password")
        self.database_name = self.config.get("pg_database_name")
        self.server_address = self.config.get("pg_server_address")
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

    def iterate_net(self, net_raw):
        for ip in netaddr.IPNetwork(net_raw).iter_hosts():
            yield str(ip)

    def validate_request(self, request):
        if self.net_re.match(request) or self.ip_re.match(request):

            return True

    def get_cpu_count(self):
        return Semaphore(cpu_count()).get_value()

    def get_files(self, directory):
        files = list()

        for file in os.listdir(directory):
            files.append(os.path.join(directory, file))

        return files

    def extend_result_data(self, results, currently_presented_count=0):
        bunched_dict = dict()
        extended_results = list()

        for dictionary in results:
            current_status = "absent"

            if not dictionary.get("last_removed"):
                current_status = "present"

            elif dictionary.get("last_added") > dictionary.get("last_removed"):
                current_status = "present"

            dictionary.update({
                "current_status": current_status
            })

            bunching_element = dictionary.pop("ip", None)
            bunched_dict.setdefault(bunching_element, []).append(dictionary)

        for bunching_element, value in bunched_dict.items():
            currently_blacklisted = False

            for dictionary in value:
                if dictionary.get("current_status", None) == "present":
                    currently_blacklisted = True
                    currently_presented_count += 1

                    break

            extended_results.append({
                "ip": bunching_element,
                "categories": list(set([dictionary.get("category") for dictionary in bunched_dict[bunching_element]])),
                "first_seen": sorted(list(set([dictionary.get("first_seen") for dictionary in bunched_dict[bunching_element]])))[0],
                "last_added": sorted(list(set([dictionary.get("last_added") for dictionary in bunched_dict[bunching_element]])), reverse=True)[0],
                "hits_count": len(value),
                "currently_blacklisted": currently_blacklisted,
                "hits": bunched_dict.get(bunching_element, None)
            })

        return extended_results, currently_presented_count
