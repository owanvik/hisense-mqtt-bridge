#!/usr/bin/env python3
"""Test sending key to Hisense TV"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = '10.0.0.109'
TV_PORT = 36669
TV_MAC = 'a062fb1bf2e1'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, 'rcm_certchain_pem.cer')
KEY_FILE = os.path.join(SCRIPT_DIR, 'rcm_pem_privkey.pkcs8')

client = mqtt.Client(
    client_id='HABridge',
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set('hisenseservice', 'multimqttservice')
client.tls_set(certfile=CERT_FILE, keyfile=KEY_FILE, cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)

key_sent = False

def on_connect(client, userdata, flags, rc, props=None):
    global key_sent
    if rc == 0:
        print('✅ Tilkoblet TV!')
        client.subscribe('#')
        
        # Prøv forskjellige topic-formater
        topics_to_try = [
            f'/remoteapp/tv/remote_service/{TV_MAC}$normal/actions/sendkey',
            f'/remoteapp/tv/remote_service/HABridge/actions/sendkey',
            f'/remoteapp/tv/ui_service/HABridge/actions/sendkey',
        ]
        
        payload = json.dumps({'keytype': 'keypress', 'keyvalue': 'KEY_VOLUMEUP'})
        
        for topic in topics_to_try:
            print(f'📤 Prøver: {topic}')
            client.publish(topic, payload)
            time.sleep(0.5)
        
        key_sent = True

def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode())
        if 'volume' in topic.lower() or 'volume' in str(payload).lower():
            print(f'🔊 Volum-respons: {payload}')
    except:
        pass

client.on_connect = on_connect
client.on_message = on_message

print(f'🔄 Kobler til {TV_IP}:{TV_PORT}...')
client.connect(TV_IP, TV_PORT, 60)
client.loop_start()

# Vent på tilkobling og sending
timeout = 10
start = time.time()
while not key_sent and time.time() - start < timeout:
    time.sleep(0.5)

# Vent litt på respons
time.sleep(3)

client.loop_stop()
client.disconnect()
print('👋 Ferdig')
