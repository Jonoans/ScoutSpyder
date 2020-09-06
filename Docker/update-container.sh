#!/bin/bash
docker cp ../ crawler-api:/opt/scoutspyder/
docker exec crawler-api rm -rf /opt/scoutspyder/{.git,.gitignore,Docker,requirements.txt}
docker restart crawler-api