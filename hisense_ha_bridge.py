#!/usr/bin/env python3
"""
Hisense TV to Home Assistant MQTT Bridge

Kobler til Hisense TV via MQTT og publiserer data til Home Assistant.
Kan kjøres som en daemon eller som en-gangs polling.
"""

import paho.mqtt.client as mqtt
import ssl
import json
import time
import os
import sys
import argparse
import requests

# Hisense TV-konfigurasjon
TV_IP = "10.0.0.109"
TV_PORT = 36669
TV_MAC = "a0:62:fb:1b:f2:e1"
MQTT_USER = "hisenseservice"
MQTT_PASS = "multimqttservice"

# Home Assistant-konfigurasjon
HA_URL = "http://10.0.0.50:8123"
HA_TOKEN = os.environ.get("HA_TOKEN", "")

# Sertifikatbaner (relativt til script-mappen)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_FILE = os.path.join(SCRIPT_DIR, "rcm_certchain_pem.cer")
KEY_FILE = os.path.join(SCRIPT_DIR, "rcm_pem_privkey.pkcs8")

# MQTT Topics
MAC_CLEAN = TV_MAC.replace(":", "")
BASE_TOPIC = f"/remoteapp/tv/remote_service/{MAC_CLEAN}$normal"

class HisenseHABridge:
    def __init__(self, ha_token=None):
        self.ha_token = ha_token or HA_TOKEN
        self.client = None
        self.connected = False
        self.data = {
            "power": "unknown",
            "volume": 0,
            "muted": False,
            "source": "unknown",
            "sources": [],
            "apps": [],
            "app_name": "unknown"
        }
        self.message_received = False
        
    def setup_mqtt(self):
        """Setter opp MQTT-klient med SSL"""
        self.client = mqtt.Client(
            client_id="HABridge", 
            protocol=mqtt.MQTTv311,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        
        # SSL-konfigurasjon
        self.client.tls_set(
            certfile=CERT_FILE,
            keyfile=KEY_FILE,
            cert_reqs=ssl.CERT_NONE
        )
        self.client.tls_insecure_set(True)
        
        # Callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("✅ Koblet til Hisense TV")
            self.connected = True
            # Subscribe til alle topics
            client.subscribe("#")
            # Hent data
            self.request_data()
        else:
            print(f"❌ Tilkoblingsfeil: {rc}")
            
    def on_disconnect(self, client, userdata, rc, properties=None):
        print("🔌 Frakoblet fra TV")
        self.connected = False
        
    def on_message(self, client, userdata, msg):
        self.message_received = True
        try:
            payload = json.loads(msg.payload.decode())
        except:
            payload = msg.payload.decode()
            
        topic = msg.topic
        
        # Parse ulike meldingstyper
        if "volume" in topic.lower():
            if isinstance(payload, dict):
                if "volume_value" in payload:
                    self.data["volume"] = payload["volume_value"]
                    self.data["muted"] = payload.get("volume_mute", 0) == 1
                elif "volume" in payload:
                    self.data["volume"] = payload["volume"]
                self.data["power"] = "on"
                
        elif "sourcelist" in topic.lower():
            if isinstance(payload, list):
                self.data["sources"] = [s.get("displayname", s.get("sourcename", "?")) for s in payload]
                self.data["power"] = "on"
                
        elif "applist" in topic.lower():
            if isinstance(payload, list):
                self.data["apps"] = [app.get("name", "") for app in payload]
                self.data["power"] = "on"
                
        elif "state" in topic.lower() and isinstance(payload, dict):
            if "displayname" in payload or "sourcename" in payload:
                self.data["source"] = payload.get("displayname", payload.get("sourcename", "unknown"))
                self.data["power"] = "on"
                
    def request_data(self):
        """Ber om data fra TV-en - bruker riktige topics"""
        base = "/remoteapp/tv"
        client_id = "HABridge"
        
        # Kilder
        self.client.publish(f"{base}/ui_service/{client_id}/actions/sourcelist", "")
        time.sleep(0.3)
        
        # Volum
        self.client.publish(f"{base}/platform_service/{client_id}/actions/getvolume", "")
        time.sleep(0.3)
        
        # Apper
        self.client.publish(f"{base}/ui_service/{client_id}/actions/applist", "")
        time.sleep(0.3)
            
    def send_key(self, key):
        """Sender en tastetrykkkommando til TV-en"""
        topic = f"{BASE_TOPIC}/actions/sendkey"
        payload = {"keytype": "keypress", "keyvalue": key}
        self.client.publish(topic, json.dumps(payload))
        print(f"📺 Sendt tast: {key}")
        
    def update_ha_entities(self):
        """Oppdaterer Home Assistant-entiteter via REST API"""
        if not self.ha_token:
            print("⚠️ Ingen HA-token konfigurert")
            return
            
        headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json"
        }
        
        # Oppdater hovedsensor
        state_data = {
            "state": self.data["power"],
            "attributes": {
                "friendly_name": "Hisense TV Stue",
                "volume": self.data["volume"],
                "muted": self.data["muted"],
                "source": self.data["source"],
                "app_name": self.data["app_name"],
                "sources": self.data["sources"][:10] if self.data["sources"] else [],
                "apps": self.data["apps"][:20] if self.data["apps"] else [],
                "icon": "mdi:television"
            }
        }
        
        try:
            response = requests.post(
                f"{HA_URL}/api/states/sensor.hisense_tv_stue",
                headers=headers,
                json=state_data
            )
            if response.status_code in [200, 201]:
                print("✅ Home Assistant oppdatert")
            else:
                print(f"❌ HA-feil: {response.status_code}")
        except Exception as e:
            print(f"❌ Kunne ikke oppdatere HA: {e}")
            
    def poll_once(self, timeout=10):
        """Henter data én gang og oppdaterer HA"""
        self.setup_mqtt()
        
        try:
            self.client.connect(TV_IP, TV_PORT, 60)
            self.client.loop_start()
            
            # Vent på data
            start = time.time()
            while time.time() - start < timeout:
                if self.message_received:
                    time.sleep(2)  # Gi tid til flere meldinger
                    break
                time.sleep(0.5)
                
            # Oppdater HA
            self.update_ha_entities()
            
            # Returner data
            return self.data
            
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            
    def run_daemon(self, interval=30):
        """Kjører kontinuerlig og oppdaterer HA med jevne mellomrom"""
        print(f"🚀 Starter Hisense-HA Bridge (oppdaterer hvert {interval}. sekund)")
        
        while True:
            try:
                self.poll_once()
            except Exception as e:
                print(f"❌ Feil: {e}")
            time.sleep(interval)

def send_remote_command(key):
    """Sender en fjernkontrollkommando"""
    bridge = HisenseHABridge()
    bridge.setup_mqtt()
    
    try:
        bridge.client.connect(TV_IP, TV_PORT, 60)
        bridge.client.loop_start()
        time.sleep(1)  # Vent på tilkobling
        bridge.send_key(key)
        time.sleep(0.5)
    finally:
        bridge.client.loop_stop()
        bridge.client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hisense TV til Home Assistant Bridge")
    parser.add_argument("--daemon", action="store_true", help="Kjør som daemon")
    parser.add_argument("--interval", type=int, default=30, help="Oppdateringsintervall i sekunder")
    parser.add_argument("--key", type=str, help="Send fjernkontrolltast (f.eks. KEY_POWER)")
    parser.add_argument("--token", type=str, help="Home Assistant Long-Lived Access Token")
    
    args = parser.parse_args()
    
    # Sett token fra argument eller miljøvariabel
    ha_token = args.token or os.environ.get("HA_TOKEN", "")
    
    if args.key:
        send_remote_command(args.key)
    elif args.daemon:
        bridge = HisenseHABridge(ha_token)
        bridge.run_daemon(args.interval)
    else:
        # Én-gangs polling
        bridge = HisenseHABridge(ha_token)
        data = bridge.poll_once()
        print("\n📊 Hisense TV Data:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
