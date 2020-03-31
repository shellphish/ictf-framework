# Notes on major changes in ansible

## Game master

- The version of docker changed from 17.12.0 to 17.12.1... Should we consider to update docker to the latest version (18)?
- There are hardcoded ips for iptables rules... we need to chenge them
- /var/log/upstart is not a thing anymore, I changed the directory to /var/log
- Symbolic links from /var/log to /opt/ictf/gm fails unless executed with force: true. I need to understand which are the implications of that.