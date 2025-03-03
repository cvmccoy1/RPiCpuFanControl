1) Move the python code common folder
    sudo mkdir -p /usr/local/projects/RPiCpuFanControl
    sudo chmod 777 /usr/local/projects/
    sudo ln -s ./*.py /usr/local/projects/RPiCpuFanControl/.
    sudo ln -s ./config.ini /usr/local/projects/RPiCpuFanControl/.

2) Create a shortcut to the Fan Controller
     sudo cp ./images/fan*.png /usr/share/pixmaps/.
     sudo cp ./scripts/fan.desktop /home/pi/Desktop/.
     Set the option in File manager-->Edit-->Preferences-->General-->Do not ask option on executable launch
4) sudo chmod 755 ./scrips/fancontrol
5) sudo ln -s ./scripts/fancontrol /etc/init.d/. 

///// The first two options for autostart didn't work
Do:
6) sudo update-rc.d fancontrol defaults
Or:
7) sudo cp '/usr/local/nas_public/Installs/Raspberry Pi/fancontrol.service' /etc/systemd/system/.
8) sudo chmod 755 /etc/systemd/system/fancontrol.service
9) sudo systemctl daemon-reload
10) sudo systemctl enable fancontrol.service
11) sudo systemctl start fancontrol.service
/////
Or:
4) sudo mkdir -p /home/pi/.config/autostart
5) sudo cp /home/pi/Desktop/fan.desktop /home/pi/.config/autostart/.