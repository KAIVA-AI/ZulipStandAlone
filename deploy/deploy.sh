set -e
set -x
cd /home/zulip/deployments/current
git pull

. zulip-current-venv/bin/activate
./manage.py migrate
tools/update-prod-static
scripts/restart-server
