#!/bin/bash
######################################################
####### Bash Script to Setup PyBot in Blank OS #######
######################################################
# Install pybot dependancies
#
# Author: Sylphrena Kleinsasser
######################################################

#install dependancies:
sudo apt update
sudo apt install git pip python3-flask libgl1
sudo raspi-config nonint do_i2c 0 #enable I2C
pip3 install pandas numpy picamera2 adafruit-circuitpython-motorkit schedule adafruit-circuitpython-vcnl4040 adafruit-circuitpython-vl53l1x

#clone repo into current directory:
git config --global user.name "<git_username>"
git config --global user.email "<git_email>"
git config --global user.password "<git_password>"
git config --global credential.helper store
git clone https://github.com/sylphrena0/pybot .

#add aliases and variables:
echo 'export FLASK_APP=pybot' >> ~/.bashrc 
echo 'export FLASK_ENV=development' >> ~/.bashrc 
echo 'alias car="cd /home/pi/pybot; flask run -h 0.0.0.0"' >> ~/.bashrc 
source ~/.bashrc 

cd /home/pi/pybot
flask init-db