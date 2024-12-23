# Secure IoT Project

# Hotspot
- Move hostapd.conf to /et/hostapd.conf
- Read guide.md

# MQTT
## installation
- Install mosquitto on PC
## Setup
- Run mosquitto MQTT Broker
- sudo nano /etc/mosquitto/mosquitto.conf 
- -  allow_anonymous true
     bind_address 0.0.0.0

# Docker
- ```docker-compose down```
- ```docker-compose build --no-cache```
- ```docker-compose up```

IF now changes and just run:
     ```docker-compose up --build```
     

## Test
- ```bash mosquitto_sub -t "home/test" ```
- ```bash mosquitto_pub -m "ON" -t "home/test" ```

# LateX
## Installation
- Install Latex-Workshop on VS Code
- Add "-shell-escape", to setting of Latex-Workshop (pdflatex and latexmk if faced build error)
- Build