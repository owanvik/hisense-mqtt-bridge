#!/usr/bin/env python3
"""Test changevolume med bare tall som payload (ikke JSON)"""

import ssl
import json
import time
from paho.mqtt import client as mqtt_client

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HAVol123"

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
        print(f"  📩 {msg.topic.split('/')[-1]}: {msg.payload.decode()}")

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Tilkoblet TV")
    client.subscribe("/remoteapp/tv/#")
    # Subscribe til broadcast også
    client.subscribe("/remoteapp/mobile/#")

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

# Test 1: Sett volum til 15 med bare tallet (som den originale integrasjonen gjør)
topic = f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/changevolume"
print(f"\n🔊 Test 1: Sender bare tallet 15 (ikke JSON)")
client.publish(topic, "15")
time.sleep(2)

# Test 2: Sett volum til 10 med bare tallet
print(f"\n🔊 Test 2: Sender bare tallet 10")
client.publish(topic, "10")
time.sleep(2)

# Test 3: Prøv med int i stedet for string
print(f"\n🔊 Test 3: Sender int 12")
client.publish(topic, 12)
time.sleep(2)

print("\n" + "="*50)
print("👀 Sjekk volumet på TV nå! Er det 12?")
print("="*50)

client.loop_stop()
client.disconnect()
