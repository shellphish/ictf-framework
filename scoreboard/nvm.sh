#! /bin/bash
. /home/deploy/.nvm/nvm.sh
. /home/deploy/.profile
. /home/deploy/.bashrc
export NVM_DIR="/home/deploy/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"  # This loads nvm

nvm install stable
nvm run stable --version 
nvm alias default stable creates=/home/deploy/.nvm/versions/node/v6.6.0



