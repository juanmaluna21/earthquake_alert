FROM ubuntu:latest

COPY /config /config
COPY app.py /app.py
COPY cronworker.sh /cronworker.sh
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install requests pandas pymongo
RUN chmod +x /cronworker.sh

CMD ["/bin/bash", "/cronworker.sh"]
