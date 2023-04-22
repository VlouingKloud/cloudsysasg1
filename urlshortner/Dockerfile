FROM fedora

RUN dnf up -y

RUN dnf install -y python3 python3-pip

RUN pip3 install duckdb Flask

RUN mkdir /web

COPY conf.py main.py /web

CMD cd /web && python3 main.py
