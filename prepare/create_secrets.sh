#!/bin/bash
#
kubectl create secret generic my-secret --from-literal=strongkey

kubectl create secret generic my-secret --from-literal=DBADDR=http://db-service/\x20DBUSER=postgres\x20DBPASSWORD=password
