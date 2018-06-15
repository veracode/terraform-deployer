FROM docker-ro.laputa.veracode.io/twowas/containers:m3-gradle-latest
MAINTAINER plussier@veracode.com

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
    CONTAINER_NAME=deployer


RUN set -euo pipefail && \
    yum -y update && \
    yum -y upgrade && \
    yum makecache && \
    yum install -y \
        make openssl libffi wget && \
    wget https://releases.hashicorp.com/terraform/0.10.2/terraform_0.10.2_linux_amd64.zip && \
    unzip terraform_0.10.2_linux_amd64.zip -d /usr/local/bin && \
    terraform --version

COPY . /deployer

RUN cd /deployer && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    mkdir /tmp/deployer_dir && \
    make install && \
    yum autoremove -y && \
    yum clean all
# ---------------------------------------------------------
# END: final cleanups.
# ---------------------------------------------------------

CMD ["bash"]
