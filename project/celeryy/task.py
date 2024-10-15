#client
from celery.app import Celery
client = Celery(__name__, broker="redis://localhost:6379", backend="redis://localhost:6379")
# client = Celery('tasks', backend='redis://localhost', broker='pyamqp://guest@localhost//')

#task
import time
@client.task
def log_write():
    time.sleep(10)
    with open("notification.log",mode="a") as notification_log:
       notification_log.write("\nxxx")
        