#!/usr/bin/env bash

SSHFS_EXEC="$(ps -e -o comm)"

if [[ ! $SSHFS_EXEC =~ "sshfs" ]]; then
   echo "Chamando SSHFS"
fi
echo "Executando Compose DEV"
sudo docker compose -f docker/docker-compose-dev.yaml up --build -d
