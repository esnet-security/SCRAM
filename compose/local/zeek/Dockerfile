FROM zeek/zeek:lts

# do all the python and redis installs
RUN apt-get update && apt-get install -y python3 python3-pip python3-setuptools python3-venv redis-server && rm -rf /var/lib/apt/lists/*

# configure everything like the zeek training
RUN git clone https://github.com/zeek/zeek-training && \
    cd zeek-training/Intro-to-Zeek/training-res/ && \
    sh ./setup.sh

# zeek_scram requires a zeek user (well, home dir) and venv for scram-client, do all that in this heinous oneliner.
# oh yeah, also monkey patch the scram-client to use http instead of https because i'm an insane person (and don't have certs locally)
RUN useradd -m -s /bin/bash zeek || true && \
    mkdir -p /home/zeek && \
    python3 -m venv /home/zeek/scram_client_venv && \
    git clone -b topic/chris/debugger https://github.com/esnet-security/scram-client.git /opt/scram-client && \
    cd /opt/scram-client && \
    /home/zeek/scram_client_venv/bin/pip install . && \
    sed -i 's/https:\/\//http:\/\//g' /opt/scram-client/src/scram_client/cli.py && \
    sed -i 's/https:\/\//http:\/\//g' /home/zeek/scram_client_venv/lib/python*/site-packages/scram_client/cli.py && \
    echo '#!/bin/bash\n/home/zeek/scram_client_venv/bin/python -m scram_client "$@"' > /home/zeek/scram_client_venv/bin/scram-client && \
    chmod +x /home/zeek/scram_client_venv/bin/scram-client && \
    chown -R zeek:zeek /home/zeek

# setup the script that inits the scram-client.
COPY ./compose/local/zeek/scram-startup.sh /usr/local/bin/scram-startup.sh
RUN chmod +x /usr/local/bin/scram-startup.sh

# Install Zeek packages we need.
RUN zkg autoconfig --force && \
    zkg install --force --skiptests bro-simple-scan && \
    zkg install --force --skiptests zeek_scram

WORKDIR /usr/local/zeek

# start Redis, run auto-registration, deploy zeek, and start scram-client in run_queue mode FOREVER.
CMD ["sh", "-c", "redis-server --daemonize yes && /usr/local/bin/scram-startup.sh && zeekctl deploy && while true; do /home/zeek/scram_client_venv/bin/scram-client run_queue; done"]
