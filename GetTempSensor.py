import json
import time
import os
import requests
import re
import signal
from influxdb import InfluxDBClient

HUE_BRIDGE_IP = os.environ.get('HUE_BRIDGE_IP')
HUE_API_TOKEN = os.environ.get('HUE_API_TOKEN')

INFLUX_DB_HOST = os.environ.get('INFLUX_DB_HOST', 'influxdb')
INFLUX_DB_PORT = int(os.environ.get('INFLUX_DB_PORT', 8086))

API_URL = 'http://{}/api/{}/sensors'.format(HUE_BRIDGE_IP, HUE_API_TOKEN)


def format_id(id):
    return re.sub('-[0-9]*$', '', id)


def insert_point(client, name, value):
    json_body = [
        {
            "measurement": "temperature_sensor",
            "tags": {
                "name": name
            },
            "fields": {
                "value": value
            }
        }
    ]

    client.write_points(json_body)


def query_hue_sensors():
    response = requests.get(API_URL)

    response.raise_for_status()

    content = json.loads(response.content.decode('utf-8'))

    sensor_names = {}
    for sensor in list(filter(lambda x: x['type'] == 'ZLLPresence', content.values())):
        sensor_names[format_id(sensor['uniqueid'])] = sensor['name']

    return list(map(lambda x: {
        'id': format_id(x['uniqueid']),
        'name': sensor_names[format_id(x['uniqueid'])],
        'temp': x['state']['temperature'] / 100
    }, filter(lambda x: x['type'] == 'ZLLTemperature', content.values())))


def exit_gracefully():
    exit(0)


signal.signal(signal.SIGTERM, exit_gracefully)

if __name__ == '__main__':

    client = InfluxDBClient(INFLUX_DB_HOST, INFLUX_DB_PORT, database='temperature')

    try:
        start_time = time.time()
        while True:
            temp_sensors = query_hue_sensors()
            for temp_sensor in temp_sensors:
                print(temp_sensor)

                insert_point(client, temp_sensor['name'], temp_sensor['temp'])

            time.sleep(60.0 - ((time.time() - start_time) % 60.0))

    except KeyboardInterrupt:
        exit_gracefully()
