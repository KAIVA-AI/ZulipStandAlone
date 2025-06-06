# Kaiva2025.En.Zulip

```sh
YOUR_EMAIL=hao.nguyendang@vietis.com.vn
YOUR_HOSTNAME=kaiva-en-zulip.collab.vietis.com.vn
sudo apt-get install gettext
scripts/setup/install --self-signed-cert --email=$YOUR_EMAIL --hostname=$YOUR_HOSTNAME

./manage.py change_user_role -r 2 hao.nguyendang@vietis.com.vn can_create_users
```
