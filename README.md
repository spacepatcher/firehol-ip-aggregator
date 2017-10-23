# Firehol-IP-Aggregator
Аpplication for keeping reputation feeds from https://github.com/firehol/blocklist-ipsets (.netset and .ipset only) data in relational database PostgreSQL with including historical data

`client.py` - Simple python script for convenient interaction with FIA API.

`app/conf/config.json` - The main configuration file with several parameters. `"unique_ips_limit"` is the most interesting one, with his help you can limit the set of Firehol feeds based on the number of unique IP addresses.


Here is an example of the result of the request ip using the client (`python client.py -s 8.8.8.8`):
```
{
    "8.8.8.8": [
        {
            "category": "reputation",
            "entries": "23 unique IPs",
            "feed_name": "packetmail_emerging_ips",
            "first_seen": "2017-10-23T07:46:13.696159+00:00",
            "last_added": "2017-10-23T07:46:13.696159+00:00",
            "list_source_url": "https://www.packetmail.net/iprep_emerging_ips.txt",
            "maintainer": "PacketMail.net",
            "maintainer_url": "https://www.packetmail.net/",
            "source_file_date": "Sun Oct 22 08:55:06 UTC 2017"
        }
    ]
}

```

To start the collection module and the API server locally, just type:
```
sudo docker-compose up -d
```
