ARG BUILD_FROM
FROM $BUILD_FROM

# Install dependencies
RUN apk add --no-cache python3 py3-pip jq

WORKDIR /app

# Copy files
COPY hisense_bridge.py requirements.txt ./

# Install Python packages
RUN pip3 install --no-cache-dir --break-system-packages paho-mqtt pyyaml

# Copy s6-overlay service
COPY rootfs /
