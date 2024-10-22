#!/usr/bin/env bash
sudo docker compose -f docker/docker-compose-dev.yaml down
sudo chown -R leandro:leandro .
rm _frontend/v1/dev-webpack-stats.json