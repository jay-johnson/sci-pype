FROM centos:7
MAINTAINER Jay Johnson jay.p.h.johnson@gmail.com

RUN yum -y update && yum clean all

RUN yum -y install \
    curl \
    gcc \
    gcc-c++ \
    git \
    logrotate \
    python-pip \
    python-dev \
    python-setuptools \
    which \
    wget \
    make \
    mlocate \
    net-tools \
    telnet \
    tar \
    vim \
    vim-enhanced \
    && yum clean all \
    && wget http://download.redis.io/releases/redis-3.2.8.tar.gz -O /tmp/redis.gz \
    && pushd /tmp \
    && tar xvf /tmp/redis.gz \
    && rm /tmp/redis.gz \
    && cd redis-3.2.8 \
    && make \
    && make install \
    && rm -rf /tmp/redis.gz \
    && rm -rf /tmp/redis-3.2.8

RUN easy_install pip && \
    /usr/bin/pip install --upgrade pip && \
    /usr/bin/pip install --upgrade setuptools 

RUN mkdir -p -m 777 /opt \
    && mkdir -p -m 777 /opt/deps \
    && mkdir -p -m 777 /opt/work \
    && mkdir -p -m 777 /opt/work/bins \
    && mkdir -p -m 777 /opt/work/configs \
    && mkdir -p -m 777 /opt/work/data \
    && mkdir -p -m 777 /opt/work/data/dst \
    && mkdir -p -m 777 /opt/work/data/src \
    && mkdir -p -m 777 /opt/work/src \
    && mkdir -p -m 777 /opt/work/thirdparty \
    && mkdir -p -m 777 /opt/shared \
    && mkdir -p -m 777 /opt/tools \
    && mkdir -p -m 777 /opt/redis \
    && touch /tmp/firsttimerunning

WORKDIR /opt/work

CMD [ "redis-server" ]
