FROM jupyter/scipy-notebook

MAINTAINER Jay Johnson <jay.p.h.johnson@gmail.com>

USER root

# Install all OS dependencies for notebook server that starts but lacks all
# features (e.g., download as all possible file formats)
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -y

RUN apt-get install -yq --no-install-recommends \
    jed \
    emacs \
    build-essential \
    python-dev \
    python-setuptools \
    unzip \
    libsm6 \
    pandoc \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-fonts-recommended \
    texlive-generic-recommended \
    libxrender1 \
    julia \
    libnettle4 \
    git \
    sqlite \
    vim \
    wget \
    mlocate \
    cron \
    rsyslog \
    logrotate \
    gcc \
    telnet \
    tree \
    curl \
    tar \
    net-tools \
    mariadb-server \
    libmysqlclient-dev \
    fonts-dejavu \
    gfortran \
    libav-tools \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libpcap-dev \
    libsqlite3-dev \
    libattr1-dev \
    libffi-dev \
    && apt-get clean

RUN apt-get install -yq --no-install-recommends \
    libatlas-base-dev \
    libopenblas-dev \
    libopencv-dev \
    libprotobuf-dev \
    liblapack-dev \
    libleveldb-dev \
    protobuf-compiler \
    libsnappy-dev \
    libboost-all-dev \
    && apt-get clean

RUN apt-get install -yq --no-install-recommends \
    libgflags-dev \
    libgoogle-glog-dev \
    liblmdb-dev \
    && apt-get clean

RUN apt-get remove -y librdkafka*
# Install the new Confluent Kafka toolchain for using their kafka client: https://github.com/confluentinc/confluent-kafka-python / http://blog.parsely.com/post/3886/pykafka-now
RUN wget -qO - http://packages.confluent.io/deb/3.0/archive.key | sudo apt-key add -
RUN echo "deb [arch=amd64] http://packages.confluent.io/deb/3.0 stable main" >> /etc/apt/sources.list
RUN apt-get update -y && apt-get install -y confluent-platform-2.11 librdkafka-dev

ENV NB_USER jovyan
ENV ENV_PORT 8888
ENV ENV_PROJ_DIR /opt/work
ENV ENV_DATA_DIR /opt/work/data
ENV ENV_DATA_SRC_DIR /opt/work/data/src
ENV ENV_DATA_DST_DIR /opt/work/data/dst
ENV ENV_REDIS_HOST localhost
ENV ENV_REDIS_PORT 6000
ENV ENV_REDIS_SRC_KEY JUPYTER_SRC_KEY
ENV ENV_REDIS_DST_KEY JUPYTER_DST_KEY

# Coordinate events without changing the container
ENV ENV_SYNTHESIZE_DIR /opt/work/data/synthesize
ENV ENV_SYNTHESIZE_BIN /opt/containerfiles/synthesize.sh
ENV ENV_TIDY_DIR /opt/work/data/tidy
ENV ENV_TIDY_BIN /opt/containerfiles/tidy.sh
ENV ENV_ANALYZE_DIR /opt/work/data/analyze
ENV ENV_ANALYZE_BIN /opt/containerfiles/analyze.sh
ENV ENV_OUTPUT_DIR /opt/work/data/output
ENV ENV_OUTPUT_BIN /opt/containerfiles/output-model.sh
ENV ENV_REDIS_MODEL_OUT_BIN /opt/containerfiles/redis-model.sh
ENV ENV_REDIS_MODEL_DST_KEY JUPYTER_REDIS_MODEL_DST_KEY

# Bin and Libs Dir
ENV ENV_BINS /opt/work/bins
ENV ENV_LIBS /opt/work/libs

# Configuration Dir:
ENV ENV_CONFIGS_DIR /opt/work/configs

# Global Python Dirs:
ENV ENV_PYTHON_SRC_DIR /opt/work/src
ENV ENV_PYTHON_COMMON_DIR /opt/work/src/common
ENV ENV_PYTHON_REDIS_DIR /opt/work/src/connectors/redis
ENV ENV_PYTHON_DB_DIR /opt/work/src/connectors/database
ENV ENV_PYTHON_SCHEMA_DIR /opt/work/src/databases/schema
ENV ENV_PYTHON_CORE_CONFIG /opt/work/configs/jupyter.json

# Slack Debugging Env:
ENV ENV_SLACK_BOTNAME bugbot
ENV ENV_SLACK_CHANNEL debugging
ENV ENV_SLACK_NOTIFY_USER jay
ENV ENV_SLACK_TOKEN xoxb-51351043345-Lzwmto5IMVb8UK36MghZYMEi
ENV ENV_SLACK_ENVNAME dev-jupyter
ENV ENV_SLACK_ENABLED 1

# Environment Deployment Type
ENV ENV_DEPLOYMENT_TYPE Local

USER root

# Python packages for interfacing with resources outside of this container
RUN conda install --quiet --yes \
    'coverage' \
    'seaborn' \
    'pcre' \
    'six' \
    'pika' \
    'python-daemon' \
    'feedparser' \
    'pytest' \
    'nose' \
    'lxml' \
    'Django' \
    'sphinx' \
    'sphinx-bootstrap-theme' \
    'requests' \
    'redis=3.2.0' \
    'hiredis' \
    'redis-py' \
    'boto' \
    'awscli' \
    'django-redis-cache' \
    'uwsgi' \
    'PyMySQL' \
    'psycopg2' \
    'pymongo' \
    'SQLAlchemy' \
    'pandas' \
    'numpy' \
    'tqdm' \
    'pandas-datareader' \
    'tensorflow' \
    'alembic' \
    'pyqt=4.11'

# Add Volumes and Set permissions
RUN mkdir -p -m 777 /opt \
    && mkdir -p -m 777 /opt/containerfiles \
    && chmod 777 /opt \
    && chmod 777 /opt/containerfiles \
    && touch /tmp/firsttimerunning

### Finish the setup using root
USER $NB_USER

# Add custom Python 2 pips:
COPY ./python2/ /opt/python2

RUN /opt/python2/install_pips.sh

USER root

RUN conda install pyqt=4.11 -y

# Configure container startup as root
EXPOSE 8888
#ENTRYPOINT ["tini", "--"]
CMD ["/opt/containerfiles/start-container.sh"]

#########################################################
#
# Add Files into the container now that the setup is done
#
# Add the starters and installers:
ADD ./containerfiles/ /opt/containerfiles/

RUN chmod 777 /opt/containerfiles/*.sh \
    && cp /opt/containerfiles/bashrc ~/.bashrc \
    && cp /opt/containerfiles/vimrc  ~/.vimrc \
    && cp /opt/containerfiles/bashrc /home/$NB_USER/.bashrc \
    && cp /opt/containerfiles/vimrc  /home/$NB_USER/.vimrc \
    && chown $NB_USER /home/$NB_USER/.bashrc \
    && chown $NB_USER /home/$NB_USER/.vimrc \
    && chmod 664 /home/$NB_USER/.bashrc \
    && chmod 664 /home/$NB_USER/.vimrc 

RUN echo 'export PATH=$PATH:/opt/conda/envs/python2/bin:/opt/conda/bin:/opt/work/bins' >> /root/.bashrc \
    && echo '' >> /home/$NB_USER/.bashrc \
    && echo 'if [[ "${PYTHONPATH}" == "" ]]; then' >> /root/.bashrc \
    && echo '   export PYTHONPATH=/opt/work' >> /root/.bashrc \
    && echo 'else' >> /root/.bashrc \
    && echo '   export PYTHONPATH=$PYTHONPATH:/opt/work' >> /root/.bashrc \
    && echo 'fi' >> /root/.bashrc \
    && echo '' >> /root/.bashrc \
    && echo 'source activate python2' >> /root/.bashrc \
    && echo '' >> /root/.bashrc \
    && mv /usr/bin/vi /usr/bin/bak.vi \
    && cp /usr/bin/vim /usr/bin/vi

RUN echo 'export PATH=$PATH:/opt/conda/envs/python2/bin:/opt/conda/bin:/opt/work/bins' >> /home/$NB_USER/.bashrc \
    && echo '' >> /home/$NB_USER/.bashrc \
    && echo 'if [[ "${PYTHONPATH}" == "" ]]; then' >> /home/$NB_USER/.bashrc \
    && echo '   export PYTHONPATH=/opt/work' >> /home/$NB_USER/.bashrc \
    && echo 'else' >> /home/$NB_USER/.bashrc \
    && echo '   export PYTHONPATH=$PYTHONPATH:/opt/work' >> /home/$NB_USER/.bashrc \
    && echo 'fi' >> /home/$NB_USER/.bashrc \
    && echo '' >> /home/$NB_USER/.bashrc \
    && echo 'source activate python2' >> /home/$NB_USER/.bashrc \
    && echo '' >> /home/$NB_USER/.bashrc

# Add local files as late as possible to avoid cache busting
RUN cp /opt/containerfiles/start-notebook.sh /usr/local/bin/ \
    && cp /opt/containerfiles/start-singleuser.sh /usr/local/bin/ \
    && cp /opt/containerfiles/jupyter_notebook_config.py /home/$NB_USER/.jupyter/ \
    && mkdir -p -m 777 /opt/python2 \
    && chmod 777 /opt \
    && chown -R $NB_USER:users /opt/python2 \
    && mkdir -p -m 777 /opt/work/ \
    && chmod 777 /opt \
    && chmod 777 /opt/work \
    && chown -R $NB_USER:users /opt/work \
    && mkdir -p -m 777 /opt/work/examples \
    && mkdir -p -m 777 /opt/work/src \
    && mkdir -p -m 777 /opt/work/env \
    && mkdir -p -m 777 /opt/work/bins \
    && mkdir -p -m 777 /opt/work/libs \
    && mkdir -p -m 777 /opt/work/configs \
    && mkdir -p -m 777 /opt/work/pips \
    && mkdir -p -m 777 /opt/work/data \
    && chown -R $NB_USER:users /opt/work/examples \
    && chown -R $NB_USER:users /opt/work/src \
    && chown -R $NB_USER:users /opt/work/env \
    && chown -R $NB_USER:users /opt/work/bins \
    && chown -R $NB_USER:users /opt/work/libs \
    && chown -R $NB_USER:users /opt/work/configs \
    && chown -R $NB_USER:users /opt/work/pips \
    && chown -R $NB_USER:users /opt/work/data 

WORKDIR /opt/work

ENV ENV_IN_DOCKER 1

COPY ./libs/ /opt/work/libs/
COPY ./configs/ /opt/work/configs/
COPY ./bins/ /opt/work/bins/
COPY ./src/ /opt/work/src/
COPY ./env/ /opt/work/env/
COPY ./examples /opt/work/examples/

# Assign all permissions over:
RUN chown -R $NB_USER:users /opt/work/* \
    && chmod 777 /opt/work/bins/*

#########################################################
#
# Run as the user
#
USER $NB_USER

# Track the Python 2 and Python 3 pips and Conda Environment
RUN pip2 freeze > /opt/work/pips/python2-requirements.txt \
    && pip3 freeze > /opt/work/pips/python3-requirements.txt
