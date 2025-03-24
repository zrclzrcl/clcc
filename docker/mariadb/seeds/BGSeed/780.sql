set optimizer_switch='semijoin=on,materialization=on,firstmatch=on,loosescan=on,index_condition_pushdown=on,mrr=on,mrr_cost_based=on';
set @read_rnd_buffer_size_save= @@read_rnd_buffer_size;
set read_rnd_buffer_size=79;
create table t1(a int) charset utf8mb4;
show create table t1;
insert into t1 values (0),(1),(2),(3),(4),(5),(6),(7),(8),(9);
delete from t3 where b in ('c-1013=z', 'a-1014=w');
alter table t3 add primary key(b);
ANALYZE TABLE t4;
CREATE TABLE t1 ( ID int(10) unsigned NOT NULL AUTO_INCREMENT, col1 int(10) unsigned DEFAULT NULL, key1 int(10) unsigned NOT NULL DEFAULT '0', key2 int(10) unsigned DEFAULT NULL, text1 text, text2 text, col2 smallint(6) DEFAULT '100', col3 enum('headers','bodyandsubject') NOT NULL DEFAULT 'bodyandsubject', col4 tinyint(3) unsigned NOT NULL DEFAULT '0', PRIMARY KEY (ID), KEY (key1), KEY (key2) ) AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;
INSERT INTO t1 VALUES (1,NULL,1130,NULL,'Hello',NULL,100,'bodyandsubject',0), (2,NULL,1130,NULL,'bye',NULL,100,'bodyandsubject',0), (3,NULL,1130,NULL,'red',NULL,100,'bodyandsubject',0), (4,NULL,1130,NULL,'yellow',NULL,100,'bodyandsubject',0), (5,NULL,1130,NULL,'blue',NULL,100,'bodyandsubject',0);
update t1 set b=repeat(char(65+a), 20) where a < 25;
