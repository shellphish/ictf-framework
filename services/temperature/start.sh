#/bin/bash
set -e
cd /var/ictf/services/temperature
/sbin/start-stop-daemon -b --chdir /var/ictf/services/temperature --start --exec /ictf/services/temperature/temperature
