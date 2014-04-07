## Setting up your local environment 

#### Setting up on Ubuntu 

```
#! /bin/sh

set -e

apt-get update
apt-get install git unzip -y
sudo apt-get install python-setuptools python-dev build-essential -y
apt-get install libxml2-dev libxslt1-dev -y 
easy_install -U setuptools
apt-get install python-pip
pip install lxml
pip install requests
```
