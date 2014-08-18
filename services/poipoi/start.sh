#!/bin/bash
set -e
cd /var/ictf/services/poipoi
/sbin/start-stop-daemon -b --chdir /var/ictf/services/poipoi --start --exec /ictf/services/poipoi/poipoi -- 3335
