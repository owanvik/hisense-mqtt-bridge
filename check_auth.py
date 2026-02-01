#!/usr/bin/env python3
"""Sjekk auth-status og re-autentiser om nødvendig"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os
import sys

TV_IP = "10.0.0.109"
TV_PORT = 36669
CLIENT_ID = "HomeAssistant"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

needs_auth = False
auth_done = False

def on_connect(client, userdata, flags, rc, props=None):
    print(f"✅ Tilkoblet TV!")
    client.subscribe("#")
    
def on_message(client, userdata, msg):
    global needs_auth, auth_done
    
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode()) if msg.payload else {}
    except:
        payload = {}
    
    # Sjekk authentication-meldinger
    if "authentication" in topic and "code" not in topic:
        print(f"🔐 Auth melding: {topic}")
        print(f"   Data: {payload}")
        
        if not payload or payload == {}:
            print("⚠️ TRENGER AUTENTISERING!")
            needs_auth = True
        elif "result" in payload:
            if payload["result"] == 1:
                print("✅ ALLEREDE AUTORISERT!")
                auth_done = True
            else:
                print(f"❓ Auth result: {payload}")
                
    elif "authenticationcode" in topic:
        print(f"🔑 Auth code respons: {payload}")
        if payload.get("result") == 1:
            print("✅ AUTENTISERING VELLYKKET!")
            auth_done = True

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

print(f"🔄 Kobler til TV med client_id: {CLIENT_ID}...")
client.connect(TV_IP, TV_PORT, 60)
client.loop_start()

time.sleep(3)

if needs_auth:
    print("\n" + "="*50)
    print("📺 Se på TV-skjermen for koden!")
    print("="*50)
    code = input("Skriv inn koden fra TV: ").strip()
    
    if code:
        payload = json.dumps({"authNum": code})
        topic = f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/authenticationcode"
        client.publish(topic, payload)
        print(f"📤 Sendte kode: {code}")
        time.sleep(3)
else:
    print("\n📊 Tester volum-kontroll...")
    client.publish("/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume", "")
    time.sleep(1)
    
    print("📤 Sender KEY_VOLUMEUP...")
    client.publish("/remoteapp/tv/remote_service/HomeAssistant/actions/sendkey",
                  json.dumps({"keytype": "keypress", "keyvalue": "KEY_VOLUMEUP"}))
    time.sleep(1)
    
    client.publish("/remoteapp/tv/platform_service/HomeAssistant/actions/getvolume", "")
    time.sleep(1)

client.loop_stop()
