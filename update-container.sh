#!/bin/bash
docker cp ./ crawler-api:/opt/scoutspyder/
docker exec crawler-api rm -rf /opt/scoutspyder/{.git,.gitignore,Dockerfile,requirements.txt,update-container.sh,docker-compose.yml}
docker restart crawler-api