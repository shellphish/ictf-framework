#!/bin/bash -eux

# This sleep comes from the packer.io documentation
# (https://www.packer.io/intro/getting-started/provision/)
# sleep 30
whoami
# Install Ansible repository.
# The line above will cause the process to get stuck during the updating of grub
# See: https://github.com/chef/bento/issues/661#issuecomment-248136601
DEBIAN_FRONTEND=noninteractive sudo apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
sudo apt -y install software-properties-common
sudo apt-add-repository ppa:ansible/ansible

# Install Ansible.
sudo apt -y update
sudo apt -y install ansible
