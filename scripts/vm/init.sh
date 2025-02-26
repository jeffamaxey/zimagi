#!/usr/bin/env bash
#
#=========================================================================================
# Initialize Virtual Machine
#

export DEBIAN_FRONTEND=noninteractive

if ! [ -f /etc/apt/sources.list.d/docker.list ]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
    https://download.docker.com/linux/ubuntu/ $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
fi
apt-get update -y
apt-get upgrade -y
apt-get install -y --no-install-recommends docker-ce net-tools

usermod -aG docker vagrant

export ZIMAGI_HOST_APP_DIR="/project/app"
export ZIMAGI_HOST_DATA_DIR="/project/data"
export ZIMAGI_HOST_LIB_DIR="/project/lib"
export ZIMAGI_HOST_PACKAGE_DIR="/project/package"

su - vagrant -c "/project/scripts/reactor init"
su -P - vagrant -c "/project/scripts/zimagi env get"
