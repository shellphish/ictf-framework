#!/bin/bash
set -e
cd /var/ictf/services/sillybox
/sbin/start-stop-daemon -b --start --chdir /var/ictf/services/sillybox --exec /ictf/services/sillybox/sillybox_spawner --
