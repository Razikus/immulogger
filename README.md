# Starting

``` docker-compose up -d --scale immulogger=4 ```


# Accessing interactive docs

``` http://localhost/docs ```

# Default credentials

``` Login: admin password: admin ```


# Testing
You need docker to perform tests

``` cd api && pip install -r reqirements-test.txt && pytest ```

# Test tool
## Building test tool

``` cd test_tool && go build ```

## Starting test tool

```HOST=localhost FIXEDWAIT=10 PORT=80 WORKERS=32 ./boomboom```

- PORT - port of service
- HOST - host of service
- WORKERS - how much workers to spawn
- FIXEDWAIT - sleep between requests

Docker service 

``` docker run -e HOST=xxx -e PORT=xxx -e WORKERS=32 -e FIXEDWAIT=10 ghcr.io/razikus/immulogger/testtool:master ```

