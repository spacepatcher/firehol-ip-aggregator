### fia-client

This client is designed for easy integration with the FIA API service in various python scripts.

### Usage

Install fia-client by command:
```
pip install fia-client
```

Create client object from python3 console:
```
from fia_client import fia_client
client = fia_client.FIAClient(fia_url="http://127.0.0.1:8000/")
```

Generate search requests to FIA API using fia-client:
```
result = client.search(["8.8.8.8"])
```