import re
import requests


net_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2]))$")
ip_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
word_re = re.compile("\w+")


class FIAClient(object):
    def __init__(self, fia_url):
        self.fia_url = fia_url

        self.net_re = net_re
        self.ip_re = ip_re
        self.word_re = word_re

    def search(self, payload):
        """Search for a list of IP objects in all available feeds.

        Args:
            payload (list): A list of IP objects (CIDR format is also possible).

        Returns:
            dict: All information about requested the list of IP objects.

        """

        path = "/search"

        url = self.fia_url + path

        if isinstance(payload, list):
            for item in payload:
                if self._validate_request(item):
                    pass

                else:
                    return {"errors": "Data validation error in '%s'" % item}

        else:
            return {"errors": "Got an unrecognized structure"}

        payload = ",".join(payload)

        return self._request_post(url, payload)

    def feeds_categories(self):
        """Retrieve all feed categories.

        Returns:
            dict: All feed categories.

        """

        path = "/feeds/categories"

        url = self.fia_url + path
        payload = {}

        return self._request_get(url, payload)

    def feeds_maintainers(self):
        """Retrieve all feed maintainers.

        Returns:
            dict: All feed maintainers.

        """

        path = "/feeds/maintainers"

        url = self.fia_url + path
        payload = {}

        return self._request_get(url, payload)

    def feed_info(self, feed_name):
        """Retrieve all available information about the feed by its name.

        Args:
            feed_name (str): A feed name.

        Returns:
            dict: All available information about the feed by its name.

        """

        path = "/feed/info"

        feed_name = self._clear_request(feed_name)

        url = self.fia_url + path
        payload = {"feed_name": feed_name}

        return self._request_get(url, payload)

    def maintainer_info(self, maintainer):
        """Retrieve all available information about the maintainer by its name.

        Args:
            maintainer (str): A maintainer name.

        Returns:
            dict: All available information about the maintainer by its name.

        """

        path = "/maintainer/info"

        maintainer = self._clear_request(maintainer)

        url = self.fia_url + path
        payload = {"maintainer": maintainer}

        return self._request_get(url, payload)

    def maintainers_by_category(self, category):
        """Retrieve all maintainers by category.

        Args:
            category (str): A maintainers category.

        Returns:
            dict: All maintainers by category.

        """

        path = "/maintainers/by_category"

        category = self._clear_request(category)

        url = self.fia_url + path
        payload = {"category": category}

        return self._request_get(url, payload)

    def ip_bulk_by_category(self, category):
        """Retrieve all IP addresses that are in feeds by feed category.

        Args:
            category (str): A feed category.

        Returns:
            dict: All IP addresses that are in feeds by the feed category.

        """

        path = "/ip/bulk/by_category"

        category = self._clear_request(category)

        url = self.fia_url + path
        payload = {"category": category}

        return self._request_get(url, payload)

    def _validate_request(self, request):
        if self.net_re.match(request) or self.ip_re.match(request):

            return True

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
