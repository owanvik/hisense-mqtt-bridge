#!/usr/bin/env python3
"""Test med ny client_id"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import random

# Ny unik client_id
CLIENT_ID = f'HATest{random.randint(1000,9999)}'

print(f'Bruker ny client_id: {CLIENT_ID}')

client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set('hisenseservice', 'multimqttservice')
client.tls_set(certfile='rcm_certchain_pem.cer', keyfile='rcm_pem_privkey.pkcs8', cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)

auth_needed = False

def on_msg(c, u, m):
    global auth_needed
    try:
        p = json.loads(m.payload.decode()) if m.payload else {}
        if 'volume' in m.topic.lower():
            print(f'  Volum: {p}')
        if 'authentication' in m.topic and 'code' not in m.topic:
            if not p or p.get('result') != 1:
                auth_needed = True
                print('⚠️ TRENGER AUTH - se på TV!')
    except: pass

client.on_message = on_msg
client.connect('10.0.0.109', 36669, 60)
client.subscribe('#')
client.loop_start()
time.sleep(3)

if auth_needed:
    code = input('Skriv inn kode fra TV: ').strip()
    if code:
        client.publish(f'/remoteapp/tv/ui_service/{CLIENT_ID}/actions/authenticationcode', 
                      json.dumps({'authNum': code}))
        time.sleep(2)

print('\nSetter volum til 12...')
client.publish(f'/remoteapp/tv/platform_service/{CLIENT_ID}/actions/changevolume', 
              json.dumps({'volume_type': 0, 'volume_value': 12}))
time.sleep(2)

print('\nHenter volum...')
client.publish(f'/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume', '')
time.sleep(2)

print('\n👀 Sjekk volumet på TV!')
client.loop_stop()
