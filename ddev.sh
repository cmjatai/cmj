#!/usr/bin/env bash
sudo docker compose -f docker/docker-compose-dev.yaml down
sudo chown -R leandro:leandro .