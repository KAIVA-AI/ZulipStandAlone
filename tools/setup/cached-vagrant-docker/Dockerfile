# docker volume create --name=chat-server-beta
# set IS_WINDOWS true or IS_MACOS true in ~/.zulip-vagrant-config
# vagrant up --provider=docker --provision
# after provision, change postgresql setting
# run below to create a new image
# docker ps
# export CONTAINERID=
# docker commit $CONTAINERID chat-server:beta
# set IS_CACHED_BUILD true in ~/.zulip-vagrant-config
FROM chat-server:beta

RUN \
    # We use https://github.com/gdraheim/docker-systemctl-replacement
    # to make services we install like PostgreSQL, Redis, etc. normally
    # managed by systemd start within Docker, which breaks normal
    # operation of systemd.
    curl -fLsS --retry 3 -o ~vagrant/.ssh/authorized_keys 'https://raw.githubusercontent.com/hashicorp/vagrant/be7876d83644aa6bdf7f951592fdc681506bcbe6/keys/vagrant.pub' \
    && chown -R vagrant: ~vagrant/.ssh \
    && echo 'vagrant ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/vagrant
