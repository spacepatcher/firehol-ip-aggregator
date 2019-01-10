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

    def _validate_request(self, request):
        if self.net_re.match(request) or self.ip_re.match(request):

            return True

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
