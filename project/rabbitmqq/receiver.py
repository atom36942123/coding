#client
import pika
credentials = pika.PlainCredentials("rabbitmq","password")
connection= pika.BlockingConnection(pika.ConnectionParameters(host="localhost", credentials= credentials))
channel = connection.channel()
channel.queue_declare(queue='hello')

#callback
def callback(ch, method, properties, body):
        print(body)

#logic
def main():
    channel.basic_consume(queue='hello',on_message_callback=callback,auto_ack=True)
    print('waiting for messages')
    channel.start_consuming()

#main
import sys,os
if __name__ == '__main__':
    try:main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:sys.exit(0)
        except SystemExit:os._exit(0)
            
        
            