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
#下面的语句请在主机上运行,如果您是windows，请在wsl或linux下运行！请确保您已经安装了docker
cd CLCC_REPO/
apt install unzip
git submodule update --init
cd docker/sqlright/SQLite/scripts/
bash setup_sqlite.sh
cd CLCC_REPO/
cp -r docker/sqlite/seeds/[select seed]/* docker/set_seed/
docker build -f ./docker/sqlright/SQLite/docker/Dockerfile -t sqlite_sqlright .
```
### PostgreSQL
1. Squirrel

2. CLCC

3. SQLRight

### MariaDB
1. Squirrel
```shell
docker build -f ./docker/mariadb/dockers/squirrel_dockerfile -t mariadb_squirrel .
```
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
python3 count_feedbackpoint.py -t 0.5 -db sqlite -o 1 -k 你的LLMkey -conf "" -ms 65536 -norm 6  #这里的参数选择在后续会有详细解释

#下面请在shell2中运行
python3 clcc_run.py sqlite /home/Squirrel/data/fuzz_root/set_seed/
#这将启动fuzz!!
```

3. sqlright
```SHELL
#下面语句请在主机运行，请注意使用linux环境，同docke构建部分
cd CLCC_REPO/
cd docker/sqlright/SQLite/scripts
docker run -it -v ~/clcc/docker/sqlright/SQLite/Results/fuzz_output:/home/sqlite/fuzzing/fuzz_root/outputs -v ~/clcc/docker/sqlright/SQLite/Results/bug_output:/home/sqlite/fuzzing/Bug_Analysis --name sqlite_sqlright_bgseed_1 --cpuset-cpus="24,25" sqlite_sqlright_bgseed

#下面语句请在容器中运行！
python3 run_parallel.py -o /home/sqlite/fuzzing/fuzz_root/outputs -E --start-core 24 --num-concurrent 1 --oracle NOREC
```
### mariadb
1. squirrel
```SHELL
#下面语句请在主机运行！
docker run -it --name mariadb_squirrel_bgseed_1  --cpuset-cpus="26,27" mariadb_squirrel_bgseed

#下面语句请在容器中运行！
python3 run.py mariadb /home/Squirrel/data/fuzz_root/set_seed/
```
2.  

### mysql
1. squirrel
```SHELL
#下面的语句请在主机上运行
docker run -it --name mysql_squirrel  --cpuset-cpus="30,31" mysql_squirrel

#以下语句请在容器中运行
AFL_IGNORE_PROBLEMS=1 AFL_MAP_SIZE=$(cat /tmp/mapsize) python3 run.py mysql /home/Squirrel/data/fuzz_root/set_seed/
#这将启动fuzz!!
```
2. clcc
```SHELL
#下面的语句请在主机上运行
docker run -it --name mysql_clcc  --cpuset-cpus="29,28" mysql_clcc

#以下语句请在容器中运行,您需要两个shell窗口进行操作
#下面请在shell1中运行
cd /home/clcc
python3 count_feedbackpoint.py -t 0.5 -db mysql -o 1 -k 你的LLMkey -conf "/home/Squirrel/data/mysql_showmap_config.yml" -ms [check mapsize!] -norm 6  #这里的参数选择在后续会有详细解释

#下面请在shell2中运行
AFL_IGNORE_PROBLEMS=1 AFL_MAP_SIZE=$(cat /tmp/mapsize) python3 clcc_run.py mysql /home/Squirrel/data/fuzz_root/set_seed/
#这将启动fuzz!!
```
4. 