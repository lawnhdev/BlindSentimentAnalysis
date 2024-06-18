#!/bin/bash

sudo dnf install python3-pip -y
python3 -m pip install selenium requests bs4 pandas boto3 --use-deprecated=legacy-resolver # have to do this flag b/c of the modulenotfound dateutil error with awscli
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo dnf localinstall google-chrome-stable_current_x86_64.rpm -y
sudo ln -s /opt/google/chrome/google-chrome /usr/local/bin/google-chrome
wget https://storage.googleapis.com/chrome-for-testing-public/126.0.6478.61/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
cd chromedriver-linux64
sudo mv chromedriver /usr/local/bin/
cd ..