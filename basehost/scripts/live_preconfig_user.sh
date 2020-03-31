#!/usr/bin/env bash

useradd -m -c 'ICTF infrastructure user' -G sudo "$ICTF_USER" -s /bin/bash
echo "$ICTF_USER:$ICTF_USER_PASSWORD" | chpasswd
passwd -l $OLD_USER

if [ "$TARGET" == "AMI" ]; then
    TMP_PYTHON_SCRIPT=$(mktemp tmp.XXXXXXXXXX.py)
    TMP_RESULT_FILE=$(mktemp tmp.XXXXXXXXXX)

    echo """
import re
import sys
s = sys.stdin.read();
replaced = re.sub('(.*default_user:\s+name:\s+)([a-zA-Z_]+)(.*)', '\\\\1$ICTF_USER\\\3', s)
print(replaced)
""" > $TMP_PYTHON_SCRIPT

    cat /etc/cloud/cloud.cfg | python3 "$TMP_PYTHON_SCRIPT" > "$TMP_RESULT_FILE"
    mv "$TMP_RESULT_FILE" /etc/cloud/cloud.cfg

    if [ -f /etc/sudoers.d/90-cloudimg-ubuntu ]; then
        mv /etc/sudoers.d/90-cloudimg-ubuntu /etc/sudoers.d/90-cloud-init-users
    fi
    perl -pi -e "s/ubuntu/$ICTF_USER/g;" /etc/sudoers.d/90-cloud-init-users
fi

