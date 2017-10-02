from itertools import cycle
import json
import resource
import itertools
import re
import netaddr

added_ip_re = re.compile(r"(?<=\+)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?=\n)")
added_net_re = re.compile(r"(?<=\+)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})(?=\n)")
ip_re = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
net_re = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}")
not_periodic_feed_re = re.compile(r"^(?!.*_\d{1,3}d(\.ipset|\.netset)).*(\.ipset|\.netset)$")
uniq_ips_re = re.compile(r"(?<=\ )(\d*)(?= unique IPs)")


def zip_uneven(A, B):
    if len(A) == len(B):
        return zip(A, B)
    if len(B) > len(A):
        C = list(B)
        B = list(A)
        A = list(C)
        del C
    return zip(A, cycle(B)) if len(A) > len(B) else zip(cycle(A), B)


def jsonify(data):
    json_data = json.dumps(data, indent=4, sort_keys=True)
    return json_data


def load_cfg(config):
    with open(config) as f:
        data = json.load(f)
        return data


def read_file(filename):
    with open(filename) as f:
        for line in f:
            yield line.strip("\n")


def limit_memory(maxsize_g):
    maxsize = maxsize_g * 2 ** 30
    resource.setrlimit(resource.RLIMIT_AS, (maxsize, maxsize))


def grouper(n, iterable):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def normalize_ip4(ip_list_raw):
    ip_norm_list = []
    for ip_raw in ip_list_raw:
        net_match = net_re.search(ip_raw)
        if net_match:
            for ip in netaddr.IPNetwork(ip_raw).iter_hosts():
                ip_norm_list.append(str(ip))
        else:
            ip_norm_list.append(str(netaddr.IPAddress(ip_raw)))
    return ip_norm_list


def net_is_local(net):
    is_local = netaddr.IPNetwork(net).is_private()
    return is_local


def remove_duplicate_dicts(with_duplicates):
    unique_ip = []
    unique_dicts = []
    for data_dict in with_duplicates:
        if len(unique_ip) > 0:
            if data_dict.get("ip") in unique_ip:
                pass
            else:
                unique_dicts.append(data_dict)
                unique_ip.append(data_dict.get("ip"))
        else:
            unique_dicts.append(data_dict)
            unique_ip.append(data_dict.get("ip"))
    return unique_dicts
