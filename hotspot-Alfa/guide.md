# Start wlan0 
sudo airmon-ng start wlan0
# test scan
sudo airodump-ng wlan0

# Configure IP address for WLAN
sudo ifconfig wlan0 192.168.1.1
# Start DHCP/DNS server
sudo service dnsmasq restart
# Enable routing
sudo sysctl -w net.ipv4.ip_forward=1
# Enable NAT
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
# Run access point daemon
sudo hostapd /etc/hostapd.conf


# Stop
# Disable NAT
sudo iptables -D POSTROUTING -t nat -o eth0 -j MASQUERADE
# Disable routing
sudo sysctl -w net.ipv4.ip_forward=0
# Disable DHCP/DNS server
sudo service dnsmasq stop
sudo service hostapd stop
