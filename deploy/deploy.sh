set -x
set -e
sudo su zulip -c 'git -C /home/zulip/deployments/current pull'
sudo su -c '/home/zulip/deployments/current/zulip-current-venv/bin/pip install --use-deprecated=legacy-resolver --no-deps --require-hashes -r /home/zulip/deployments/current/requirements/prod.txt'
sudo su zulip -c '/home/zulip/deployments/current/manage.py migrate'
sudo su zulip -c '/home/zulip/deployments/current/tools/update-prod-static' # in this command, do collect static again, do generate new static and copy all to static_root
sudo su zulip -c '/home/zulip/deployments/current/scripts/restart-server'
