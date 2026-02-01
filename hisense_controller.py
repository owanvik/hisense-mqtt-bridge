#!/usr/bin/env python3
"""
Hisense TV MQTT Controller med klientsertifikater

Din TV:
- Navn: Stue
- IP: 10.0.0.109
- transport_protocol: 2152
- MAC: a062fb1bf2e1
"""

import ssl
import socket
import time
import json
import os
import paho.mqtt.client as mqtt

# === KONFIGURASJON ===
TV_IP = "10.0.0.109"
PORT = 36669
CLIENT_ID = "HomeAssistant"

# Sertifikater (relativt til script-katalogen)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_CERT = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
CLIENT_KEY = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

# MQTT Credentials
MQTT_USERNAME = "hisenseservice"
MQTT_PASSWORD = "multimqttservice"

# Status
connected = False
messages = []

def on_connect(client, userdata, flags, rc, properties=None):
    global connected
    codes = {
        0: "OK - Tilkoblet!",
        1: "Feil protokollversjon",
        2: "Ugyldig klient-ID",
        3: "Server utilgjengelig",
        4: "Feil brukernavn/passord",
        5: "Ikke autorisert"
    }
    if rc == 0:
        print(f"✅ {codes[0]}")
        connected = True
        client.subscribe("#")
    else:
        print(f"❌ Tilkobling feilet: {codes.get(rc, f'Ukjent feil {rc}')}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8", errors="ignore")
        messages.append((msg.topic, payload))
        
        # Parse JSON hvis mulig
        try:
            data = json.loads(payload)
            print(f"\n📩 {msg.topic}")
            print(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")
        except:
            if payload:
                print(f"\n📩 {msg.topic}: {payload[:200]}")
    except:
        pass

def on_disconnect(client, userdata, rc, properties=None, reasonCode=None):
    global connected
    connected = False
    if rc == 0:
        print("🔌 Frakoblet (normal)")
    else:
        print(f"🔌 Frakoblet (rc={rc})")

def create_client():
    """Opprett MQTT-klient med riktig konfigurasjon"""
    client = mqtt.Client(
        client_id=CLIENT_ID,
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    return client

def try_connect_with_certs(client):
    """Prøv tilkobling med klientsertifikater"""
    print(f"\n🔐 Prøver med klientsertifikater...")
    
    if not os.path.exists(CLIENT_CERT):
        print(f"   ❌ Finner ikke: {CLIENT_CERT}")
        return False
    if not os.path.exists(CLIENT_KEY):
        print(f"   ❌ Finner ikke: {CLIENT_KEY}")
        return False
    
    print(f"   📜 Sertifikat: {os.path.basename(CLIENT_CERT)}")
    print(f"   🔑 Nøkkel: {os.path.basename(CLIENT_KEY)}")
    
    try:
        # Setup TLS med klientsertifikater
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
        
        # Vent på tilkobling
        for i in range(20):
            if connected:
                return True
            time.sleep(0.5)
        
        return connected
        
    except Exception as e:
        print(f"   ❌ Feil: {e}")
        return False

def try_connect_ssl_only(client):
    """Prøv tilkobling med bare SSL (uten klientsertifikater)"""
    print(f"\n🔐 Prøver med SSL (uten klientsertifikater)...")
    
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        client.tls_set_context(ssl_context)
        client.connect(TV_IP, PORT, keepalive=30)
        client.loop_start()
        
        for i in range(20):
            if connected:
                return True
            time.sleep(0.5)
        
        return connected
        
    except Exception as e:
        print(f"   ❌ Feil: {e}")
        return False

def try_connect_no_ssl(client):
    """Prøv tilkobling uten SSL"""
    print(f"\n🔓 Prøver uten SSL...")
    
    try:
        client.connect(TV_IP, PORT, keepalive=30)
        client.loop_start()
        
        for i in range(20):
            if connected:
                return True
            time.sleep(0.5)
        
        return connected
        
    except Exception as e:
        print(f"   ❌ Feil: {e}")
        return False

def main():
    global connected
    
    print("=" * 60)
    print("   HISENSE TV MQTT CONTROLLER")
    print("=" * 60)
    print(f"   TV: {TV_IP}:{PORT}")
    print(f"   Klient-ID: {CLIENT_ID}")
    print("=" * 60)
    
    # Sjekk nettverkstilgang
    print(f"\n🔄 Sjekker om TV-en er tilgjengelig...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((TV_IP, PORT))
        sock.close()
        
        if result != 0:
            print(f"❌ Port {PORT} er lukket. Er TV-en slått på?")
            return
        print(f"✅ Port {PORT} er åpen!")
    except Exception as e:
        print(f"❌ Nettverksfeil: {e}")
        return
    
    # Prøv forskjellige tilkoblingsmetoder
    methods = [
        ("Klientsertifikater", try_connect_with_certs),
        ("SSL uten sertifikater", try_connect_ssl_only),
        ("Uten SSL", try_connect_no_ssl),
    ]
    
    client = None
    for name, method in methods:
        connected = False
        client = create_client()
        
        if method(client):
            print(f"\n🎉 Tilkoblet med metode: {name}")
            break
        else:
            try:
                client.loop_stop()
                client.disconnect()
            except:
                pass
            client = None
    
    if not connected or client is None:
        print("\n❌ Kunne ikke koble til TV-en med noen metode.")
        print("\n💡 Mulige løsninger:")
        print("   1. Sørg for at TV-en er slått på (ikke standby)")
        print("   2. Par telefonen med VIDAA/RemoteNOW-appen først")
        print("   3. Sjekk at TV-en er på samme nettverk")
        return
    
    # Interaktiv meny
    print("\n" + "=" * 60)
    print("📺 TV er tilkoblet! Tilgjengelige kommandoer:")
    print("=" * 60)
    print("   1. Hent TV-status")
    print("   2. Hent kilder")
    print("   3. Hent apper")
    print("   4. Hent volum")
    print("   5. Volume opp")
    print("   6. Volume ned")
    print("   7. Send tast (f.eks. KEY_UP)")
    print("   8. Start YouTube")
    print("   9. Start Netflix")
    print("   0. Avslutt")
    print("-" * 60)
    
    topics = {
        "state": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/gettvstate",
        "sources": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/sourcelist",
        "apps": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/applist",
        "volume": f"/remoteapp/tv/platform_service/{CLIENT_ID}/actions/getvolume",
        "key": f"/remoteapp/tv/remote_service/{CLIENT_ID}/actions/sendkey",
        "launch": f"/remoteapp/tv/ui_service/{CLIENT_ID}/actions/launchapp",
    }
    
    try:
        while True:
            choice = input("\nVelg (0-9): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                client.publish(topics["state"], "")
                print("📺 Sendte forespørsel om TV-status...")
            elif choice == "2":
                client.publish(topics["sources"], "")
                print("📋 Sendte forespørsel om kilder...")
            elif choice == "3":
                client.publish(topics["apps"], "")
                print("📱 Sendte forespørsel om apper...")
            elif choice == "4":
                client.publish(topics["volume"], "")
                print("🔊 Sendte forespørsel om volum...")
            elif choice == "5":
                client.publish(topics["key"], "KEY_VOLUMEUP")
                print("🔊 Volume opp!")
            elif choice == "6":
                client.publish(topics["key"], "KEY_VOLUMEDOWN")
                print("🔉 Volume ned!")
            elif choice == "7":
                key = input("Tast (f.eks. KEY_UP, KEY_OK, KEY_POWER): ").strip().upper()
                if not key.startswith("KEY_"):
                    key = "KEY_" + key
                client.publish(topics["key"], key)
                print(f"🎮 Sendte: {key}")
            elif choice == "8":
                payload = json.dumps({
                    "name": "YouTube",
                    "urlType": 37,
                    "storeType": 0,
                    "url": "youtube"
                })
                client.publish(topics["launch"], payload)
                print("▶️ Starter YouTube...")
            elif choice == "9":
                payload = json.dumps({
                    "name": "Netflix",
                    "urlType": 37,
                    "storeType": 0,
                    "url": "netflix"
                })
                client.publish(topics["launch"], payload)
                print("▶️ Starter Netflix...")
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Avsluttet")

if __name__ == "__main__":
    main()
