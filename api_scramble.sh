#!/bin/bash

# Variabili
API_BASE="http://192.168.1.159:3000"
USERNAME="apollo@example.com"
PASSWORD="1234"

# Login e estrazione token
TOKEN=$(http --form POST $API_BASE/auth/token username=$USERNAME password=$PASSWORD | jq -r '.access_token')

# Chiamata API con token
http GET $API_BASE/rifiuti/ "Authorization: Bearer $TOKEN"
