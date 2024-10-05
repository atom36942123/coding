#run celery from 1st terminal from script folder=celery -A celeryy.client worker --loglevel=info
#run fastapi from 2nd terminal from script folder= uvicorn celeryy:app --reload
#run flower from 3rd terminal from script folder(http://localhost:5555/)=celery -A celeryy.client flower --port=5555

#celery
import time
from celery import shared_task, Celery
# client=Celery(__name__,broker="redis://127.0.0.1:6379/0",backend="redis://127.0.0.1:6379/0")
# client = Celery('tasks', broker='pyamqp://guest@localhost//')
client = Celery('tasks', backend='redis://localhost', broker='pyamqp://guest@localhost//')

@client.task
def send_push_notification(device_token: str):
    time.sleep(10)  # simulates slow network call to firebase/sns
    with open("notification.log", mode="a") as notification_log:
        response = f"Successfully sent push notification to: {device_token}\n"
        notification_log.write(response)
        
#fastapi
from fastapi import FastAPI
app = FastAPI()
@app.get("/push/{device_token}")
async def notify(device_token: str):
    send_push_notification.delay(device_token)
    return {"message": "Notification sent"}

