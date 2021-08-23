# Dockerfile for ont-did-driver

FROM universalresolver/base-ubuntu


RUN apt-get -y update && \
    apt-get -y install -y python3 python3-pip && \
    python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install ontology-python-sdk aiohttp  setuptools-rust


ADD . /opt/driver-did-ont

RUN cd /opt/driver-did-ont

EXPOSE 8080

RUN chmod a+rx /opt/driver-did-ont/driver.py
CMD "/opt/driver-did-ont/driver.py"
