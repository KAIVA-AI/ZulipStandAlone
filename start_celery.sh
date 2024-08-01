#!/bin/bash
source zulip-py3-venv/bin/activate
celery -A zproject worker -l info
