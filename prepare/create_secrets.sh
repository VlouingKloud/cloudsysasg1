#!/bin/bash
#
echo "strongkey" | docker secret create jwtkey -

echo "DBADDR=http://db-service/ DBUSER=postgres DBPASSWORD=password" | docker secret create dbconfig -
