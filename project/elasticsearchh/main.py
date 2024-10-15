#client
from elasticsearch import Elasticsearch
CERT_FINGERPRINT = "FA:5F:BD:32:54:0B:80:F4:A4:51:2D:C3:93:1E:0E:30:E6:D7:38:A6:24:DB:2F:33:5B:A9:9C:8E:65:FB:99:8B"
client = Elasticsearch("https://localhost:9200",basic_auth=("elastic", "password"),ssl_assert_fingerprint=CERT_FINGERPRINT,verify_certs=True)
print(client.info())

#index
if False:client.indices.create(index="test-index")

#create
doc = {'author': 'atom','conent': 'self is the path'}
resp = client.index(index="test-index", id=1, document=doc)
resp = client.index(index="test-index", id=2, document=doc)
print(resp['result'])

#read
resp = client.get(index="test-index", id=1)
print(resp['_source'])

#refresh
client.indices.refresh(index="test-index")

#search
resp = client.search(index='test-index', body={'query': {'match': {'author': 'atom'}}})
print("Got %d Hits:" % resp['hits']['total']['value'])

#update
doc = {'author': 'atom','conent': 'self is the paths'}
resp = client.update(index="test-index", id=1, doc=doc)
print(resp['result'])

#delete
client.delete(index="test-index", id=2)




