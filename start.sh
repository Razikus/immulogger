#!/bin/bash

docker-compose build && docker-compose up -d --scale immulogger=4
