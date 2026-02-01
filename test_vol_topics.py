#!/usr/bin/env python3
"""Test forskjellige topic-mønstre for volume"""

import ssl
import json
import time
from paho.mqtt import client as mqtt_client

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HAVolTest"

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
ssl_context.load_cert_chain(
    certfile="rcm_certchain_pem.cer",
    keyfile="rcm_pem_privkey.pkcs8"
)

responses = []

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"  📩 {msg.topic}: {data}")
        responses.append(data)
    except:
        print(f"  📩 {msg.topic}: {msg.payload}")

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Tilkoblet TV")
    # Subscribe til alt
    client.subscribe("/remoteapp/tv/#")

client = mqtt_client.Client(
    callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
    client_id=CLIENT_ID
)
client.username_pw_set("hisenseservice", "multimqttservice")
client.tls_set_context(ssl_context)
client.on_connect = on_connect
client.on_message = on_message

print("Kobler til TV...")
client.connect(TV_IP, TV_PORT)
client.loop_start()
time.sleep(2)

# Test forskjellige topics for volume
tests = [
    # ui_service (som changesource bruker)
    (f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/changevolume", {"volume_type": 0, "volume_value": 15}),
    
    # remote_service
    (f"/remoteapp/tv/remote_service/{CLIENT_ID}/actions/changevolume", {"volume_type": 0, "volume_value": 15}),
    
    # Prøv volumechange i stedet for changevolume
    (f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/volumechange", {"volume_type": 0, "volume_value": 15}),
    
    # Prøv setvolume
    (f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/setvolume", {"volume_type": 0, "volume_value": 15}),
    (f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/setvolume", {"volume_type": 0, "volume_value": 15}),
    
    # Prøv volume uten change/set prefix
    (f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/volume", {"volume_type": 0, "volume_value": 15}),
    
    # Prøv med "value" i stedet for "volume_value"
    (f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/changevolume", {"volume_type": 0, "value": 15}),
    
    # Prøv med bare tall
    (f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/changevolume", 15),
]

for topic, payload in tests:
    responses.clear()
    print(f"\n🔊 Tester: {topic.split('/actions/')[1] if '/actions/' in topic else topic}")
    print(f"   Payload: {payload}")
    
    if isinstance(payload, dict):
        client.publish(topic, json.dumps(payload))
    else:
        client.publish(topic, str(payload))
    
    time.sleep(2)
    
    if responses:
        print(f"   ✅ Fikk svar!")
    else:
        print(f"   ❌ Ingen svar")

print("\n" + "="*50)
print("👀 Sjekk volumet på TV nå!")
print("="*50)

client.loop_stop()
client.disconnect()
