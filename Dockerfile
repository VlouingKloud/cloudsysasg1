FROM fedora

RUN dnf up -y

RUN dnf install -y python3 python3-pip nginx

RUN pip3 install duckdb Flask urllib3 bcrypt

RUN mkdir /web

COPY url23.conf /web
ADD auth /web/auth
ADD urlshortner /web/urlshortner
#CMD cd /web && python3 main.py
