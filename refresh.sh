#!/bin/bash

echo 'sudo docker-compose down'
sudo docker-compose down

echo 'sudo rm -rf docker_persistence/app-data'
sudo rm -rf docker_persistence/app-data
echo 'sudo rm -rf docker_persistence/postgres'
sudo rm -rf docker_persistence/postgres
echo 'sudo rm -rf app/git_data'
sudo rm -rf app/git_data
#echo 'sudo truncate -s 0 app/log/run.log'
#sudo truncate -s 0 app/log/run.log


echo 'sudo docker-compose up -d'
sudo docker-compose up -d