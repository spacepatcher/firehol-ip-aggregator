# Aggregator of Firehol IP blacklists
Аpplication for keeping reputation feeds from https://github.com/firehol/blocklist-ipsets (.netset and .ipset only and not time sliced lists) in PostgreSQL database with including historical data. 

Some features of keeping and processing data:
* New data is written to existing data with `last_added` field update.
* Data deleted from reputation feed is not deleted from the application database. For such data, `last_removed` field is updated.
* Field `timeline` is based on events of adding and removing item from reputation list.

**Start application**

To start the collection module and the API server, just type:
```
sudo docker-compose up -d
```

**Important files**

* `client.py` - simple python script for convenient interaction with Firehol-IP-Aggregator API.
* `app/conf/config.json` - the main configuration file with several parameters. `"unique_ips_limit"` is the most interesting one, with his help you can limit the set of Firehol feeds based on the number of unique IP addresses.

**Example usage**

Application is able to get search requests in IP or CIDR format, also in mixed list of both data types. To search, run the command:
`python client.py -s 212.92.122.66` 

Here is an example of the result of the request ip using the client:
```
{
    "blacklisted_count": 1,
    "feeds_available": 151, 
    "request_time": "2017-12-08T17:59:56.576402+03:00", 
    "requested_count": 1, 
    "results": {
        "212.92.122.66": {
            "categories": [
                "reputation", 
                "attacks"
            ], 
            "first_seen": "2017-12-05T12:15:30.436526+00:00", 
            "hits": [
                {
                    "category": "attacks", 
                    "entries": "198 unique IPs", 
                    "feed_name": "urandomusto_unspecified", 
                    "first_seen": "2017-12-05T12:15:30.436526+00:00", 
                    "last_added": "2017-12-05T12:15:30.436526+00:00", 
                    "last_removed": "2017-12-07T12:24:06.489593+00:00", 
                    "list_source_url": "http://urandom.us.to/report.php?ip=&info=&tag=unspecified&out=txt&submit=go", 
                    "maintainer": "urandom.us.to", 
                    "maintainer_url": "http://urandom.us.to/", 
                    "source_file_date": "Fri Dec  8 10:02:15 UTC 2017", 
                    "timeline": [
                        {
                            "added": "2017-12-05T12:15:30.436526", 
                            "removed": "2017-12-07T12:24:06.489593"
                        }
                    ]
                }, 
                {
                    "category": "reputation", 
                    "entries": "93 unique IPs", 
                    "feed_name": "bds_atif", 
                    "first_seen": "2017-12-05T12:15:53.183365+00:00", 
                    "last_added": "2017-12-05T12:15:53.183365+00:00", 
                    "last_removed": "2017-12-08T12:25:00.947136+00:00", 
                    "list_source_url": "https://www.binarydefense.com/banlist.txt", 
                    "maintainer": "Binary Defense Systems", 
                    "maintainer_url": "https://www.binarydefense.com/", 
                    "source_file_date": "Fri Dec  8 08:00:04 UTC 2017", 
                    "timeline": [
                        {
                            "added": "2017-12-05T12:15:53.183365", 
                            "removed": "2017-12-08T12:25:00.947136"
                        }
                    ]
                }
            ], 
            "hits_count": 2, 
            "last_added": "2017-12-05T12:15:53.183365+00:00"
        }
    }
}
```
If the observable is not found in the application database, the response will look like this:
```
{
    "blacklisted_count": 0,
    "requested_count": 2,
    "feeds_available": 136,
    "request_time": "2017-10-29T18:15:10.807654+03:00",
    "results": {}
}
```
Also you can make requests by using python requests library.

**Thanks**

Thanks @ilyaglow for contributing!
