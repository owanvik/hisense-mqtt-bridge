#!/usr/bin/env python3
"""Test volumeup/volumedown actions"""

import ssl
import json
import time
from paho.mqtt import client as mqtt_client

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HAVolUD"

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
ssl_context.load_cert_chain(
    certfile="rcm_certchain_pem.cer",
    keyfile="rcm_pem_privkey.pkcs8"
)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"  📩 {msg.topic.split('/')[-1]}: {data}")
    except:
        print(f"  📩 {msg.topic}: {msg.payload}")

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Tilkoblet TV")
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

# Test volumeup/volumedown/mute actions
services = ["platform_service", "ui_service", "remote_service"]
actions = ["volumeup", "volumedown", "mute", "unmute", "volume_up", "volume_down"]

print("\n🔊 Tester volumeup/volumedown actions...")

for service in services:
    for action in actions:
        topic = f"/remoteapp/tv/{service}/{CLIENT_ID}/actions/{action}"
        print(f"\n   {service}/{action}...", end=" ", flush=True)
        client.publish(topic, "{}")
        time.sleep(0.5)
        
print("\n\n" + "="*50)
print("👀 Sjekk volumet på TV! Gikk det opp/ned?")
print("="*50)

client.loop_stop()
client.disconnect()
