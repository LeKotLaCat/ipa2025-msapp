import pika
import time
import sys
import os
from netmiko import ConnectHandler
from pymongo import MongoClient
from bson import json_util
import datetime 

def get_mongo_connection():
    mongo_uri = os.environ.get("MONGO_URI")
    db_name = os.environ.get("DB_NAME")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    return db.interfaces

def main():
    rabbitmq_host = 'rabbitmq'
    connection = None
    while not connection:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
            print(f"Worker ({os.getpid()}) connected to RabbitMQ.")
        except pika.exceptions.AMQPConnectionError:
            print("Connection to RabbitMQ failed. Retrying in 5 seconds...")
            time.sleep(5)

    channel = connection.channel()
    channel.queue_declare(queue='router_jobs', durable=True)
    print(f' [*] Worker ({os.getpid()}) waiting for jobs. To exit press CTRL+C')

    def callback(ch, method, properties, body):
        job_data = json_util.loads(body)
        ip = job_data.get('ip')
        username = job_data.get('username')
        password = job_data.get('password')
        print(f" [x] Received job for router: {ip}")

        device = {
            'device_type': 'cisco_ios',
            'host':   ip,
            'username': username,
            'password': password,
        }

        interfaces_data = None

        try:
            with ConnectHandler(**device) as net_connect:
                output = net_connect.send_command('show ip interface brief', use_textfsm=True)
                interfaces_data = output
            
            print(f"    - DEBUG: Parsed data from {ip}:")
            import pprint
            pprint.pprint(interfaces_data)

            print(f"    - Successfully collected and parsed data from {ip}")

        except Exception as e:
            print(f"    - Failed to connect or get data from {ip}: {e}")
            interfaces_data = [{'error': str(e)}]
        
        # try:
        #     with ConnectHandler(**device) as net_connect:
        #         output = net_connect.send_command('show ip interface brief', use_textfsm=True)
        #         interfaces_data = output
        #     print(f"    - Successfully collected and parsed data from {ip}")

        # except Exception as e:
        #     print(f"    - Failed to connect or get data from {ip}: {e}")
        #     interfaces_data = [{'error': str(e)}]

        
        # บันทึก/อัปเดตข้อมูลลง MongoDB
        if interfaces_data:
            try:
                interfaces_collection = get_mongo_connection()
                # เราจะเก็บ List of Dictionaries ทั้งหมดลงใน field 'interfaces'
                
                interfaces_collection.insert_one({
                    'router_ip': ip, 
                    'interfaces': interfaces_data,
                    'timestamp': datetime.datetime.now()
                })

                #interfaces_collection.update_one(
                 #   {'ip': ip},
                  #  {'$set': {
                   #     'ip': ip, 
                    #    'interfaces': interfaces_data, # <--- เก็บข้อมูลที่ parse แล้ว
                     #   'last_updated': time.strftime("%Y-%m-%d %H:%M:%S")
                    #}},
                    #upsert=True
                #)
                
                print(f"    - Data for {ip} saved to MongoDB.")
            except Exception as e:
                print(f"    - Failed to save data for {ip} to MongoDB: {e}")

        print(" [x] Done")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='router_jobs', on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    os.environ.setdefault('MONGO_URI', 'mongodb://admin:cisco@localhost:27017/')
    os.environ.setdefault('DB_NAME', 'ipa2025_db')
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
