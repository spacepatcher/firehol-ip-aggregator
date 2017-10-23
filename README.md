# Firehol-IP-Aggregator
Аpplication for keeping reputation feeds from https://github.com/firehol/blocklist-ipsets (.netset and .ipset only) data in relational database PostgreSQL with including historical data

`client.py` - Simple python script for convenient interaction with FIA API.

`app/conf/config.json` - The main configuration file with several parameters. `"unique_ips_limit"` is the most interesting one, with his help you can limit the set of Firehol feeds based on the number of unique IP addresses.


Here is an example of the result of the request ip using the client (`python client.py -s 8.8.8.8`):
```
{
    "8.8.8.8": {
        "categories": [
            "reputation", 
            "malware"
        ], 
        "feeds_available": 158, 
        "first_seen": "2017-10-23T15:08:46.089022+00:00", 
        "hits": [
            {
                "category": "reputation", 
                "entries": "23 unique IPs", 
                "feed_name": "packetmail_emerging_ips", 
                "first_seen": "2017-10-23T15:08:46.089022+00:00", 
                "last_added": "2017-10-23T15:08:46.089022+00:00", 
                "list_source_url": "https://www.packetmail.net/iprep_emerging_ips.txt", 
                "maintainer": "PacketMail.net", 
                "maintainer_url": "https://www.packetmail.net/", 
                "source_file_date": "Mon Oct 23 08:55:05 UTC 2017"
            }, 
            {
                "category": "reputation", 
                "entries": "33927 unique IPs", 
                "feed_name": "hphosts_psh", 
                "first_seen": "2017-10-23T15:12:52.563252+00:00", 
                "last_added": "2017-10-23T15:12:52.563252+00:00", 
                "list_source_url": "http://hosts-file.net/psh.txt", 
                "maintainer": "hpHosts", 
                "maintainer_url": "http://hosts-file.net/", 
                "source_file_date": "Sun Oct 22 20:02:30 UTC 2017"
            }, 
            {
                "category": "reputation", 
                "entries": "27388 unique IPs", 
                "feed_name": "hphosts_fsa", 
                "first_seen": "2017-10-23T15:12:29.365978+00:00", 
                "last_added": "2017-10-23T15:12:29.365978+00:00", 
                "list_source_url": "http://hosts-file.net/fsa.txt", 
                "maintainer": "hpHosts", 
                "maintainer_url": "http://hosts-file.net/", 
                "source_file_date": "Sun Oct 22 10:24:52 UTC 2017"
            }, 
            {
                "category": "malware", 
                "entries": "28000 unique IPs", 
                "feed_name": "hphosts_emd", 
                "first_seen": "2017-10-23T15:12:26.819655+00:00", 
                "last_added": "2017-10-23T15:12:26.819655+00:00", 
                "list_source_url": "http://hosts-file.net/emd.txt", 
                "maintainer": "hpHosts", 
                "maintainer_url": "http://hosts-file.net/", 
                "source_file_date": "Sun Oct 22 10:31:51 UTC 2017"
            }
        ], 
        "hits_count": 4, 
        "last_added": "2017-10-23T15:12:52.563252+00:00"
    }
}
```

To start the collection module and the API server locally, just type:
```
sudo docker-compose up -d
```
