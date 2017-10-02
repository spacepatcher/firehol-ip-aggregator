from multiprocessing import Queue, Process
import argparse
import sys
import re
import requests
import json
import netaddr


NETWORK_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2]))$")
IP_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
ES_SERVER = "http://10.0.180.12:9200"
PG_SERVER = "http://10.0.180.34:8081"


def prettify(data):
    if data:
        return json.dumps(data, indent=4, sort_keys=True)


def read_file(filename):
    with open(filename) as f:
        lines = f.read().splitlines()
    return lines


def validate_input(input):
    if NETWORK_re.match(input) or IP_re.match(input):
        return True


def request_api(url, payload):
    try:
        r = requests.post(url, data=payload, verify=False)
    except requests.exceptions.ConnectionError as e:
        print(e)
        print("Server is down or bad http address.")
        sys.exit(1)
    if r.status_code == 200:
        data = r.json()
        return data
    else:
        print("Something went wrong. Server down?")
        print("Status code: {}".format(r.status_code))
        sys.exit(1)


def pg_search_net(net_list):
    net_string = ",".join(net_list)
    url = PG_SERVER + "/search"
    payload = net_string
    results_total = request_api(url, payload)
    return results_total


def es_search_net(net_list):
    results_total = []
    for net in net_list:
        for ip in netaddr.IPNetwork(net).iter_hosts():
            try:
                url = ES_SERVER + "/_all/_search/"
                request = json.dumps({
                    "query": {
                        "match": {
                            "_all": str(ip)
                        }
                    },
                    "size": 0,
                    "aggregations": {
                        "aggr": {
                            "terms": {
                                "field": "_type"
                            }
                        }
                    },
                    "sort": [{
                            "_timestamp": {
                                "order": "desc"
                            }
                        }]
                })
                response = requests.get(url, data=request).json()
                if response.get("aggregations").get("aggr"):
                    result_dict = {}
                    feeds = []
                    for bucket in response.get("aggregations").get("aggr").get("buckets"):
                        feeds.append(bucket.get("key"))
                    if feeds:
                        result_dict["feeds"] = feeds
                        result_dict["ip"] = str(ip)
                    if result_dict:
                        results_total.append(result_dict)
            except AttributeError as e:
                print("Bad responce for URL %s" % (url))
            except requests.exceptions.ConnectionError as e:
                print("Server is down or bad http address.")
                return
    return results_total


def output_to_file(file_name, output_total):
    with open(file_name, 'a') as f:
        json.dump(output_total, f, indent=4, sort_keys=True)


def aggregate_outputs(pg_results, es_results):
    pg_ips = set()
    es_ips = set()
    output_total = []
    for pg_result in pg_results:
        pg_ips.add(pg_result.get("ip"))
    for es_result in es_results:
        es_ips.add(es_result.get("ip"))
    not_in_pg = es_ips.difference(pg_ips)
    not_in_es = pg_ips.difference(es_ips)
    common = es_ips.intersection(pg_ips)
    unoin = pg_ips.union(es_ips)
    for ip in list(unoin):
        aggregated_output = {}
        if ip in list(not_in_pg):
            for es_result in es_results:
                if es_result.get("ip") == ip:
                    aggregated_output["ip"] = es_result.get("ip")
                    aggregated_output["feeds"] = es_result.get("feeds")
        elif ip in list(not_in_es):
            for pg_result in pg_results:
                if pg_result.get("ip") == ip:
                    aggregated_output["ip"] = pg_result.get("ip")
                    aggregated_output["added"] = pg_result.get("added")
                    aggregated_output["feeds"] = pg_result.get("feeds")
        elif ip in list(common):
            for pg_result in pg_results:
                if pg_result.get("ip") == ip:
                    aggregated_output["ip"] = pg_result.get("ip")
                    aggregated_output["added"] = pg_result.get("added")
                    aggregated_output["feeds"] = pg_result.get("feeds")
                    for es_result in es_results:
                        if es_result.get("ip") == ip:
                            pg_feeds = pg_result.get("feeds")
                            es_feeds = es_result.get("feeds")
                            aggregated_output["feeds"] = pg_feeds + es_feeds
        output_total.append(aggregated_output)
    return output_total


def output_to_stdout(output_total):
    print(prettify(output_total))
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='''
ES Intel Feed server: %s
PG IP Feed server: %s''' % (ES_SERVER, PG_SERVER))

    parser.add_argument("-t", "--feed-type", choices=["ip_feed", "intel_feed", "all"], default="ip_feed", help="Input required feed types separated by commas (default: ip_feed). Notice that search in intel_feed can be slow enough.")
    parser.add_argument("-s", "--single", help="Search a single IP or network in IPv4 CIDR format.")
    parser.add_argument("-f", "--file", help="Search IPs or networks in IPv4 CIDR format from file (one per line).")
    parser.add_argument("-o", "--output", help="Dump results to JSON file (default output to stdout).", default=False)
    args = parser.parse_args()

    if not args.feed_type and not args.single and not args.file and not args.output:
        print("Type -h to get help info.")
        sys.exit(1)

    pg_results = {}
    es_results = {}
    if args.single:
        if validate_input(args.single):
            if args.feed_type == "all":
                pg_results = pg_search_net([args.single])
                es_results = es_search_net([args.single])
            elif args.feed_type == "ip_feed":
                pg_results = pg_search_net([args.single])
            elif args.feed_type == "intel_feed":
                es_results = es_search_net([args.single])
            else:
                print("You must choose the required feed type. Exiting...")
                sys.exit(1)
        else:
            print("Data validation error in '%s'." % (args.single))
            sys.exit(1)
    elif args.file:
        net_lines = read_file(args.file)
        line_number = 0
        for line in net_lines:
            line_number += 1
            if validate_input(line):
                pass
            else:
                print("Data validation error at line number %s in '%s'." % (line_number, line))
                sys.exit(1)
        if args.feed_type == "all":
            pg_results = pg_search_net(net_lines)
            es_results = es_search_net(net_lines)
        elif args.feed_type == "ip_feed":
            pg_results = pg_search_net(net_lines)
        elif args.feed_type == "intel_feed":
            es_results = es_search_net(net_lines)
        else:
            print("You must choose the required feed type. Exiting...")
            sys.exit(1)
    else:
        print("You must choose the input data format. Exiting...")
        sys.exit(1)
    aggregated_output = aggregate_outputs(pg_results, es_results)
    if args.output:
        output_to_file(args.output, aggregated_output)
    else:
        output_to_stdout(aggregated_output)
