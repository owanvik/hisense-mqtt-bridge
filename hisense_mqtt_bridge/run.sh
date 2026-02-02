#!/bin/sh
set -e

CONFIG_PATH=/data/options.json

# Read config from HA Add-on options using jq
TV_IP=$(jq -r '.tv_ip' $CONFIG_PATH)
TV_PORT=$(jq -r '.tv_port' $CONFIG_PATH)
TV_CLIENT_ID=$(jq -r '.tv_client_id' $CONFIG_PATH)
MQTT_HOST=$(jq -r '.mqtt_host' $CONFIG_PATH)
MQTT_PORT=$(jq -r '.mqtt_port' $CONFIG_PATH)
MQTT_USER=$(jq -r '.mqtt_username' $CONFIG_PATH)
MQTT_PASS=$(jq -r '.mqtt_password' $CONFIG_PATH)
DEVICE_ID=$(jq -r '.device_id' $CONFIG_PATH)
DEVICE_NAME=$(jq -r '.device_name' $CONFIG_PATH)
VOLUME_MAX=$(jq -r '.volume_max' $CONFIG_PATH)

# Create topic_prefix without "hisense_" prefix
TOPIC_ID=$(echo "$DEVICE_ID" | sed 's/hisense_//')

# Create config.yaml for the bridge
cat > /app/config.yaml << EOF
tv:
  ip: "${TV_IP}"
  port: ${TV_PORT}
  client_id: "${TV_CLIENT_ID}"
mqtt:
  host: "${MQTT_HOST}"
  port: ${MQTT_PORT}
  username: "${MQTT_USER}"
  password: "${MQTT_PASS}"
device:
  id: "${DEVICE_ID}"
  name: "${DEVICE_NAME}"
  topic_prefix: "hisense/${TOPIC_ID}"
volume:
  max: ${VOLUME_MAX}
  step: 1
EOF

echo "Starting Hisense TV MQTT Bridge..."
echo "TV: ${TV_IP}:${TV_PORT}"
echo "MQTT: ${MQTT_HOST}:${MQTT_PORT}"

exec python3 -u /app/hisense_bridge.py
