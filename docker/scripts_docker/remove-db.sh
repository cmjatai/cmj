#!/usr/bin/env bash
sudo docker stop cmj_localhost_1
sudo docker rm cmj_localhost_1
sudo docker rmi -f postgres
