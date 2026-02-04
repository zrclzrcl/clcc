create table t1(a int) charset utf8mb4;
show create table t1;
insert into t1 values (0),(1),(2),(3),(4),(5),(6),(7),(8),(9);
delete from t3 where b in ('c-1013=z', 'a-1014=w');
INSERT INTO t1 VALUES (1,NULL,1130,NULL,'Hello',NULL,100,'bodyandsubject',0), (2,NULL,1130,NULL,'bye',NULL,100,'bodyandsubject',0), (3,NULL,1130,NULL,'red',NULL,100,'bodyandsubject',0), (4,NULL,1130,NULL,'yellow',NULL,100,'bodyandsubject',0), (5,NULL,1130,NULL,'blue',NULL,100,'bodyandsubject',0);
update t1 set b=repeat(char(65+a), 20) where a < 25;
set read_rnd_buffer_size=64;
