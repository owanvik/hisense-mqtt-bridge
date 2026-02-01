#!/usr/bin/env python3
"""
Hisense TV MQTT Debug - Viser ALLE meldinger fra TV-en
"""

import ssl
import socket
import time
import json
import os
import paho.mqtt.client as mqtt

TV_IP = "10.0.0.109"
PORT = 36669
CLIENT_ID = "HomeAssistant"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_CERT = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
CLIENT_KEY = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

connected = False
all_messages = []

def on_connect(client, userdata, flags, rc, properties=None):
    global connected
    if rc == 0:
        print("✅ MQTT tilkoblet!")
        connected = True
        client.subscribe("#")
    else:
        print(f"❌ Feil: {rc}")

def on_message(client, userdata, msg):
    global all_messages
    topic = msg.topic
    try:
        payload = msg.payload.decode("utf-8", errors="ignore")
    except:
        payload = str(msg.payload)
    
    all_messages.append((topic, payload))
    
    # Vis alle meldinger med full detalj
    print(f"\n{'='*60}")
    print(f"📩 TOPIC: {topic}")
    print(f"{'='*60}")
    
    if payload:
        try:
            data = json.loads(payload)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(f"RAW: {payload[:500]}")
    else:
        print("(tom melding)")

def on_disconnect(client, userdata, rc, properties=None, reasonCode=None):
    print("🔌 Frakoblet")

def main():
    global connected
    
    print("=" * 60)
    print("   HISENSE TV MQTT DEBUG")
    print(f"   Viser ALLE meldinger fra {TV_IP}")
    print("=" * 60)
    
    # Sjekk tilgang
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    if sock.connect_ex((TV_IP, PORT)) != 0:
        print("❌ TV-en svarer ikke")
        return
    sock.close()
    
    # Koble til
    client = mqtt.Client(
        client_id=CLIENT_ID,
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    client.username_pw_set("hisenseservice", "multimqttservice")
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    client.tls_set(
        ca_certs=None,
        certfile=CLIENT_CERT,
        keyfile=CLIENT_KEY,
        cert_reqs=ssl.CERT_NONE,
        tls_version=ssl.PROTOCOL_TLS_CLIENT,
    )
    client.tls_insecure_set(True)
    
    client.connect(TV_IP, PORT, keepalive=30)
    client.loop_start()
    
    for _ in range(20):
        if connected:
            break
        time.sleep(0.5)
    
    if not connected:
        print("❌ Kunne ikke koble til")
        return
    
    print("\n" + "=" * 60)
    print("Skriv kommandoer for å sende til TV-en:")
    print("  1 = gettvstate")
    print("  2 = sourcelist") 
    print("  3 = applist")
    print("  4 = getvolume")
    print("  5 = KEY_VOLUMEUP")
    print("  6 = KEY_VOLUMEDOWN")
    print("  7 = Vis alle mottatte topics")
    print("  q = Avslutt")
    print("=" * 60)
    
    base = "/remoteapp/tv"
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == "q":
                break
            elif cmd == "1":
                topic = f"{base}/ui_service/{CLIENT_ID}/actions/gettvstate"
                print(f"📤 Sender til: {topic}")
                client.publish(topic, "")
            elif cmd == "2":
                topic = f"{base}/ui_service/{CLIENT_ID}/actions/sourcelist"
                print(f"📤 Sender til: {topic}")
                client.publish(topic, "")
            elif cmd == "3":
                topic = f"{base}/ui_service/{CLIENT_ID}/actions/applist"
                print(f"📤 Sender til: {topic}")
                client.publish(topic, "")
            elif cmd == "4":
                topic = f"{base}/platform_service/{CLIENT_ID}/actions/getvolume"
                print(f"📤 Sender til: {topic}")
                client.publish(topic, "")
            elif cmd == "5":
                topic = f"{base}/remote_service/{CLIENT_ID}/actions/sendkey"
                print(f"📤 Sender KEY_VOLUMEUP")
                client.publish(topic, "KEY_VOLUMEUP")
            elif cmd == "6":
                topic = f"{base}/remote_service/{CLIENT_ID}/actions/sendkey"
                print(f"📤 Sender KEY_VOLUMEDOWN")
                client.publish(topic, "KEY_VOLUMEDOWN")
            elif cmd == "7":
                print("\n📋 ALLE MOTTATTE TOPICS:")
                unique_topics = sorted(set(t for t, p in all_messages))
                for t in unique_topics:
                    print(f"   {t}")
            else:
                # Send custom topic/message
                if ":" in cmd:
                    topic, msg = cmd.split(":", 1)
                    client.publish(topic.strip(), msg.strip())
                    print(f"📤 Sendt: {topic.strip()} -> {msg.strip()}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        print("\n👋 Avsluttet")
        
        # Skriv ut oppsummering
        print(f"\n📊 Mottok totalt {len(all_messages)} meldinger")
        print("Unike topics:")
        for t in sorted(set(t for t, p in all_messages)):
            print(f"   {t}")

if __name__ == "__main__":
    main()
