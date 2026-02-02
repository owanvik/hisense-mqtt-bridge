#!/usr/bin/env bash
set -e

CONFIG_PATH=/data/options.json

# Check if running as HA Add-on (with bashio) or standalone
if command -v bashio &> /dev/null && [ -f "$CONFIG_PATH" ]; then
    # Running as Home Assistant Add-on
    echo "Running as Home Assistant Add-on"
    
    TV_IP=$(bashio::config 'tv_ip')
    TV_PORT=$(bashio::config 'tv_port')
    TV_CLIENT_ID=$(bashio::config 'tv_client_id')
    MQTT_HOST=$(bashio::config 'mqtt_host')
    MQTT_PORT=$(bashio::config 'mqtt_port')
    MQTT_USER=$(bashio::config 'mqtt_username')
    MQTT_PASS=$(bashio::config 'mqtt_password')
    DEVICE_ID=$(bashio::config 'device_id')
    DEVICE_NAME=$(bashio::config 'device_name')
    VOLUME_MAX=$(bashio::config 'volume_max')

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
  topic_prefix: "hisense/${DEVICE_ID/hisense_/}"
volume:
  max: ${VOLUME_MAX}
  step: 1
EOF

    bashio::log.info "Starting Hisense TV MQTT Bridge..."
    bashio::log.info "TV: ${TV_IP}:${TV_PORT}"
    bashio::log.info "MQTT: ${MQTT_HOST}:${MQTT_PORT}"
else
    # Running standalone - use existing config.yaml
    echo "Running standalone mode"
    if [ ! -f /app/config.yaml ]; then
        echo "ERROR: config.yaml not found. Run with --setup first."
        exit 1
    fi
fi

exec python3 -u /app/hisense_bridge.py
