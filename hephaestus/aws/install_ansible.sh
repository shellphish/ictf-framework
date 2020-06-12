#!/bin/bash -eux

# Install Ansible repository.
# The line above will cause the process to get stuck during the updating of grub
# See: https://github.com/chef/bento/issues/661#issuecomment-248136601
DEBIAN_FRONTEND=noninteractive sudo apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
sudo apt-get -y install software-properties-common
sudo apt-add-repository ppa:ansible/ansible

# Install Ansible.
sudo apt-get -y update
sudo apt-get -y install ansible
