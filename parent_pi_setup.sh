#!/bin/bash

# Set up a Raspberry Pi as an ODM360 Parent.
model="$( cat /proc/device-tree/model )" 2>> provisioning/error.log
onpi="no"
if [[ "$model" == *"Raspberry Pi"* ]]; then
    echo "This is actually a Raspberry Pi!"
    onpi="yes"
else
    echo "This is not a raspberry pi, exiting."
    exit 1
fi

# If nothing in /proc/device-tree/model:
if [[ "$model" == "" ]]; then
    echo "I have no idea what this machine is!"
    model="computer of some sort"
fi


echo Running base pi setup
provisioning/base_pi_setup.sh

echo Running database setup script
provisioning/database_setup.sh

echo Running gpsd setup script
provisioning/gpsd_setup.sh >> provisioning/setup.log 2>> provisioning/error.log

echo Running NTP setup script
provisioning/ntp_setup.sh >> provisioning/setup.log 2>> provisioning/error.log

echo Setting NTP to server config
echo '
restrict 192.168.1.0 mask 255.255.255.0

broadcast 192.168.1.255
broadcast 224.0.1.1
' | sudo tee -a /etc/ntp.conf

# Install dnsmasq and hostapd
provisioning/wifi_setup.sh >> provisioning/setup.log 2>> provisioning/error.log

echo installing nginx and configuring it to use uwsgi
sudo apt install -y nginx >> provisioning/setup.log 2>> provisioning/error.log

sudo rm /etc/nginx/sites-enabled/default
echo adding the odm360dashboard site config file to nginx
sudo cp provisioning/odm360dashboard /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/odm360dashboard /etc/nginx/sites-enabled/

echo Copying dashboard unit file into systemd folder
sudo cp provisioning/systemd_services/odm360_dashboard.service /etc/systemd/system/
echo Starting and enabling the odm360dashboard service with Systemd
sudo systemctl start odm360dashboard.service
sudo systemctl enable odm360dashboard.service

echo Naming the parent
echo parent.local | sudo tee /etc/hostname

echo Establishing as systemd service to run on startup.
sudo cp provisioning/odm_rent.service /etc/systemd/system/.
sudo systemctl start odm_rent.service 
sudo systemctl enable odm_rent.service 

echo "************************************"
echo Now you should have a $model set up as a Parent for an ODM360 rig.
echo "************************************"
echo
