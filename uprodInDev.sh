#!/usr/bin/env bash

SSHFS_EXEC="$(ps -e -o comm)"

if [[ ! $SSHFS_EXEC =~ "sshfs" ]]; then
   echo "Chamando SSHFS"
   sshfs -o allow_other cmj@168.228.184.70:/storage/djangoapps/cmj_backup/volumes/portalcmj_cmj_media/_data /mnt/volumes/cmj_media
fi
echo "Executando Compose DEV"
sudo UID="$(id -u)" GID="$(id -g)" docker compose -f docker/docker-compose-dev-mode-prod.yaml up --build -d
