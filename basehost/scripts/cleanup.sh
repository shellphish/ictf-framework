#!/bin/bash -eux

# Uninstall Ansible and remove PPA.
DEBIAN_FRONTEND=noninteractive apt -y remove --purge ansible
apt-add-repository --remove ppa:ansible/ansible

# Apt cleanup.
DEBIAN_FRONTEND=noninteractive apt autoremove -y
DEBIAN_FRONTEND=noninteractive apt update -y

# Delete unneeded files.
rm -f /home/vagrant/*.sh

# Zero out the rest of the free space using dd, then delete the written file.
dd if=/dev/zero of=/EMPTY bs=1M
rm -f /EMPTY

# Add `sync` so Packer doesn't quit too early, before the large file is deleted.
sync
