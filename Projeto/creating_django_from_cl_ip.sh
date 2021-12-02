#!/bin/bash
sudo su - ubuntu
HOME="/home/ubuntu/"



cd $HOME
sudo apt update
git clone https://github.com/raulikeda/tasks.git
cd tasks
sudo sed -i 's/node1/3.145.64.208/g' ./portfolio/settings.py
./install.sh
sudo ufw allow 8080/tcp
sudo reboot


