FROM jayjohnson/redis-base:3.2.8

MAINTAINER Jay Johnson <jay.p.h.johnson@gmail.com>

# Environment Deployment Type
ENV ENV_DEPLOYMENT_TYPE DEV
ENV ENV_PROJ_DIR /opt/work
ENV ENV_DATA_DIR /opt/work/data
ENV ENV_DATA_SRC_DIR /opt/work/data/src
ENV ENV_DATA_DST_DIR /opt/work/data/dst
ENV ENV_SRC_DIR /opt/work/src
ENV ENV_THIRD_PARTY_DIR /opt/work/thirdparty
ENV ENV_CONFIGS_DIR /opt/work/configs

# Allow running starters from outside the container
ENV ENV_BIN_DIR /opt/work/bin
ENV ENV_PRESTART_SCRIPT /opt/tools/pre-start.sh
ENV ENV_START_SCRIPT /opt/tools/start-services.sh
ENV ENV_POSTSTART_SCRIPT /opt/tools/post-start.sh
ENV ENV_CUSTOM_SCRIPT /opt/tools/custom-pre-start.sh
ENV ENV_DEFAULT_VENV /venv
ENV ENV_AWS_ACCESS_KEY NOT_A_REAL_KEY
ENV ENV_AWS_SECRET_KEY NOT_A_REAL_KEY

ENV ENV_SSH_CREDS /opt/shared/.ssh
ENV ENV_GIT_CONFIG /opt/shared/.gitconfig
ENV ENV_AWS_CREDS /root/.aws/credentials
ENV ENV_AWS_PROFILE default

WORKDIR /opt/redis

# Add the starters and installers:
ADD ./docker/ /opt/tools/

RUN chmod 777 /opt/tools/*.sh 

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
    && mkdir -p -m 777 /etc/supervisor.d \
    && updatedb \
    && cat /opt/tools/inputrc >> /etc/inputrc

RUN cp -rp /opt/tools/etc /opt/redis/ \
    && cp -rp /opt/tools/node /opt/redis/ \
    && easy_install supervisor

# Redis dir and start wrapper script
ENV ENV_REDIS_DIR /opt/redis
ENV ENV_CONFIGURABLES_DIR /opt/redis/node
ENV ENV_ETC_DIR /opt/redis/etc
ENV ENV_START_SERVICE /opt/redis/node/start_redis_node.sh

CMD [ "/opt/start-container.sh" ]
  
