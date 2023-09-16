#!/bin/bash
yum update -y
yum install -y python-pip
pip3 install django gunicorn