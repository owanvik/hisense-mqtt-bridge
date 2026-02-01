#!/usr/bin/env python3
"""Test forskjellige kommandoer mot TV"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HomeAssistant"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet!")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode()) if msg.payload else {}
        topic = msg.topic
        
        # Vis interessante meldinger
        if any(x in topic for x in ["state", "source", "volume"]) and "broadcast" in topic:
            print(f"📨 {topic.split('/')[-1]}: {payload}")
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

def send_key(key):
    print(f"\n📤 Sender {key}...")
    client.publish(f"/remoteapp/tv/remote_service/{CLIENT_ID}/actions/sendkey",
                  json.dumps({"keytype": "keypress", "keyvalue": key}))
    time.sleep(2)

# Test forskjellige taster
print("\n" + "="*50)
print("TEST 1: Mute (bør vise mute-ikon på TV)")
print("="*50)
send_key("KEY_MUTE")

print("\n" + "="*50)  
print("TEST 2: Unmute")
print("="*50)
send_key("KEY_MUTE")

print("\n" + "="*50)
print("TEST 3: Menu (bør åpne meny)")
print("="*50)
send_key("KEY_MENU")

print("\n" + "="*50)
print("TEST 4: Back (bør lukke meny)")
print("="*50)
send_key("KEY_BACK")

print("\n" + "="*50)
print("TEST 5: Home")
print("="*50)
send_key("KEY_HOME")

client.loop_stop()
print("\n👀 Så du noe skje på TV-en?")
