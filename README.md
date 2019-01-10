# Aggregator of FireHOL IP lists

Application for keeping feeds from <a href="https://github.com/firehol/blocklist-ipsets" target="_blank">blocklist-ipsets</a> (only *.netset and *.ipset files are aggregated) with including historical changes. HTTP-based API service for search requests developed.

Some features of keeping and processing data:
* New data is written to existing data with `last_added` field update
* Data deleted from reputation feed is not deleted from the application database
* Field `timeline` is based on events of adding and removing item from reputation list

### Start application

To start the collection module and the HTTP-based API service, just type:
```
docker-compose up
```
The collection module will start in container `sync`.

By default, the HTTP-based API service running in container `api` and is available on port 8000.

### API

There are several API-functions for search requests:

* POST `/search` - retrieve all information about requested IP or CIDR format objects
* GET `/search/ip` - retrieve all information about single requested IP or CIDR format object

Access to the API documentation can be obtained by requesting any unspecified URL.

### Example usage

A simple python3 package `fiaclient` is designed as a client for FireHOL-IP-Aggregator API.

Install the package with pip:
```
pip install fiaclient
```

Get a client object in python3 console:
```
from fiaclient import fiaclient
client = fiaclient.FIAClient(fia_url="http://127.0.0.1:8000/")
```

To get information about `fiaclient` package visit https://github.com/spacepatcher/FireHOL-IP-Aggregator/blob/develop/fiaclient/README.md.

The application is able to get search requests in IP or CIDR format, also in mixed list of both data types. To search, run the command in python3 console:
```
result = client.search(payload=["149.255.60.136"])
```

Also you can generate search requests using cURL:
* For HTTP POST search API function:
```
curl -X POST --data '8.8.8.8,1.1.1.1' -H 'Content-Type: text/html' localhost:8000/search
```
* For HTTP GET search API function:
```
curl -X GET localhost:8000/search/ip?v=8.8.8.8
```

Here is an example of the result of the requested payload:
```
{
  "request_time": "2019-01-10T15:39:03.927874+03:00",
  "records_count": 1601585,
  "requested_count": 1,
  "blacklisted_count": 1,
  "currently_blacklisted_count": 1,
  "results": [
    {
      "ip": "5.153.47.228",
      "categories": [
        "malware"
      ],
      "first_seen": "2019-01-10T12:37:09.164000",
      "last_added": "2019-01-10T12:37:09.164000",
      "hits_count": 1,
      "currently_blacklisted": true,
      "hits": [
        {
          "feed_name": "vxvault",
          "category": "malware",
          "maintainer": "VxVault",
          "maintainer_url": "http://vxvault.net",
          "list_source_url": "http://vxvault.net/ViriList.php?s=0&m=100",
          "source_file_date": "Thu Jan 10 03:24:39 UTC 2019",
          "entries": "76 unique IPs",
          "first_seen": "2019-01-10T12:37:09.164000",
          "last_added": "2019-01-10T12:37:09.164000",
          "last_removed": null,
          "current_status": "present",
          "timeline": [
            {
              "added": "2019-01-10T12:37:09.164000",
              "removed": null
            }
          ]
        }
      ]
    }
  ]
}
```

If the observable is not found in the application database, the response will looks like this:
```
{
  "request_time": "2019-01-10T15:30:03.813983+03:00",
  "records_count": 1601585,
  "requested_count": 1,
  "blacklisted_count": 0,
  "currently_blacklisted_count": 0,
  "results": []
}
```

### Important files

* `docker-persistent/conf/app.conf` - the main application configuration file
* `docker-persistent/app/log/run.log` - the main log file

### Application configuration

The most important configuration parameters from `docker-persistent/conf/app.conf` are listed in the table below.

| Parameter | Description |
| ------ | ------ |
| `"unique_ips_limit"` | Defines the limit of the number of unique IP addresses in FireHOL feeds that will be aggregated (the goal is to filter out huge feeds) |
| `"sync_period_h"` | Defines time period for syncing with FireHOL IP list repository |
| `"firehol_ipsets_git"` | Defines FireHOL IP lists repository url |

Also it's possible to change count of workers that process queries to API in `docker/Dockerfile.api` by changing `--workers` argument value in `ENTRYPOINT`.
```
ENTRYPOINT ["gunicorn", "--bind=0.0.0.0:8000", "--workers=4", "--timeout", "3600", "api:__hug_wsgi__"]
```

To apply configuration changes you should rebuild containers:
```
docker-compose down
docker-compose up --build
```
