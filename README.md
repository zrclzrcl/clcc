# 介绍
本工具是数据库模糊测试工具，目前还在开发中...

## docker镜像构建
下面简述docker启动的方法
下面的所有的命令都要在 `CLCC_REPO/` 下执行
并且要将选择使用的种子，复制`CLCC_REPO/docker/set_seed/`文件夹下
各个数据库的种子，放在了`CLCC_REPO/docker/[db_name]/seeds/`文件夹下
### MySQL
1. Squirrel
```SHELL
docker build -f ./docker/mysql/dockers/squirrel_dockerfile -t mysql_squirrel .
```
2. CLCC
```SHELL
docker build -f ./docker/mysql/dockers/clcc_dockerfile -t mysql_clcc .
```
3. SQLRight

### SQLite
1. Squirrel
```SHELL
docker build -f ./docker/sqlite/dockers/squirrel_dockerfile -t sqlite_squirrel .
```
2. CLCC
```SHELL
docker build -f ./docker/sqlite/dockers/clcc_dockerfile -t sqlite_clcc .
```
3. SQLRight
win环境需要在linux环境下运行!
```SHELL
cd ./docker/sqlite/dockers/SQLite/scripts/
./setup_sqlite.sh
```
### PostgreSQL
1. Squirrel

2. CLCC

3. SQLRight

### MariaDB
1. Squirrel

2. CLCC

3. SQLRight

### DuckDB
1. Squirrel

2. CLCC

3. SQLRight

## 启动测试
在下面的shell命令中，`--name`可以自己起名 `--cpuset-cpus=""`可以选择不添加！
### sqlite
1. squirrel
```SHELL
#下面的语句请在主机上运行
docker run -it --name sqlite_squirrel  --cpuset-cpus="30,31" sqlite_squirrel

#以下语句请在容器中运行
python3 run.py sqlite /home/Squirrel/data/fuzz_root/set_seed/
#这将启动fuzz!!
```
2. clcc
```SHELL
#下面的语句请在主机上运行
docker run -it --name sqlite_clcc  --cpuset-cpus="29,28" sqlite_clcc

#以下语句请在容器中运行,您需要两个shell窗口进行操作
#下面请在shell1中运行
cd /home/clcc
python3 count_feedbackpoint.py -t -100 -db sqlite -o 1 -k 您的api-key -conf "" -ms 65536  #这里的参数选择在后续会有详细解释

#下面请在shell2中运行
python3 clcc_run.py sqlite /home/Squirrel/data/fuzz_root/set_seed/
#这将启动fuzz!!
```

3. sqlright
```SHELL
#下面的语句请在主机上运行,如果您是windows，请在wsl或linux下运行！请确保您已经安装了docker
cd CLCC_REPO/
git submodule update --init
cd docker/sqlright/SQLite/scripts/
bash setup_sqlite.sh
cd CLCC_REPO/
docker build -f .docker/sqlright/SQLite/docker/Dockerfile -t sqlite_sqlright .
```
4.  