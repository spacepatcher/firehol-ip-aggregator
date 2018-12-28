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

There are several API-functions for obtaining various information about feeds:

* POST `/search` - retrieve all information about requested IP or CIDR format objects
* GET `/search/ip` - retrieve all information about single requested IP or CIDR format object
* GET `/feeds` - retrieve all information about feeds
* GET `/feed/info` - retrieve all available information about the feed by his name
* GET `/feeds/categories` - retrieve all feed categories
* GET `/feeds/maintainers` - retrieve all feed maintainers
* GET `/maintainer/info` - retrieve all available information about the maintainer by his name
* GET `/maintainers/by_category` - retrieve all maintainers by category
* GET `/ip/bulk/by_category` - retrieve all IP addresses that are in feeds filtered by feed category

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
    "blacklisted_count": 1,
    "currently_blacklisted_count": 0,
    "feeds_available": 188,
    "request_time": "2018-02-02T14:27:59.957559+03:00",
    "requested_count": 1,
    "results": [
        {
            "categories": [
                "reputation"
            ],
            "currently_blacklisted": false,
            "first_seen": "2017-11-08T12:00:38.932354+00:00",
            "hits": [
                {
                    "category": "reputation",
                    "current_status": "absent",
                    "entries": "37968 unique IPs",
                    "feed_name": "hphosts_psh",
                    "first_seen": "2017-11-08T12:00:38.932354+00:00",
                    "last_added": "2018-01-12T11:35:49.283765+00:00",
                    "last_removed": "2017-11-19T07:09:04.321675+00:00",
                    "list_source_url": "http://hosts-file.net/psh.txt",
                    "maintainer": "hpHosts",
                    "maintainer_url": "http://hosts-file.net/",
                    "source_file_date": "Wed Jan 31 16:18:34 UTC 2018",
                    "timeline": [
                        {
                            "added": "2017-11-08T12:00:38.932354",
                            "removed": "2017-11-19T07:09:04.321675"
                        },
                        {
                            "added": "2018-01-12T11:35:49.283765",
                            "removed": ""
                        }
                    ]
                }
            ],
            "hits_count": 1,
            "ip": "149.255.60.136",
            "last_added": "2018-01-12T11:35:49.283765+00:00"
        }
    ]
}
```

If the observable is not found in the application database, the response will look like this:
```
{
    "blacklisted_count": 0,
    "currently_blacklisted_count": 0,
    "feeds_available": 188,
    "request_time": "2018-02-02T14:31:17.291948+03:00",
    "requested_count": 1,
    "results": []
}
```

### Important files

* `docker-persistent/conf/app.conf` - the main application configuration file
* `docker-persistent/conf/postgresql.conf` - the main Postgres configuration file (generated with http://pgtune.leopard.in.ua/)
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

It's recommended to use 2 workers per 1 core (do not forget to change `max_connections` parameter in `docker-persistent/conf/postgresql.conf`).

To apply configuration changes you should rebuild containers:
```
docker-compose down
docker-compose up --build
```
