FROM ubuntu:16.04
MAINTAINER @pllsaph

RUN apt-get update > /dev/null

# Need to fix the locales on ubuntu
RUN apt-get install -y locales && locale-gen en_US.UTF-8
COPY ./src/locale /etc/default/locale

# --------------------------------------------------------------------
# Consolidating as many environment variables as possible.
# --------------------------------------------------------------------
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LC_COLLATE=C \
    LC_CTYPE=en_US.UTF-8 \
    PATH=/usr/local/terraform:$PATH \
    HOME=/root \
    CONTAINER_NAME=seek-and-deploy


RUN set -euo && \
    apt-get install -y	 \
    	    git	    	 \
	    libffi-dev	 \
	    libffi6	 \
    	    openssl	 \
	    python	 \
	    python-pip	 \
	    unzip	 \
	    wget	 

RUN wget -nv https://releases.hashicorp.com/terraform/0.11.11/terraform_0.11.11_linux_amd64.zip
RUN unzip terraform_0.11.11_linux_amd64.zip -d /usr/local/bin
RUN terraform --version

COPY . /deployer

RUN mkdir /tmp/deployer_dir
RUN pip install awscli
RUN cd /deployer && pip install -r requirements.txt  && make install


# ---------------------------------------------------------
# END: final cleanups.
# ---------------------------------------------------------

CMD ["bash"]
