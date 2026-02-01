#!/usr/bin/env python3
"""Test alternative volum-metoder"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HASoverom"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet!")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode()) if msg.payload else {}
        if "volume" in msg.topic.lower() or "volume" in str(payload).lower():
            print(f"📨 {msg.topic.split('/')[-1]}: {payload}")
    except:
        pass

client = mqtt.Client(
    client_id=CLIENT_ID,
    protocol=mqtt.MQTTv311,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.username_pw_set("hisenseservice", "multimqttservice")
client.tls_set(certfile=CERT_FILE, keyfile=KEY_FILE, cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
client.on_connect = on_connect
client.on_message = on_message

print(f"🔄 Kobler til...")
client.connect(TV_IP, TV_PORT, 60)
client.loop_start()
time.sleep(2)

print("\n" + "="*50)
print("METODE 1: Direkte volum-setting (setvolume)")
print("="*50)
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/setvolume",
              json.dumps({"volume_type": 0, "volume_value": 15}))
time.sleep(2)
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume", "")
time.sleep(1)

print("\n" + "="*50)
print("METODE 2: changevolume")
print("="*50)
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/changevolume",
              json.dumps({"volume_type": 0, "volume_value": 20}))
time.sleep(2)
client.publish(f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume", "")
time.sleep(1)

print("\n" + "="*50)
print("METODE 3: KEY_0 (tall-tast test)")
print("="*50)
client.publish(f"/remoteapp/tv/remote_service/{CLIENT_ID}/actions/sendkey",
              json.dumps({"keytype": "keypress", "keyvalue": "KEY_0"}))
time.sleep(2)

print("\n" + "="*50)
print("METODE 4: Endre til HDMI1")
print("="*50)
client.publish(f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/changesource",
              json.dumps({"sourceid": "HDMI1"}))
time.sleep(3)

print("\n👀 Skjedde noe på TV-en?")
client.loop_stop()
