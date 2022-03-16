FROM mcr.microsoft.com/dotnet/sdk:6.0
USER root

# 必要なツールをビルド
WORKDIR /tmp
RUN apt update \
	&& apt install -y \
	apt-utils\
	git \
	curl \
	supervisor \
	locales \
	tzdata \
	nkf\
	# 画像の拡大縮小で必要
	libgdiplus\
	#パラメータ調整
	rsync\
	unzip

RUN apt-get clean \
	&& rm -rf /var/apt/cache/* /tmp/* /var/tmp/* \
	&& locale-gen ja_JP.UTF-8

# 対象となるコードを取得
RUN wget https://github.com/Implem/Implem.Pleasanter.NetCore/releases/download/Pleasanter_1.3.2.0/Pleasanter_1.3.2.0.zip

RUN unzip Pleasanter_1.3.2.0.zip
RUN cp -a pleasanter ../home/publish/

WORKDIR /home/publish
COPY supervisord.conf /usr/local/etc/supervisord.conf
COPY Rds.json Implem.Pleasanter/App_Data/Parameters/Rds.json
COPY pleasanter.sh cmdnetcore/pleasanter.sh
COPY parameters/init_send Implem.Pleasanter/App_Data/Parameters/
RUN echo 'export LANG=ja_JP.UTF-8' >> ~/.bashrc

RUN nkf -Lu --overwrite /usr/local/etc/supervisord.conf && \
	nkf -Lu --overwrite Implem.Pleasanter/App_Data/Parameters/Rds.json &&\
	nkf -Lu --overwrite cmdnetcore/pleasanter.sh
RUN chmod 744 cmdnetcore/*.sh

EXPOSE 80 1433
CMD ["/usr/bin/supervisord", "-n", "-c", "/usr/local/etc/supervisord.conf"]
