sudo ufw reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow from 128.111.48.6


sudo ufw allow from 199.27.128.0/21 to any port 80
sudo ufw allow from 173.245.48.0/20 to any port 80
sudo ufw allow from 103.21.244.0/22 to any port 80
sudo ufw allow from 103.22.200.0/22 to any port 80
sudo ufw allow from 141.101.64.0/18 to any port 80
sudo ufw allow from 108.162.192.0/18 to any port 80
sudo ufw allow from 190.93.240.0/20 to any port 80
sudo ufw allow from 188.114.96.0/20 to any port 80
sudo ufw allow from 197.234.240.0/22 to any port 80
sudo ufw allow from 198.41.128.0/17 to any port 80
sudo ufw allow from 162.158.0.0/15 to any port 80
sudo ufw allow from 104.16.0.0/12 to any port 80
sudo ufw allow from 172.64.0.0/13 to any port 80
sudo ufw allow from 199.27.128.0/21 to any port 443
sudo ufw allow from 173.245.48.0/20 to any port 443
sudo ufw allow from 103.21.244.0/22 to any port 443
sudo ufw allow from 103.22.200.0/22 to any port 443
sudo ufw allow from 141.101.64.0/18 to any port 443
sudo ufw allow from 108.162.192.0/18 to any port 443
sudo ufw allow from 190.93.240.0/20 to any port 443
sudo ufw allow from 188.114.96.0/20 to any port 443
sudo ufw allow from 197.234.240.0/22 to any port 443
sudo ufw allow from 198.41.128.0/17 to any port 443
sudo ufw allow from 162.158.0.0/15 to any port 443
sudo ufw allow from 104.16.0.0/12 to any port 443
sudo ufw allow from 172.64.0.0/13 to any port 443



sudo ufw allow from 128.111.48.6 to any port 80
sudo ufw allow from 128.111.48.6 to any port 443
sudo ufw allow from 192.168.48.0/24 to any port 80
sudo ufw allow from 192.168.48.0/24 to any port 443

sudo ufw enable
