---
title: pleasanter+PostgreSQL+SSL+dockerで自動バックアップを作ってみた(2022)
tags: PostgreSQL Docker Pleasanter
author: yamada28go
slide: false
---
# 概要

- [pleasanter+PostgreSQL+SSL+dockerで自動バックアップを作ってみた](https://qiita.com/yamada28go/items/4e1200ef22daf4e056d7)の2022年度版です。
- [前回記事](https://qiita.com/yamada28go/items/b9e6acdb4cca9572c7a6)の続きです。
- 本格的にシステムを使う事を考えた場合、バックアップはちゃんと考えておく必要が有ります。
- 素直に**RDS使えよ**という話もありますが、docker-composeファイル単体で動作する事を目指しました。
- 今回は自動でバックアップできるようにシステム化しました。
- 対応できるバックアップ種別は「Fullバックアップ」と「PITR(ポイント・イン・タイム・リカバリ)」です。
- AWS S3の設定を入れておくことで、バックアップデータをS3に同期する事も出来ます。

## Backupの方式

本コンテナ構成では2種類のバックアップ方式を使ってデータを保全するように設定されています。
それぞれのバックアップ方式に関しては下記に示します。

| 種別 | 概要 |メリット|デメリット|
|:-----------|:------------|:------------|:------------|
| 全バックアップ   | バックアップがSQL形式になるので復元が簡単|時間がかかる。容量が多い| BDに対してFull Backupを実行       | 
|  PITR   |早い。必要とされる容量が差分だけ。| 完全な復元に手間がかかる。 | PITR( (Point In Time Recovery) )を実行   | 

2種類のバックアップ処理は共にAWS S3への同期処理にを行うことができます。
AWS S3との同期を行っておくことでバックアップ完了後にバックアップデータをAWS S3上に同期する事ができるため、障害発生時にデータが失われるリスクを最小限にする事ができます。
ただし、RDSのようにミラーリングがかかっている訳ではないので、可用性が高まるという訳ではありません。


## バックアップの取得頻度

バックの動作管理はcronにより制御されています。
該当cromの設定は「cron-backup\config\crontab」にあります。
初期状態では以下の指定になっています。
必要に応じて、対象時間を切り替えてください。

| 種別 | 頻度 |
|:-----------|:------------|
|全バックアップ|毎日午前3時に1回|
|PITR(ポイント・イン・タイム・リカバリ)|30分毎|

## ローカル環境におけるバックアップの保持期間

本構成では長期的なデータの保管はAWS S3を使用する事を前提としています。
このため、ローカル環境におけるバックアップデータの保持期間は必要最低限となるように設定されています。
バックアップ期間を変更したい場合、後述のバックアップスクリプト上の定義を修正してください。

| 種別 | 頻度 |
|:-----------|:------------|
|全バックアップ|2日間|
|PITR(ポイント・イン・タイム・リカバリ)|1日間|

# コンテナ構成

作成したコンテナ構成は以下となります。

![スクリーンショット 2022-01-02 14.21.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/63200/bb2c37aa-4001-cf80-f019-2b81c50daadf.png)

postgres-dbとcron-backupはPITRを実現するためにDBの領域を共有しています。

| No | コンテナ名 | 概要 |定義ファイル|
|:-----------|:-----------|:------------|:------------|
|1| https-portal     | HTTPS通信用。Let's Encryptを用いた証明書取得の自動化      | docker-compose.https-portal.yml|
|2| pleasanter-web| PleasanterのWebシステム        | docker-compose.yml|
|3| postgres-db       | PostgreSQL DB(Pleasanterで使用されるDB)        |docker-compose.yml| 
|4| cron-backup     | バックアップ用のクローンプログラムを格納      | docker-compose.yml|

# バックアップスクリプト

自動バックアップ機構に使用されるスクリプトは以下となります。
これらのスクリプトはcron-backupコンテナに配備されます。

| スクリプト名 | 概要 |
|:-----------|:------------|
|   /var/backup_sh/pg_rman.sh   |   PITRを実行   | 
|   /var/backup_sh/pg_dumpall.sh   | Full Backupを実行       | 
|   /var/backup_sh/pg_dumpall.sh   | S3同期を実行      | 


# バックアップ設定
## ディレクトリ構成
pcron-backupコンテナから見たディレクトリ構成が下表となります。
共有が〇となっているパスに関してはpostgres-dbコンテナと共有しています。

バックアップ結果のデータは「/var/db_backup」に集まってくるように出来ています。
このため、このディレクトリをコンテナ外の接続してバックアップを取得しておけば必要なコンテナの外側からバックアップは取れる状態になります。

| パス名 | 概要 |コンテナ間共有 |
|:-----------|:------------|:------------|
| /var/db_backup/PITR/       |    ポイント・イン・タイム・リカバリ用のバックアップ結果保持ディレクトリ    | |
| /var/db_backup/dumpall     | 全データバックアップ結果保持ディレクトリ      | |
| /var/backup_sh| バックアップ用Shell格納ディレクトリ        | |
| /var/| バックアップ用Shell格納ディレクトリ        | |
| /var/lib/postgresql/data/|   postgresqlデータ領域    |〇  | 
| /var/lib/postgresql/arclog| postgresqlWAL領域       | 〇| 

--- 

## バックアップの開始

これらバックアップスクリプトはDocker Composeを起動すると自動的に起動を開始します。
開始にあたり、何か特別な操作は不要です。

バックアップを取りたくない場合、該当のコンテナを起動しないようにComposeファイルをコメントアウトしてください。

# S3同期設定
## 概要

先述したとおり、本構成では長期的に保持するデータはS3に保持する事を前提としています。
このため、長期的に使用される場合、S3の設定を実施される事をおすすめします。
**S3の設定が行われていな場合、S3同期処理は実行されません。**

## S3同期の有効化

AWS CLIの設定が存在する時に有効化されます。
有効化判定の対象となるパスは以下です。

「/root/.aws/config」

この設定ファイルはユーザーが調整する事が多いのでconfigとしてコンテナ内部にコピーさせるよりは、コンテナの外に置いておいてマウントさせるほうが楽です。
(以下の★の部分を外してください。)

```yaml:docker-compose.yml
  cron-backup:
    build:
      context: cron-backup/.
    volumes:
      - *APP_DB_data
      - *APP_DB_arclog
      # 自動バックアップされた結果は「/var/db_backup」に格納される。
      # コンテナの外からアクセスする場合は、このパスを外から見える所に配置しておく
      - db-backup:/var/db_backup
      # S3で自動バックアップする場合
      # aws cliの設定を以下パスに行う。
      # 存在しない場合はバックアップは行われない
      - ./cron-backup/config/aws-cli:/root/.aws/ ←　★
```

## 設定

ホストがWindows環境の場合、GITの設定によっては、**設定ファイルがCRLF**で取得される事があります。
設定ファイルをその状態でコンテナ内に持っていくと**改行コードが合わなくて正しく動かない**ので、設定ファイルの改行コードの取り扱いには注意してください。

まず、AWS CLIの設定が必要です。
このあたりは一般的な設定なので、ご自分のアカウントから必要な情報を取得してください。
[AWS CLIのインストールから初期設定メモ](https://qiita.com/n0bisuke/items/1ea245318283fa118f4a)

```config:cron-backup\config\aws-cli\credentials
[default]
aws_access_key_id = アクセスキー
aws_secret_access_key = シークレットキー 
```

次に、バックアップ対象の設定を行います。
これはshell形式の設定となります。

```bash:cron-backup\config\aws-cli\S3Config.sh
#!/bin/bash

# --- S3 同期設定

# 同期対象となる S3 バケット名
export S3_TARGET_BUCKET_NAME={バケット名}

# 同期対象となる S3 ディレクトリ名
export S3_TARGET_DIRECTORY_NAME={ディレクトリ名}
```

## 実行タイミング

S3への同期はバックアップ処理が実行されたタイミングとなります。
設定が正しくできていれば、開始のために特別な設定は不要です。

## 古いファイルの自動削除

S3上に同期されたバックアップデータに対して、古いファイルの削除動作はバックアップデータの取得方法に応じて異なります。
以下にバックアップ方式別に、S3におけるデータの保持期間を示します。

| 種別 | 保持期間|
|:-----------|:------------|
| 全バックアップ   |   S3上のバックアップファイルは追記されるのみで自動削除は行われない。    | 
|  PITR   | ローカルファイルの保持期間と同じ。  | 

全バックアップに関しては、デフォルトの状態のままですと、バックアップデータがたまり続ける事となります。

S3が標準に持つ機能として「ライフサイクル」という機能があり、この機能を使うと古くなったデータを自動的に削除することができます。古くなったデータの自動削除を検討してください。

[S3ライフサイクルルールで古いオブジェクトを自動削除する](https://nakada-r.com/2021/01/s3-lifecycle/)

----

# リストア

リストアに関しては、
バックアップデータの取得方法により戻し方が変わってきます。

## 全バックアップで取得した場合

以下、cron-backupコンテナで作業した事とします。
バックアップファイルは7z形式、かつ、暗号化されています。
適宜復元してください。
(暗号キーに関してはshellファイル「cron-backup\shell\pg_dumpall.sh」を参照してください。)
以下コマンドは、復元されたファイルが「backup」という名称となっている事を前提としています。
全バックアップからの復元は以下コマンド一発で完了です。

``` bash
 psql -h postgres-db -p 5432  -U postgres -f backup
```

## PITR

PITRの場合、少しややこしいです。
PITRの場合、postgresが動いているとうまく復元できないため、一旦コンテナ郡を落としてください。
次に、cron-backupコンテナだけ起動させます。

```
docker-compose up pleasanter-cron-backup
```

### 手順0 . データコピー

pleasanter-cron-backupコンテナで実施します。
復元に使用するデータを用意します。
復元に用いるデータは「/var/db_backup/PITR/」にコピーしてください。

### 手順1 . クーロン停止

pleasanter-cron-backupコンテナで実施します。
クーロンを普通に起動しておくとバックアップクーロンがデータのバックアップを開始してしまいます。
そこで、バックアップクーロン停止しておきます。

```
crontab -l > my_cron_backup.txt
crontab -r
```
### 手順2 . バックアップ済みデータ確認

pleasanter-cron-backupコンテナで実施します。
以下コマンドで取得済みのバックアップ一覧を表示します。

```
/usr/lib/postgresql/12/bin/pg_rman show  -B /var/db_backup/PITR/
```

コマンドを実行すると以下のようにバックアップとして戻すことが出来るタイミングの一覧が表示されます。

```
root@885777f50d56:~/out/cron-backup/shell# /usr/lib/postgresql/12/bin/pg_rman show  -B /var/db_backup/PITR/
=====================================================================
 StartTime           EndTime              Mode    Size   TLI  Status
=====================================================================
2020-09-22 21:44:35  2020-09-22 21:44:38  INCR    33kB     3  OK
2020-09-22 21:43:32  2020-09-22 21:43:35  INCR    33kB     3  OK
2020-09-22 21:40:54  2020-09-22 21:40:58  INCR    33kB     3  OK
2020-09-22 21:39:32  2020-09-22 21:39:35  INCR    33kB     3  OK
2020-09-22 21:38:47  2020-09-22 21:38:51  INCR    33kB     3  OK
2020-09-22 21:32:47  2020-09-22 21:36:18  FULL    61MB     3  OK
```

### 手順3 . リストア

pleasanter-cron-backupコンテナで実施します。
PITRの場合、戻し方には二つのパターンがあります。

#### 最終バックのタイミングに戻す

以下コマンドを用います。


```
/usr/lib/postgresql/12/bin/pg_rman restore  -B /var/db_backup/PITR/ -D /var/lib/postgresql/data/
```

#### 任意タイミングに戻す

任意タイミングに戻す場合、戻す対象の時間を指定する事が可能です。
コマンドは以下となり、「recovery-target-time」として対象時間を指定します。

```
/usr/lib/postgresql/12/bin/pg_rman restore  --recovery-target-time '2020-09-06 14:29:00'  -B /var/db_backup/PITR/ -D /var/lib/postgresql/data/
```

### 手順6 . クーロン戻し

pleasanter-cron-backupコンテナで実施します。
クーロンの設定を元に戻します。

```
crontab my_cron_backup.txt
crontab -l
```

## DBの整合性チェック


ここの処理は「全バックアップ」、「PITR」のいずれから戻した場合においても共通で必要となります。
バックアップ処理ではシステム動作中にデータを抜いてきています。
このため、DB上に存在するセッション情報などが中途半端な状態で残っています。

以下コマンドを使って、DB上の不要なデータを一度クリーンします。
(docker ホストで実行します。)

```
docker ps | grep leasanter-web | cut -d' ' -f 1  | xargs -I {} docker exec {} cmdnetcore/codedefiner.sh
```

## 後処理

DBを戻したら後処理が必要です。

### 速やかなFUllバックアップ

動くことを確認したら速やかにFullバックアップを取りましょう。
以下コマンドを直接叩く事でFullバックアップの取得が可能です。
ただし、S3設定がされている場合、S3への同期も走るので、十分注意して実施してください。

「flock --timeout=600 /tmp/db_backup.lock /var/backup_sh/pg_dumpall.sh」
 
### PITRにおけるベースバックアップの再取得

バックアップから戻した後の場合、PITRではベースバックアップがそれまでに取得されているものと変わっている可能性があ要ります。
(PITRでは、ベースバックアップに差分を重ねるという取り方をするが、リストアによりベースバックアップと最新のDB状態がすれた場合、後続のバックアップ処理が正しく実施できなくなる。)
そこで、ベースバックアップの再取得が必要となります。

1. 「/var/db_backup/PITR/」パスにPITRのバックアップデータがあります。これを移動させます。
2. 「flock --timeout=300 /tmp/db_backup.lock /var/backup_sh/pg_rman.sh FULL」コマンドを使って、バックアップデータが空の状態で再度バックアップを実施します。(S3同期するので注意が必要)


# 参考

[OSC北海道2014_JPUG資料 ](https://www.slideshare.net/satock/osc-hokkaido2014-backuprecovery)
[MastodonのPostgreSQLをpg_rmanを使ってバックアップする](https://blog.misosi.ru/2017/04/24/backup-postgresql-by-pg_rman-with-docker/)
[pg_rman](http://ossc-db.github.io/pg_rman/index-ja.html)
[pg_rmanを使ってみる](https://think-t.hatenablog.com/entry/2014/06/08/163035)
[pg_rmanによるPostgreSQLの簡単バックアップ＆リカバリ](https://qiita.com/bwtakacy/items/84a446c642ffae76859b)