#start rabbitmq image from docker
#run=python rabbitmq_send.py

import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='hello')

for item in ["i","am","om"]:
   channel.basic_publish(exchange='', routing_key='hello', body=item)
   print(f"msg={item}")

connection.close()