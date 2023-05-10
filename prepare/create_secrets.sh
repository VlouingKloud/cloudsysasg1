#!/bin/bash
#
echo "strongkey" | docker secret create jwtkey

echo "DBADDR=http://db-service/\nDBUSER=postgres\nDBPASSWORD=password" | docker secret create dbconfig
