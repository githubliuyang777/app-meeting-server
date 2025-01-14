FROM openeuler/openeuler:21.03

MAINTAINER TommyLike<tommylikehu@gmail.com>

RUN yum update && \
    yum install -y vim wget git xz tar make automake autoconf libtool gcc gcc-c++ kernel-devel libmaxminddb-devel pcre-devel openssl openssl-devel tzdata \
        readline-devel libffi-devel python3-devel mariadb-devel python3-pip net-tools.x86_64 iputils

RUN pip3 install uwsgi

WORKDIR /work/app-meeting-server
COPY . /work/app-meeting-server
COPY ./deploy/fonts/simsun.ttc /usr/share/fonts

RUN cd /work/app-meeting-server && pip3 install -r requirements.txt
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.3/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz && \
    unxz wkhtmltox-0.12.3_linux-generic-amd64.tar.xz && \
    tar xvf wkhtmltox-0.12.3_linux-generic-amd64.tar && \
    mv wkhtmltox/bin/* /usr/local/bin && \
    rm -rf wkhtmltox && \
    rm -f wkhtmltox-0.12.3_linux-generic-amd64.tar

RUN cp /usr/bin/python3 /usr/bin/python
ENV LANG=en_US.UTF-8

EXPOSE 8080
ENTRYPOINT ["uwsgi", "--ini", "/work/app-meeting-server/deploy/production/uwsgi.ini"]
