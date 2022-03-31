#!/bin/bash

# In order to test you have to have docker
docker build -t testcontainer . -f Dockerfile.testcontainer
touch report.html
docker run --rm --network=host --name tests -v /var/run/docker.sock:/var/run/docker.sock -v "$PWD"/report.html:/report.html testcontainer
