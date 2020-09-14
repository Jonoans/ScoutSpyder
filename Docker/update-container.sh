#!/bin/bash
docker cp ../ crawler:/opt/scoutspyder/
docker exec crawler rm -rf /opt/scoutspyder/{.git,.gitignore,Docker,requirements.txt}
docker restart crawler