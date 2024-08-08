#!/bin/bash
source zulip-py3-venv/bin/activate
sudo ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill -9
celery -A zproject worker -l info
