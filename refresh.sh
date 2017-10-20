#!/bin/bash

echo 'sudo docker-compose down'
sudo docker-compose down

echo 'sudo rm -rf docker-persistence/app-data'
sudo rm -rf docker-persistence/app-data
echo 'sudo rm -rf docker-persistence/postgres'
sudo rm -rf docker-persistence/postgres
echo 'sudo rm -rf app/git-data/firehol'
sudo rm -rf app/git-data/firehol
echo 'sudo rm -rf app/__pycache__'
sudo rm -rf app/__pycache__
echo 'sudo truncate -s 0 app/log/run.log'
sudo truncate -s 0 app/log/run.log


echo 'sudo docker-compose up -d'
sudo docker-compose up -d