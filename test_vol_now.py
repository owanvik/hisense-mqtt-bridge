#!/usr/bin/env python3
"""Lytt og test volum"""

import ssl
import json
import time
from paho.mqtt import client as mqtt_client

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HAVolLytt"

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
        if "volume" in msg.topic.lower() or "volume" in str(data).lower():
            print(f"🔊 {msg.topic.split('/')[-1]}: {data}")
    except:
        pass

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Tilkoblet TV")
    client.subscribe("/remoteapp/#")

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

# Hent nåværende volum
print("\n📥 Henter volum...")
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume", "")
time.sleep(2)

# Prøv å sette volum til 12
print("\n📤 Setter volum til 12...")
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/changevolume", "12")
time.sleep(3)

print("\n" + "="*50)
print("👀 Er volumet nå 12? (var 7)")
print("="*50)

client.loop_stop()
client.disconnect()
