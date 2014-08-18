#!/bin/bash
set -e
cd /var/ictf/services/tattletale
/sbin/start-stop-daemon -b --start --chdir /var/ictf/services/tattletale --exec /ictf/services/tattletale/tattletale32 --
