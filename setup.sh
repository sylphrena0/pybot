#!/bin/bash
######################################################
####### Bash Script to Setup Picar in Blank OS #######
######################################################
# Install picar dependancies
#
# Author: Sylphrena Kleinsasser
######################################################

#install dependancies:
sudo apt update
sudo apt install git pip python3-flask python3-opencv libgl1
sudo raspi-config nonint do_i2c 0 #enable I2C
pip3 install pandas numpy picamera adafruit-circuitpython-motorkit

#clone repo into current directory:
git config --global user.name "<git_username>"
git config --global user.email "<git_email>"
git config --global user.password "<git_password>"
git config --global credential.helper store
git clone https://github.com/sylphrena0/picar .

#add aliases and variables:
echo 'export FLASK_APP=picar' >> ~/.bashrc 
echo 'export FLASK_ENV=development' >> ~/.bashrc 
echo 'alias car="cd /home/pi/picar; flask run -h 0.0.0.0"' >> ~/.bashrc 
source ~/.bashrc 