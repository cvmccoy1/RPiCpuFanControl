cd ~/git
gh repo clone cvmccoy1/RPiCpuFanControl
cd RPiCpuFanControl

1) Install Python dependencies
    pip3 install matplotlib simple-pid gpiozero

2) Install and enable the pigpiod GPIO daemon (required for kernel 6.x)
    sudo apt-get install -y pigpiod
    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod

3) Copy application files to install location
    sudo mkdir -p /usr/local/projects/RPiCpuFanControl
    sudo chmod 777 /usr/local/projects/
    sudo cp ./*.py /usr/local/projects/RPiCpuFanControl/.
    sudo cp ./config.ini /usr/local/projects/RPiCpuFanControl/.

4) Install desktop shortcut and icon
    sudo cp ./images/fan*.png /usr/share/pixmaps/.
    sudo cp ./scripts/fan.desktop /home/pi/Desktop/.
    Set the option in File manager-->Edit-->Preferences-->General-->Do not ask option on executable launch

5) (Optional) Enable autostart via systemd
    sudo cp ./scripts/fancontrol.service /etc/systemd/system/.
    sudo chmod 755 /etc/systemd/system/fancontrol.service
    sudo systemctl daemon-reload
    sudo systemctl enable fancontrol.service
    sudo systemctl start fancontrol.service

   Or via desktop autostart:
    mkdir -p ~/.config/autostart
    cp ~/Desktop/fan.desktop ~/.config/autostart/.
