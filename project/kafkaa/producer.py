from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
future = producer.send('POC', key=b'atom', value=b'self is the path')
record_metadata = future.get(timeout=10)
producer.flush()
