#!/usr/bin/env bash

echo "Desligando Compose ProdInDev"
sudo UID="$(id -u)" GID="$(id -g)" docker compose -f docker/docker-compose-dev-mode-prod.yaml down
