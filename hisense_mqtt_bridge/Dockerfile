ARG BUILD_FROM
FROM $BUILD_FROM

# Install dependencies
RUN apk add --no-cache jq

WORKDIR /app

# Copy files
COPY hisense_bridge.py requirements.txt run.sh ./

# Install Python packages
RUN pip3 install --no-cache-dir paho-mqtt pyyaml

# Make run script executable
RUN chmod a+x run.sh

CMD ["/app/run.sh"]
