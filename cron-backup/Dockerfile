FROM debian:buster-slim
USER root

# pg_rmanの設定
ARG RMAN_VER=1.3.9
ARG PG_VER=12

# 日本時間に設定
ENV TZ=Asia/Tokyo

# cronを入れる
RUN apt-get update && apt-get -y install busybox-static nkf

# cron設定をコピー
COPY ./config/crontab /var/spool/cron/crontabs/root
RUN nkf -Lu --overwrite /var/spool/cron/crontabs/root

# Postgress クライアントをインストール
RUN apt -y install lsb-release wget gnupg2 &&\
  wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - 
RUN  echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" | tee  /etc/apt/sources.list.d/pgdg.list &&\
  apt update &&\
  apt -y install postgresql-client-12

# バックアップに使用するツール
RUN apt-get -y install p7zip-full bc

# pg_rmanのビルドツールをインストール
WORKDIR /root
RUN apt update &&\
  apt-get install -y gcc make libpq-dev zlib1g-dev libpam0g-dev libssl-dev libselinux1-dev libkrb5-dev libedit-dev postgresql-server-dev-12 git
# Release zipだとビルド出来なくなっていたので、
# gitからtag指定で取得する
RUN mkdir pg_rman_git &&\
  cd pg_rman_git &&\
  git clone https://github.com/ossc-db/pg_rman.git &&\
  cd pg_rman &&\
  git checkout V1.3.9&&\
  make &&\
  make install

# S3用自動バックアップ用にAWS　CLIをインストール
RUN apt update &&\
  apt-get install -y curl unzip less 

# AWS CLIのコマンドはアーキテクチャによって異なるので、アーキテクチャによって分岐する
RUN if [ `dpkg --print-architecture` = "arm64" ]; then \
      curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"; \
    else \
      curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"; \
    fi 
RUN  unzip awscliv2.zip &&\
  ./aws/install &&\
  /usr/local/bin/aws --version

# キャッシュを消去
RUN apt-get -y clean \
  && rm -rf /var/lib/apt/lists/*

# postgressのバックアップ設定
WORKDIR /root
RUN echo "*:*:*:*:mypass-abc" > /root/.pgpass
RUN chmod 600 .pgpass
COPY ./shell/pg_dumpall.sh /var/backup_sh/pg_dumpall.sh
COPY ./shell/pg_rman.sh /var/backup_sh/pg_rman.sh
COPY ./shell/syncToS3.sh /var/backup_sh/syncToS3.sh
RUN nkf -Lu  --overwrite /var/backup_sh/pg_dumpall.sh
RUN nkf -Lu  --overwrite /var/backup_sh/pg_rman.sh
RUN nkf -Lu  --overwrite /var/backup_sh/syncToS3.sh
RUN chmod +x /var/backup_sh/pg_dumpall.sh
RUN chmod +x /var/backup_sh/pg_rman.sh
RUN chmod +x /var/backup_sh/syncToS3.sh


CMD busybox crond -l 2 -L /dev/stderr -f
