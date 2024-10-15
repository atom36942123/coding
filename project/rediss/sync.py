#client
import redis
pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
client = redis.Redis(connection_pool=pool)

#set
client.set('atom', 'self is the path')

#get
print(client.get('atom'))
