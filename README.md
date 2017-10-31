# Firehol-IP-Aggregator
Аpplication for keeping reputation feeds from https://github.com/firehol/blocklist-ipsets (.netset and .ipset) data in relational database PostgreSQL with including historical data. 

Some features of keeping and processing data:
* Reputation data is never deleted from the application database
* New data is written to existing data with a timestamp update

**Start application**

To start the collection module and the API server locally, just type:
```
sudo docker-compose up -d
```

**Important files**

* `client.py` - simple python script for convenient interaction with Firehol-IP-Aggregator API.
* `app/conf/config.json` - the main configuration file with several parameters. `"unique_ips_limit"` is the most interesting one, with his help you can limit the set of Firehol feeds based on the number of unique IP addresses.

**Example usage**

Application is able to get search requests in IP or CIDR format, also in mixed list of both data types. To search, run the command:
`python client.py -s 8.8.8.8` 

Here is an example of the result of the request ip using the client:
```
{
    "feeds_available": 136,
    "request_time": "2017-10-25T16:34:27.703801+03:00",
    "results": {
        "8.7.42.33": {
            "categories": [
                "spam"
            ],
            "first_seen": "2017-10-24T15:07:25.495289+00:00",
            "hits": [
                {
                    "category": "spam",
                    "entries": "5323 unique IPs",
                    "feed_name": "chaosreigns_iprep50",
                    "first_seen": "2017-10-24T15:07:25.495289+00:00",
                    "last_added": "2017-10-24T15:07:25.495289+00:00",
                    "list_source_url": "http://www.chaosreigns.com/iprep/iprep.txt",
                    "maintainer": "ChaosReigns.com",
                    "maintainer_url": "http://www.chaosreigns.com/iprep",
                    "source_file_date": "Fri Jun 17 10:01:27 UTC 2016"
                },
                {
                    "category": "spam",
                    "entries": "5323 unique IPs",
                    "feed_name": "chaosreigns_iprep100",
                    "first_seen": "2017-10-24T15:07:47.495608+00:00",
                    "last_added": "2017-10-24T15:07:47.495608+00:00",
                    "list_source_url": "http://www.chaosreigns.com/iprep/iprep.txt",
                    "maintainer": "ChaosReigns.com",
                    "maintainer_url": "http://www.chaosreigns.com/iprep",
                    "source_file_date": "Fri Jun 17 10:01:27 UTC 2016"
                },
                {
                    "category": "spam",
                    "entries": "5323 unique IPs",
                    "feed_name": "chaosreigns_iprep0",
                    "first_seen": "2017-10-24T15:08:11.784491+00:00",
                    "last_added": "2017-10-24T15:08:11.784491+00:00",
                    "list_source_url": "http://www.chaosreigns.com/iprep/iprep.txt",
                    "maintainer": "ChaosReigns.com",
                    "maintainer_url": "http://www.chaosreigns.com/iprep",
                    "source_file_date": "Fri Jun 17 10:01:27 UTC 2016"
                }
            ],
            "hits_count": 3,
            "last_added": "2017-10-24T15:08:11.784491+00:00"
        }
    }
}
```
If the observable is not found in the application database, the response will look like this:
```
{
    "feeds_available": 136,
    "request_time": "2017-10-29T18:15:10.807654+03:00",
    "results": {}
}
```
Also you can make requests by using python requests library.

**Thanks**

Thanks @ilyaglow for contributing!
