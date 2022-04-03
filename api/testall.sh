#!/bin/bash

sudo mkdir -p /certs/
sudo cp tests/*.pem /certs
sudo chmod 777 /certs/*

# In order to test you have to have docker
pytest -v --html=report.html --self-contained-html