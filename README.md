elasticsearch-aknn-0.0.1-SNAPSHOT.zip はElasticsearch 6.2.4用。

# aknnのインストール方法
- elasticsearch-aknn-0.0.1-SNAPSHOT.zip はあらかじめElasticsearch 6.2.4コンテナでビルドしておく
  - このリポジトリには成果物が含まれるので気にしなくて良い
- ビルドするときは、jdk(> 10), jre, gradle(>= 4.9)が必要

## ホストマシン
```bash
$ docker cp ./elasticsearch-aknn-0.0.1-SNAPSHOT.zip ${CONTAINER_ID}:/usr/share/elasticsearch
$ docker exec -it ${CONTAINER_ID} /bin/bash
```

## コンテナ内
```
# bin/elasticsearch-plugin install file:./elasticsearch-aknn-0.0.1-SNAPSHOT.zip
```
