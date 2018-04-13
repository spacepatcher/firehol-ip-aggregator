import logging
import re
import json

logger = logging.getLogger('fia_client')

NETWORK_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(/([0-9]|[1-2][0-9]|3[0-2]))$")
IP_re = re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")


class FIAClient(object):
    def __init__(self, fia_url):
        self.fia_url = fia_url

        self.NETWORK_re = NETWORK_re
        self.IP_re = IP_re

    def search(self, payload):
        """Retrieve all information about feeds"""

        pass

    def feeds_categories(self):
        """Retrieve all feed categories"""

        pass

    def feeds_maintainers(self):
        """Retrieve all feed maintainers"""

        pass

    def feed_info(self, feed_name):
        """Retrieve all available information about the feed by its name"""

        pass

    def maintainer_info(self, maintainer):
        """Retrieve all available information about the maintainer by its name"""

        pass

    def maintainers_by_category(self, category):
        """Retrieve all maintainers by category"""

        pass

    def ip_bulk_by_category(self, category):
        """Retrieve all IP addresses that are in feeds by feed category"""

        pass

    def _validate_request(self, request, passed=False):
        if isinstance(request, list):
            passed = True

            for item in request:
                if not NETWORK_re.match(item) or IP_re.match(item):
                    passed = False

                    break

        return passed

    def _clear_request(self, request):
        pass

    def _prettify(self, data):
        if data:
            return json.dumps(data, indent=4, sort_keys=True)
