#!/usr/bin/env python3
"""Test forskjellige sendkey-formater"""

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
    client_id='HomeAssistant',
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set('hisenseservice', 'multimqttservice')
client.tls_set(certfile=CERT_FILE, keyfile=KEY_FILE, cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)

def on_connect(client, userdata, flags, rc, props=None):
    if rc == 0:
        print('✅ Tilkoblet TV!')
        client.subscribe('#')
        
        # Prøv forskjellige payload-formater
        payloads = [
            # Format 1: Standard
            {"keytype": "keypress", "keyvalue": "KEY_VOLUMEUP"},
            # Format 2: Uten keytype
            {"keyvalue": "KEY_VOLUMEUP"},
            # Format 3: Med action
            {"action": "sendkey", "keyvalue": "KEY_VOLUMEUP"},
            # Format 4: Lowercase
            {"keytype": "keypress", "keyvalue": "volumeup"},
            # Format 5: Bare string
        ]
        
        topic = f'/remoteapp/tv/remote_service/HomeAssistant/actions/sendkey'
        
        for i, payload in enumerate(payloads):
            print(f'📤 Format {i+1}: {payload}')
            client.publish(topic, json.dumps(payload))
            time.sleep(1)
        
        # Prøv også som ren string
        print(f'📤 Format 6: KEY_VOLUMEUP (string)')
        client.publish(topic, 'KEY_VOLUMEUP')
        time.sleep(1)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload_str = msg.payload.decode('utf-8', errors='ignore')
    
    # Vis alle meldinger
    if 'sendkey' not in topic and payload_str:
        try:
            data = json.loads(payload_str)
            # Sjekk om det er volum-respons
            if 'volume' in str(data).lower():
                print(f'🔊 {data}')
        except:
            if len(payload_str) < 100:
                print(f'📩 {topic}: {payload_str}')

client.on_connect = on_connect
client.on_message = on_message

print(f'🔄 Kobler til {TV_IP}:{TV_PORT}...')
client.connect(TV_IP, TV_PORT, 60)
client.loop_start()

time.sleep(10)

client.loop_stop()
client.disconnect()
print('👋 Ferdig')
