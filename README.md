# Aggregator of FireHOL IP lists
Аpplication for keeping feeds from <a href="https://github.com/firehol/blocklist-ipsets" target="_blank">blocklist-ipsets</a> (only *.netset and *.ipset files are aggregated) in PostgreSQL with including historical changes. For requests developed HTTP-based API service. 

Some features of keeping and processing data:
* New data is written to existing data with `last_added` field update.
* Data deleted from reputation feed is not deleted from the application database. For such data, `last_removed` field is updated.
* Field `timeline` is based on events of adding and removing item from reputation list.

**Start application**

To start the collection module and the API server, just type:
```
sudo docker-compose up -d
```
The collection module will start automatically.

**Important files**

* `client.py` - simple python script for convenient interaction with FireHOL-IP-Aggregator API.
* `app/conf/config.json` - the main configuration file with several parameters.
* `conf/postgresql.conf` - the main Postgres configuration file (generated with http://pgtune.leopard.in.ua/).

The most important configuration parameters are listed in the table below.

| Parameter | Description |
| ------ | ------ |
| `"unique_ips_limit"` | Defines the limit of the number of unique IP addresses in FireHOL feeds that will be aggregated (the goal is to filter out huge feeds) |
| `"sync_period_h"` | Defines time period for syncing with FireHOL IP list repository |
| `"firehol_ipsets_git"` | Defines FireHOL IP lists repository url |

**Example usage**

Application is able to get search requests in IP or CIDR format, also in mixed list of both data types. To search, run the command:

`python client.py -s 149.255.60.136` 

Here is an example of the result of the request IP `149.255.60.136` using the client:
```
{
    "blacklisted_count": 1,
    "feeds_available": 188,
    "request_time": "2018-02-02T14:27:59.957559+03:00",
    "requested_count": 1,
    "results": {
        "149.255.60.136": {
            "categories": [
                "reputation"
            ],
            "first_seen": "2017-11-08T12:00:38.932354+00:00",
            "hits": [
                {
                    "category": "reputation",
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
            "last_added": "2018-01-12T11:35:49.283765+00:00"
        }
    }
}

```
If the observable is not found in the application database, the response will look like this:
```
{
    "blacklisted_count": 0,
    "feeds_available": 188,
    "request_time": "2018-02-02T14:31:17.291948+03:00",
    "requested_count": 1,
    "results": {}
}
```
Also you can make requests by using python requests library.
