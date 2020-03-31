#!/bin/bash -eux

sleep 10
# Install Ansible repository.
#apt -y update && apt-get -y upgrade
# The line above will cause the process to get stuck during the updating of grub
# See: https://github.com/chef/bento/issues/661#issuecomment-248136601
DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
apt -y install software-properties-common
apt-add-repository ppa:ansible/ansible

# Install Ansible.
apt -y update
apt -y install ansible
