FROM ubuntu

RUN apt-get update
RUN apt-get install python3 python3-pip -y

COPY ./requirements.txt /
COPY ./app.py /opt/vcount/

WORKDIR /

RUN pip3 install -r requirements.txt
RUN chmod +x /opt/vcount/app.py
ENTRYPOINT /opt/vcount/app.py
