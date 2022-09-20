#!/bin/bash

sudo -y apt install git
sudo apt-get -y install ffmpeg libsm6 libxext6  -y
sudo apt-get -y install poppler-utils
sudo apt-get -y install libleptonica-dev tesseract-ocr libtesseract-dev python3-pil tesseract-ocr-eng tesseract-ocr-script-latn
sudo apt-get -y install tesseract-ocr-all
sudo apt -y install python3-pip
pip3 install --upgrade setuptools
pip3 install -r requirements.txt