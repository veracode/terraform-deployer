FROM python:2-slim
MAINTAINER @pllsaph

RUN apt-get update > /dev/null

# Need to fix the locales on ubuntu
RUN apt-get install -y locales && locale-gen en_US.UTF-8
COPY ./src/locale /etc/default/locale

RUN echo "US/Eastern" > /etc/timezone && apt-get install -y --reinstall tzdata
# --------------------------------------------------------------------
# Consolidating as many environment variables as possible.
# --------------------------------------------------------------------
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LC_COLLATE=C \
    LC_CTYPE=en_US.UTF-8 \
    TZ=UTC \
    PATH=/usr/local/terraform:$PATH \
    HOME=/root \
    CONTAINER_NAME=seek-and-deploy

RUN cat /etc/apt/sources.list

RUN set -euo &&		\
     apt-get install -y \
     apt-utils		\
     automake		\
     autoconf		\
     dpkg-dev		\
     devscripts		\
     make		\
     rsync		\
     reprepro		\
     software-properties-common \
     wget		\
     git		\
     unzip		\
     curl		\
     bind9utils		\
     bind9-host		\
     dnsutils		\
     host		\
     rsync		\
     netcat

RUN pip install awscli --force-reinstall --upgrade --ignore-installed

RUN pip list 2>&1 /dev/null | grep awscli
RUN echo "PATH = $PATH"

RUN wget -nv https://releases.hashicorp.com/terraform/0.11.11/terraform_0.11.11_linux_amd64.zip

RUN unzip terraform_0.11.11_linux_amd64.zip -d /usr/local/bin
RUN terraform --version

RUN mkdir /deployer
COPY . /deployer

RUN mkdir /tmp/deployer_dir
RUN cd /deployer && pip install -r requirements.txt  && make install


# ---------------------------------------------------------
# END: final cleanups.
# ---------------------------------------------------------

CMD ["bash"]
