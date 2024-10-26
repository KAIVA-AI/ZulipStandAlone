set -e
set -x
sudo -u zulip git -C /home/zulip/deployments/current pull

/home/zulip/deployments/current/zulip-current-venv/bin/pip install --use-deprecated=legacy-resolver --no-deps --require-hashes -r /home/zulip/deployments/current/requirements/prod.txt
