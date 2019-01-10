import hug

from modules.db_sync import FeedsStorage
from modules.general import General


FeedsStorage = FeedsStorage()
General = General()

General.logger.info("API instance successfully started")


@hug.post("/search", output=hug.output_format.json, version=1)
def search(body):
    """Search for a list of IP objects in all available feeds. Input: a string containing IP addresses separated by commas in HTTP POST body"""

    try:
        payload = body.read().decode("utf-8")

    except AttributeError:
        payload = body

    payload = payload.split(",")

    if isinstance(payload, list):
        for item in payload:
            if General.validate_request(item):
                pass

            else:
                return {"errors": "Data validation error in '%s'" % item}

    else:
        return {"errors": "Got an unrecognized structure"}

    return FeedsStorage.search(list(set(payload)))


@hug.get("/search/ip", output=hug.output_format.json, examples="v=8.8.8.8", version=1)
def search_get(v: hug.types.text):
    """Search for an IP object in all available feeds. Input: HTTP GET with parameter containing a single IP address"""

    if General.validate_request(v):
        payload = [v]

    else:
        return {"errors": "Data validation error in '%s'" % v}

    return FeedsStorage.search(payload)
