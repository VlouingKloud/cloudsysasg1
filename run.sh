#!/bin/bash
#

nginx

cd /web/auth && python3 main.py &
cd /web/urlshortner && python3 main.py
