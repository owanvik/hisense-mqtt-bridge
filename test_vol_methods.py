#!/usr/bin/env python3
"""Test forskjellige volum-metoder"""

import paho.mqtt.client as mqtt
import ssl
import json
import time

CLIENT_ID = 'HASoverom'

client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set('hisenseservice', 'multimqttservice')
client.tls_set(certfile='rcm_certchain_pem.cer', keyfile='rcm_pem_privkey.pkcs8', cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)

def on_msg(c, u, m):
    try:
        p = json.loads(m.payload.decode())
        if 'volume' in m.topic.lower():
            print(f'  {p}')
    except: pass

client.on_message = on_msg
client.connect('10.0.0.109', 36669, 60)
client.subscribe('#')
client.loop_start()
time.sleep(2)

base = f'/remoteapp/tv/platform_service/{CLIENT_ID}/actions'

print('\n1. setvolume med volume_value=15...')
client.publish(f'{base}/setvolume', json.dumps({'volume_type': 0, 'volume_value': 15}))
time.sleep(3)

print('\n2. volumecontrol med value=12...')
client.publish(f'{base}/volumecontrol', json.dumps({'volume_type': 0, 'value': 12}))
time.sleep(3)

print('\n3. volume med level=10...')
client.publish(f'{base}/volume', json.dumps({'level': 10}))
time.sleep(3)

print('\n4. Henter volum...')
client.publish(f'{base}/getvolume', '')
time.sleep(2)

print('\n👀 Hva er volumet på TV-en?')
client.loop_stop()
