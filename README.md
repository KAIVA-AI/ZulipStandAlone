# Kaiva2025.En.Zulip

```sh
sudo su
# setup swap ram 16GB 16384
YOUR_EMAIL=hao.nguyendang@vietis.com.vn
YOUR_HOSTNAME=zulip.en.kaiva.vietis.com.vn
apt-get install -y gettext
# uncomment update corepack latest in scripts/lib/node_cache.py # TODO not work yet
scripts/setup/install --self-signed-cert --email=$YOUR_EMAIL --hostname=$YOUR_HOSTNAME
# comment update corepack latest in scripts/lib/node_cache.py

# setup certbot

./manage.py change_user_role -r 2 hao.nguyendang@vietis.com.vn can_create_users

# add postgres dev user
# add bot user
```
