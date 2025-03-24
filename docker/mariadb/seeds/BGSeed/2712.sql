set optimizer_switch='block_nested_loop=on';
set names utf8;
CREATE DATABASE world;
use world;
ANALYZE TABLE country, city, countrylanguage;
show variables like 'join_buffer_size';
set join_buffer_size=2048;
ALTER TABLE country MODIFY Name varchar(52) NOT NULL default '';
UPDATE country  SET PopulationBar=REPEAT('x', CAST(Population/100000 AS unsigned int));
use test;
INSERT INTO t1 VALUES (1616, 1571693233, 1391, 2, NULL, 'Y'), (1943, 1993216749, 1726, 2, NULL, 'Y');
