FROM debian@sha256:32a225e412babcd54c0ea777846183c61003d125278882873fb2bc97f9057c51

MAINTAINER Jay Johnson <jay.p.h.johnson@gmail.com>

USER root

# Install all OS dependencies for notebook server that starts but lacks all
# features (e.g., download as all possible file formats)
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -yq --no-install-recommends \
    wget \
    bzip2 \
    ca-certificates \
    sudo \
    locales \
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
    && apt-get clean

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

# Install Tini
RUN wget --quiet https://github.com/krallin/tini/releases/download/v0.9.0/tini && \
    echo "faafbfb5b079303691a939a747d7f60591f2143164093727e870b289a44d9872 *tini" | sha256sum -c - && \
    mv tini /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini

# Configure environment
ENV NB_USER driver
ENV NB_UID 1000
ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH
ENV SHELL /bin/bash
ENV HOME /home/$NB_USER
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
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
ENV ENV_ANALYZE_BIN /opt/containerfiles/analzye.sh
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

# Create driver user with UID=1000 and in the 'users' group
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \
    mkdir -p $CONDA_DIR && \
    chown $NB_USER $CONDA_DIR

USER root

# Add Volumes and Set permissions
RUN mkdir -p -m 777 /opt \
    && mkdir -p -m 777 /opt/containerfiles \
    && chmod 777 /opt \
    && chmod 777 /opt/containerfiles \
    && touch /tmp/firsttimerunning

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

USER $NB_USER

# Setup driver home directory
RUN mkdir /home/$NB_USER/.jupyter && \
    mkdir -p -m 700 /home/$NB_USER/.local/share/jupyter && \
    echo "cacert=/etc/ssl/certs/ca-certificates.crt" > /home/$NB_USER/.curlrc

# Install conda as driver
RUN cd /tmp && \
    mkdir -p $CONDA_DIR && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-3.19.0-Linux-x86_64.sh && \
    echo "9ea57c0fdf481acf89d816184f969b04bc44dea27b258c4e86b1e3a25ff26aa0 *Miniconda3-3.19.0-Linux-x86_64.sh" | sha256sum -c - && \
    /bin/bash Miniconda3-3.19.0-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm Miniconda3-3.19.0-Linux-x86_64.sh && \
    $CONDA_DIR/bin/conda install --quiet --yes conda==3.19.1 && \
    $CONDA_DIR/bin/conda config --system --add channels conda-forge && \
    conda clean -tipsy

# Temporary workaround for https://github.com/jupyter/docker-stacks/issues/210
# Stick with jpeg 8 to avoid problems with R packages
RUN echo "jpeg 8*" >> /opt/conda/conda-meta/pinned

# Install Jupyter notebook as driver
RUN conda install --quiet --yes \
    'notebook=4.2*' \
    && conda clean -tipsy

# Install JupyterHub to get the jupyterhub-singleuser startup script
RUN pip --no-cache-dir install 'jupyterhub==0.5'

USER root

# Add local files as late as possible to avoid cache busting
RUN cp /opt/containerfiles/start-notebook.sh /usr/local/bin/ \
    && cp /opt/containerfiles/start-singleuser.sh /usr/local/bin/ \
    && cp /opt/containerfiles/jupyter_notebook_config.py /home/$NB_USER/.jupyter/

RUN chown -R $NB_USER:users /home/$NB_USER/.jupyter

# Switch back to driver to avoid accidental container runs as root
USER $NB_USER


# End of base notebook
#####################################


#####################################
# Start of sci-py notebook

# Install Python 3 packages
# Remove pyqt and qt pulled in for matplotlib since we're only ever going to
# use notebook-friendly backends in these images
RUN conda install --quiet --yes \
    'ipywidgets=5.1*' \
    'pandas=0.18*' \
    'numexpr=2.5*' \
    'matplotlib=1.5*' \
    'scipy=0.17*' \
    'seaborn=0.7*' \
    'scikit-learn=0.17*' \
    'scikit-image=0.11*' \
    'sympy=1.0*' \
    'cython=0.23*' \
    'patsy=0.4*' \
    'statsmodels=0.6*' \
    'cloudpickle=0.1*' \
    'dill=0.2*' \
    'numba=0.23*' \
    'bokeh=0.11*' \
    'h5py=2.5*' && \
    conda remove --quiet --yes --force qt pyqt && \
    conda clean -tipsy
# Activate ipywidgets extension in the environment that runs the notebook server
RUN jupyter nbextension enable --py widgetsnbextension --sys-prefix

# Install Python 2 packages
# Remove pyqt and qt pulled in for matplotlib since we're only ever going to
# use notebook-friendly backends in these images
RUN conda create --quiet --yes -p $CONDA_DIR/envs/python2 python=2.7 \
    'ipython=4.2*' \
    'ipywidgets=5.1*' \
    'pandas=0.18*' \
    'numexpr=2.5*' \
    'matplotlib=1.5*' \
    'scipy=0.17*' \
    'seaborn=0.7*' \
    'scikit-learn=0.17*' \
    'scikit-image=0.11*' \
    'sympy=1.0*' \
    'cython=0.23*' \
    'patsy=0.4*' \
    'statsmodels=0.6*' \
    'cloudpickle=0.1*' \
    'dill=0.2*' \
    'numba=0.23*' \
    'bokeh=0.11*' \
    'h5py=2.5*' \
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
    'alembic' \
    'tensorflow' \
    'pyzmq' && \
    conda remove -n python2 --quiet --yes --force qt pyqt && \
    conda clean -tipsy

# Add shortcuts to distinguish pip for python2 and python3 envs
RUN ln -s $CONDA_DIR/envs/python2/bin/pip $CONDA_DIR/bin/pip2 && \
    ln -s $CONDA_DIR/bin/pip $CONDA_DIR/bin/pip3

# Configure ipython kernel to use matplotlib inline backend by default
RUN mkdir -p $HOME/.ipython/profile_default/startup
RUN cp /opt/containerfiles/mplimporthook.py  $HOME/.ipython/profile_default/startup/

USER root

# Install Python 2 kernel spec globally to avoid permission problems when NB_UID
# switching at runtime.
RUN $CONDA_DIR/envs/python2/bin/python -m ipykernel install

USER $NB_USER

# End of sci-py notebook
#####################################

#####################################
# Start of derived notebook

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
    'alembic'

# R packages including IRKernel which gets installed globally.
RUN conda config --add channels r && \
    conda install --quiet --yes \
    'rpy2=2.8*' \
    'r-base=3.3*' \
    'r-irkernel=0.6*' \
    'r-plyr=1.8*' \
    'r-devtools=1.11*' \
    'r-dplyr=0.4*' \
    'r-ggplot2=2.1*' \
    'r-tidyr=0.5*' \
    'r-shiny=0.13*' \
    'r-rmarkdown=0.9*' \
    'r-forecast=7.1*' \
    'r-stringr=1.0*' \
    'r-rsqlite=1.0*' \
    'r-reshape2=1.4*' \
    'r-nycflights13=0.2*' \
    'r-caret=6.0*' \
    'r-rcurl=1.95*' \
    'r-randomforest=4.6*' && conda clean -tipsy

# Install IJulia packages as driver and then move the kernelspec out
# to the system share location. Avoids problems with runtime UID change not
# taking effect properly on the .local folder in the driver home dir.
RUN julia -e 'Pkg.add("IJulia")' && \
    mv /home/$NB_USER/.local/share/jupyter/kernels/julia* $CONDA_DIR/share/jupyter/kernels/ && \
    chmod -R go+rx $CONDA_DIR/share/jupyter

# Show Julia where conda libraries are
# Add essential packages
RUN echo "push!(Sys.DL_LOAD_PATH, \"$CONDA_DIR/lib\")" > /home/$NB_USER/.juliarc.jl && \
    julia -e 'Pkg.add("Gadfly")' && julia -e 'Pkg.add("RDatasets")' && julia -F -e 'Pkg.add("HDF5")'

RUN echo 'export PATH=$PATH:/opt/work/bins' >> /home/$NB_USER/.bashrc \
    && echo 'export PYTHONPATH=$PYTHONPATH:/opt/work/src' >> /home/$NB_USER/.bashrc

# Add custom Python 2 pips:
RUN pip2 install slackclient argparse feedparser bs4 logging openpyxl cookiecutter mimeparse constants flup importlib watermark uuid engarde q prettyplotlib dotenv MySQL-python

# Add custom Python 3 pips:
RUN pip3 install slackclient argparse feedparser openpyxl cookiecutter mimeparse constants watermark uuid engarde q prettyplotlib dotenv

### Finish the setup using root
USER root

# Configure container startup as root
EXPOSE 8888
#ENTRYPOINT ["tini", "--"]
CMD ["/opt/containerfiles/start-container.sh"]

RUN echo 'export PATH=$PATH:/opt/work/bins' >> /root/.bashrc \
    && echo 'export PYTHONPATH=$PYTHONPATH:/opt/work/src' >> /root/.bashrc \
    && mv /usr/bin/vi /usr/bin/bak.vi \
    && cp /usr/bin/vim /usr/bin/vi


#########################################################
#
# Add Files into the container now that the setup is done
#
RUN mkdir -p -m 777 /opt/work/ \
    && chmod 777 /opt \
    && chmod 777 /opt/work \
    && chown -R $NB_USER:users /opt/work \
    && mkdir -p -m 777 /opt/work/examples \
    && mkdir -p -m 777 /opt/work/src \
    && mkdir -p -m 777 /opt/work/bins \
    && mkdir -p -m 777 /opt/work/libs \
    && mkdir -p -m 777 /opt/work/configs \
    && mkdir -p -m 777 /opt/work/pips \
    && mkdir -p -m 777 /opt/work/data \
    && chown -R $NB_USER:users /opt/work/examples \
    && chown -R $NB_USER:users /opt/work/src \
    && chown -R $NB_USER:users /opt/work/bins \
    && chown -R $NB_USER:users /opt/work/libs \
    && chown -R $NB_USER:users /opt/work/configs \
    && chown -R $NB_USER:users /opt/work/pips \
    && chown -R $NB_USER:users /opt/work/data 

WORKDIR /opt/work

COPY ./libs/ /opt/work/libs/
COPY ./configs/ /opt/work/configs/
COPY ./bins/ /opt/work/bins/
COPY ./src/ /opt/work/src/
COPY ./examples /opt/work/examples/

# Assign all permissions over:
RUN chown -R $NB_USER:users /opt/work/* \
    && chmod 777 /opt/work/bins/*

#########################################################
#
# Run as the user
#
USER $NB_USER

# Track the Python 2 and Python 3 pips 
RUN pip2 freeze > /opt/work/pips/python2-requirements.txt \
    && pip3 freeze > /opt/work/pips/python3-requirements.txt

# End of derived notebook
#####################################
