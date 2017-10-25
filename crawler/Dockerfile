FROM debian:jessie
MAINTAINER      bignewbie "dhfang812@163.com"

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

ENV BASEDIR /usr/src/app/crawler

# 添加阿里源，网易源下载特别缓慢
ADD ./sources.list /etc/apt/

# chronium + selenium
RUN apt-get update && apt-get install -yq --no-install-recommends \
    ca-certificates \
    curl \
    xvfb \
    chromium \
    unzip \
    build-essential \
    python-dev \
    libmysqlclient-dev \
    gcc \
    libsasl2-dev \
    libsasl2-modules \
    libaio-dev \
    cron \
    git \
    libgconf-2-4 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ADD xvfb-chromium /usr/bin/xvfb-chromium
RUN ln -s /usr/bin/xvfb-chromium /usr/bin/google-chrome
RUN ln -s /usr/bin/xvfb-chromium /usr/bin/chromium-browser

# anaconda
RUN mkdir -p $BASEDIR \
    && curl  https://repo.continuum.io/archive/Anaconda2-5.0.0.1-Linux-x86_64.sh -o $BASEDIR/anaconda.sh \
    && /bin/bash $BASEDIR/anaconda.sh -b -p $BASEDIR/anaconda \
    && rm $BASEDIR/anaconda.sh 

ENV PATH="$BASEDIR/anaconda/bin:${PATH}"

RUN conda update anaconda && rm -rf /usr/bin/python && ln -s BASEDIR/anaconda/bin/python /usr/bin/python

RUN pip install pandas \
                numpy \
                cx_Oracle \
                pyhdfs \
                pyhive \
                thrift \
                pyarrow \
                mysqlclient \
                sasl \
                thrift_sasl \
                setuptools \
                selenium

ENV CHROMEDRIVER_VERSION 2.29
ENV CHROMEDRIVER_SHA256 bb2cf08f2c213f061d6fbca9658fc44a367c1ba7e40b3ee1e3ae437be0f901c2


RUN curl -SLO  "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
  && echo "$CHROMEDRIVER_SHA256  chromedriver_linux64.zip" | sha256sum -c - \
  && unzip "chromedriver_linux64.zip" -d /usr/local/bin \
  && rm "chromedriver_linux64.zip"


# 下载Hive数据库需要的包，需要网易git帐号密码，分别替换username和password即可，如果存在特殊字符如@#$, 
# 可先使用python或java提供的urlencode编码，替换即可，也可使用下面的表格自行更换，如密码pass@123变为pass%40123：
#===========================================================================
#=  !   #   $    &   '   (   )   *   +   ,   /   :   ;   =   ?   @   [   ] =
#= %21 %23 %24 %26 %27 %28 %29 %2A %2B %2C %2F %3A %3B %3D %3F %40 %5B %5D =
#===========================================================================

RUN git clone https://username:password@git.ms.netease.com/bigdata/mining-api.git
WORKDIR $BASEDIR/mining-api/simple-io-py/
RUN python setup.py install && rm -rf $BASEDIR/mining-api

# 切换到工作目录
WORKDIR $BASEDIR


# 添加爬虫文件
ADD ./ $BASEDIR
# crontab配置
ADD ./root /var/spool/cron/crontabs/root
# 复制crontabfile到/etc/crontab
# 设置文件所有者和文件关联组为 root:crontab ，关联组必须为 crontab
RUN chown -R root:crontab /var/spool/cron/crontabs/root \
# 修改文件的权限，必须为 600，否则不认
 && chmod 600 /var/spool/cron/crontabs/root
RUN touch /var/log/cron.log

RUN chmod +x $BASEDIR/start.sh
RUN chmod +x $BASEDIR/crawler.sh
CMD bash $BASEDIR/start.sh

# 设置时间同步
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime 
