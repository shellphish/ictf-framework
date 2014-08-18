#/bin/bash
set -e
cd /var/ictf/services/driller
/sbin/start-stop-daemon -b --chdir /var/ictf/services/driller --start --exec /ictf/services/driller/driller --
