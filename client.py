import argparse
import sys
import re
import requests
import json


NETWORK_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2]))$")
IP_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
DB_SERVER = "http://127.0.0.1:8000"


def prettify(data):
    if data:
        return json.dumps(data, indent=4, sort_keys=True)


def read_file(filename):
    with open(filename) as f:
        lines = f.read().splitlines()

    return lines


def validate_request(request):
    if NETWORK_re.match(request) or IP_re.match(request):

        return True


def api_search(payload):
    url = DB_SERVER + "/search"

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


def output_to_file(file_name, output_total):
    with open(file_name, 'a') as f:
        json.dump(output_total, f, indent=4, sort_keys=True)


def output_to_stdout(output_total):
    print(prettify(output_total))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''

Postgres IP Feed API server: %s''' % (DB_SERVER))

    parser.add_argument("-s", "--stdin", help="Search IP or network in IPv4 CIDR format (enter multiple items separated by commas).")
    parser.add_argument("-f", "--file", help="Search IPs or networks in IPv4 CIDR format from file (one per line).")
    parser.add_argument("-o", "--output", help="Dump results to JSON file (default output to stdout).", default=False)
    args = parser.parse_args()

    if args.stdin:
        for request in args.stdin.split(","):
            if validate_request(request):
                pass
            else:
                print("Data validation error in '%s'." % request)
                sys.exit(1)

        search_results = api_search(args.stdin)

    elif args.file:
        line_number = 0

        request_list = read_file(args.file)

        for request in request_list:
            line_number += 1

            if validate_request(request):
                pass
            else:
                print("Data validation error at line number %s in '%s'." % (line_number, request_list))
                sys.exit(1)

        search_results = api_search(",".join(request_list))

    else:
        print("You must choose the input data format. Exiting...")
        sys.exit(1)

    if args.output:
        output_to_file(args.output, search_results)
    else:
        output_to_stdout(search_results)
