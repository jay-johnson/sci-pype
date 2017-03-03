FROM centos:7
MAINTAINER Jay Johnson <jay.p.h.johnson@gmail.com>

RUN yum install -y \
    cron \
    curl \
    logrotate \
    mlocate \
    net-tools \
    python-setuptools \
    ruby \
    ruby-dev \
    rsyslog \
    telnet \
    tar \
    vim \
    vim-enhanced \
    wget \
    && gem install --no-ri --no-rdoc bundler redis \
    && easy_install supervisor \
    && mkdir /etc/haproxy \
    && mkdir /etc/supervisor.d \
    && chmod 777 /etc/haproxy \
    && chmod 777 /etc/supervisor.d \
    && mkdir /opt/haproxy \
    && chmod 777 /opt/haproxy

WORKDIR /opt/haproxy

# Add the starters and installers:
ADD ./docker/ /opt/tools/

RUN chmod 777 /opt/tools/*.sh

RUN cp -rp /opt/tools/etc /opt/haproxy/ \
    && cp -rp /opt/tools/node /opt/haproxy/
# update, install required, clean

# Add files to start default-locations
RUN cp /opt/tools/bashrc /root/.bashrc \
    && cp /opt/tools/vimrc /root/.vimrc \
    && cp /opt/tools/gitconfig /root/.gitconfig \
    && cp /opt/tools/pre-start.sh /usr/local/bin/ \
    && cp /opt/tools/start-container.sh /usr/local/bin/ \
    && cp /opt/tools/post-start.sh /usr/local/bin/ \
    && cp /opt/tools/custom-pre-start.sh /usr/local/bin/ \
    && cp /opt/tools/start-services.sh /usr/local/bin/ \
    && cp /opt/tools/start-container.sh /opt/start-container.sh \
    && cp /opt/start-container.sh /usr/local/bin/start-container.sh \
    && mkdir -p -m 777 /opt/data/src /opt/data/dst \
    && chmod 644 /root/.bashrc && chown root:root /root/.bashrc \
    && cat /opt/tools/inputrc >> /etc/inputrc \
    && mkdir -p -m 777 /etc/supervisor.d \
    && touch /tmp/firsttimerunning

RUN cp /opt/haproxy/etc/supervisor.d/containerservices.ini /etc/supervisor.d/containerservices.ini \
    && chmod 777 /opt/haproxy/node \
    && touch /opt/haproxy/firsttimerunning \ 
    && cp /opt/haproxy/node/start_haproxy_node.sh /bin/start_haproxy_node.sh \
    && chmod 777 /bin/start_haproxy_node.sh \
    && yum -y update \
    && yum install -y haproxy \
    && updatedb \
    && yum clean all 

# Redis dir and start wrapper script
ENV ENV_HAPROXY_DIR /opt/haproxy
ENV ENV_CONFIGURABLES_DIR /opt/haproxy/node
ENV ENV_ETC_DIR /opt/haproxy/etc
ENV ENV_START_SERVICE /opt/haproxy/node/start_haproxy_node.sh

CMD [ "/opt/haproxy/node/start_haproxy_node.sh" ]
