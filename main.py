import random
import time
import uuid
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
import logging
import json
import threading

# Kafka Configuration
KAFKA_BROKERS = 'localhost:29092,localhost:29093,localhost:29094'
NUM_PARTITIONS = 5
REPLICATION_FACTOR = 3
TOPIC_NAME = "Financial_Transactions"

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

producer_conf = {
    'bootstrap.servers': KAFKA_BROKERS,
    'queue.buffering.max.messages': 1000,
    'queue.buffering.max.kbytes' : 512000,
    'batch.num.messages' : 1000,
    'linger.ms' : 10,
    'acks' : 1,
    'compression.type' : 'gzip'
}

producer = Producer(producer_conf)

def create_topic(topic_name):
    admin_client = AdminClient({'bootstrap.servers': KAFKA_BROKERS})

    try:
        # Fetch metadata for existing topics
        metadata = admin_client.list_topics(timeout=10)
        if topic_name not in metadata.topics:
            # Define the new topic
            topic = NewTopic(
                topic=topic_name,
                num_partitions=NUM_PARTITIONS,
                replication_factor=REPLICATION_FACTOR
            )
            # Create the topic
            fs = admin_client.create_topics([topic])
            for topic, future in fs.items():
                try:
                    future.result()  # Wait for the operation to complete
                    logger.info(f"Topic '{topic_name}' created successfully")
                except Exception as e:
                    logger.error(f"Failed to create topic '{topic_name}': {e}")
        else:
            logger.info(f"Topic '{topic_name}' already exists")
    except Exception as e:
        logger.error(f"Failed to create topic: {e}")


def generate_transactions():
    return dict(
        transactionId = str(uuid.uuid4()),
        userId = f"user_{random.randint(1, 100)}",
        amount = round(random.uniform(50000, 150000), 2),
        transactionTime = int(time.time()),
        merchanId = random.choice(["merchant_1","merchant_2","merchant_3","merchant_4","merchant_5"]),
        transactionType = random.choice(["buy","refund"]),
        location = f'location_{random.randint(1, 50)}',
        paymentMethod = random.choice(["credit_card","PayPal","bank_tranfer","flousi"]),
        isInernational = random.choice([True,False]),
        currency = random.choice(["EUR","GBP","USD","TND"])
    )




def delivery_report(err, msg):
    if err is not None:
        print(f'Delivery failed for record {msg.key()}')
    else:
        print(f'Record {msg.key()} successfully produced ')

def produce_transaction(thread_id):
    while True:
        transaction = generate_transactions()
        try:
            producer.produce(
                topic=TOPIC_NAME,
                key = transaction["userId"],
                value=json.dumps(transaction),
                on_delivery= delivery_report
            )
            print(f" Thread {thread_id} - Produced transaction: {transaction}")
            producer.flush()
        except Exception as e:
            print(f"Failed sending transaction: {e}")

def producer_data_in_parallel(num_threads):
    threads = []
    try:
        for i in range(num_threads):
            thread = threading.Thread(target=produce_transaction, args=(i,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
    except Exception as e:
        print(f"Failed sending data: {e}")



if __name__ == '__main__':
    create_topic(TOPIC_NAME)

    producer_data_in_parallel(3)
