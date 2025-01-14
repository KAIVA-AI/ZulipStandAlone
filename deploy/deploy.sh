#!/bin/bash
source /srv/zulip-py3-venv/bin/activate
EXTERNAL_HOST=3.107.244.178:9991 EXTERNAL_URI_SCHEME=https:// ./tools/run-dev --interface=''
