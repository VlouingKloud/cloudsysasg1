FROM fedora

RUN dnf up -y

RUN dnf install -y python3 python3-pip nginx

RUN pip3 install Flask urllib3 bcrypt

RUN mkdir /web

COPY url23.conf /etc/nginx/conf.d/url23.conf
COPY run.sh /web/
ADD auth /web/auth
ADD urlshortner /web/urlshortner
CMD cd /web && sh run.sh
