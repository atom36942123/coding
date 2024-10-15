from kafka import KafkaConsumer
consumer=KafkaConsumer('POC',group_id='my-group',bootstrap_servers=['localhost:9092'])
for message in consumer:
   print(message)
   print(message.key,message.value)