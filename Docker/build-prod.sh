#!/bin/bash
docker network inspect scoutspyder >/dev/null 2>&1 || \
    docker network create \
    --driver bridge \
    --subnet 172.16.0.0/16 \
    --gateway 172.16.0.1 \
    scoutspyder
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d