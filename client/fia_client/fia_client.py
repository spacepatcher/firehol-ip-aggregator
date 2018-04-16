import logging
import re
import requests

logger = logging.getLogger('fia_client')

network_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2]))$")
ip_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
word_re = re.compile("\w+")


class FIAClient(object):
    def __init__(self, fia_url):
        self.fia_url = fia_url

        self.network_re = network_re
        self.ip_re = ip_re
        self.word_re = word_re

    def search(self, payload):
        """Retrieve all information about feeds"""

        path = "/search"

        url = self.fia_url + path

        if self._validate_network_list(payload):
            payload = ",".join(payload)
            print(payload)

            return self._request_post(url, payload)

        else:
            return {"errors": "Data validation error occurred"}

    def feeds_categories(self):
        """Retrieve all feed categories"""

        path = "/feeds/categories"

        url = self.fia_url + path
        payload = {}

        return self._request_get(url, payload)

    def feeds_maintainers(self):
        """Retrieve all feed maintainers"""

        path = "/feeds/maintainers"

        url = self.fia_url + path
        payload = {}

        return self._request_get(url, payload)

    def feed_info(self, feed_name):
        """Retrieve all available information about the feed by its name"""

        path = "/feed/info"

        feed_name = self._clear_request(feed_name)

        url = self.fia_url + path
        payload = {"feed_name": feed_name}

        return self._request_get(url, payload)

    def maintainer_info(self, maintainer):
        """Retrieve all available information about the maintainer by its name"""

        path = "/maintainer/info"

        maintainer = self._clear_request(maintainer)

        url = self.fia_url + path
        payload = {"maintainer": maintainer}

        return self._request_get(url, payload)

    def maintainers_by_category(self, category):
        """Retrieve all maintainers by category"""

        path = "/maintainers/by_category"

        category = self._clear_request(category)

        url = self.fia_url + path
        payload = {"category": category}

        return self._request_get(url, payload)

    def ip_bulk_by_category(self, category):
        """Retrieve all IP addresses that are in feeds by feed category"""

        path = "/ip/bulk/by_category"

        category = self._clear_request(category)

        url = self.fia_url + path
        payload = {"category": category}

        return self._request_get(url, payload)

    def _validate_network_list(self, payload):
        if isinstance(payload, list):
            passed = True

            for item in payload:
                if self.network_re.match(item) or self.ip_re.match(item):
                    pass

                else:
                    passed = False

                    break

        else:
            passed = False

        return passed

    def _clear_request(self, unfiltered):
        filtered = self.word_re.search(unfiltered)

        try:
            filtered = filtered.group()

        except AttributeError:
            filtered = ""

        return filtered

    def _request_post(self, url, payload):
        try:
            r = requests.post(url, data=payload)
            print(r)

            if r.status_code == 200:
                data = r.json()

            else:
                data = {"errors": "Server answered with unexpected HTTP code {}".format(r.status_code)}

        except requests.exceptions.ConnectionError:
            data = {"errors": "Server on {} is down or bad http address".format(self.fia_url)}

        return data

    def _request_get(self, url, payload):
        try:
            r = requests.get(url, params=payload)

            if r.status_code == 200:
                data = r.json()

            else:
                data = {"errors": "Server answered with unexpected HTTP code {}".format(r.status_code)}

        except requests.exceptions.ConnectionError:
            data = {"errors": "Server on {} is down or bad http address".format(self.fia_url)}

        return data
