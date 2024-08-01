# Chat Server

# Run server
## Local
```sh
tools/run-dev
```
## MacOS
```sh
brew tap hashicorp/tap
brew install hashicorp/tap/hashicorp-vagrant
vagrant up --provider=docker --provision

vagrant ssh
./tools/run-dev
```
## Dev
```sh
# ./tools/provision
# source /srv/zulip-py3-venv/bin/activate

sudo su
ufw allow 9991
ufw allow 5432

apt install -y nginx
systemctl enable nginx
systemctl start nginx
vi /etc/nginx/sites-available/zulip
# tools/droplets/zulipdev
ln -nsf /etc/nginx/sites-available/zulip /etc/nginx/sites-enabled/
nginx -t
service nginx reload

EXTERNAL_HOST=chat-dev.kollabridge.com EXTERNAL_URI_SCHEME=https:// tools/run-dev --interface=''
```
## Stg
```sh
EXTERNAL_HOST=collab.vietis.com.vn:9991 ZULIP_BASE_PORT=9990 EXTERNAL_URI_SCHEME=https:// tools/run-dev --interface=''
```
## Beta
```sh
# https://zulip.readthedocs.io/en/latest/production/requirements.html#operating-system
sudo add-apt-repository universe
sudo apt update

# https://zulip.readthedocs.io/en/latest/production/install.html
git clone https://github.com/KOLLA-AI/k-chat-server.git
cd k-chat-server
git checkout beta
sudo -s
YOUR_EMAIL=hao.nguyendang@vietis.com.vn
YOUR_HOSTNAME=chat-beta.kollabridge.com
scripts/setup/install --certbot --email=$YOUR_EMAIL --hostname=$YOUR_HOSTNAME
# open link displayed in terminal

# /etc/zulip/zulip.conf
# server setting file
# /etc/zulip/settings.py
# secret file
# /etc/zulip/zulip-secrets.conf
# add openai, replicate key

# update code
sudo su zulip -c 'git -C /home/zulip/deployments/current pull'
# pip3 install --force-reinstall --require-hashes -r pip.txt
# pip3 install --use-deprecated=legacy-resolver --no-deps --require-hashes -r requirements/prod.txt
sudo su zulip -c '/home/zulip/deployments/current/tools/update-prod-static'
sudo su zulip -c '/home/zulip/deployments/current/scripts/restart-server'
```

## Upgrade zulip 7.5 -->8x
```
YOUR_EMAIL=hao.nguyendang@vietis.com.vn
YOUR_HOSTNAME=chat-beta.kollabridge.com

sudo -s
change to root and command run self-certbot:

scripts/setup/install --self-signed-cert --email=$YOUR_EMAIL --hostname=chat-dev-8x.kollabridge.com --postgresql-version 14

command run certbot:
- scripts/setup/install --certbot --email=$YOUR_EMAIL --hostname=$YOUR_HOSTNAME --postgresql-version 14

## Error when running install:
# start rabbitmq error cuz missing erlang
- apt install rabbitmq-server erlang

# add safe directory when cache zulip git version
git config --global --add safe.directory /home/zulip/deployments/2024-07-25-04-03-58

```

