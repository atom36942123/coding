#client
import pika
credentials = pika.PlainCredentials("rabbitmq","password")
connection= pika.BlockingConnection(pika.ConnectionParameters(host="localhost", credentials= credentials))
channel = connection.channel()

#send
channel.queue_declare(queue='hello')
channel.basic_publish(exchange='', routing_key='hello', body="xxx")
print("msg sent")

#close
connection.close