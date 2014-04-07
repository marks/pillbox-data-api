## Setting up your local environment 

#### Setting up on Ubuntu 

```
#! /bin/sh

set -e

apt-get update
sudo apt-get install git unzip python-setuptools python-dev build-essential libxml2-dev libxslt1-dev python-pip -y
easy_install -U setuptools
pip install lxml requests
```
