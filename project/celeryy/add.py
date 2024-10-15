#add task in redis queue
from task import log_write
result=log_write.delay()
print(f"tak added with id={result.id}")
