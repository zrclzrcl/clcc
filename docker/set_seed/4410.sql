set optimizer_switch='materialization=on';
set @old_opt_switch=@@optimizer_switch;
SET sql_mode = 'NO_ENGINE_SUBSTITUTION';
create table t1 (a1 char(8), a2 char(8)) charset utf8mb4;
insert into t1 values ('1 - 00', '2 - 00');
ANALYZE TABLE t1, t2, t3;
/****************************************************************************** * Simple tests. ******************************************************************************/ # non-indexed nullable fields explain select * from t1 where a1 in (select b1 from t2 where b1 > '0');
prepare st1 from "explain select * from t1 where (a1, a2) in (select b1, max(b2) from t2i group by b1)";
execute st1;
set sql_mode=(select replace(@@sql_mode,'ONLY_FULL_GROUP_BY',''));
(select * from t1 where (a1, a2) in (select b1, b2 from t2 where b2 in (select c2 from t3 where c2 LIKE '%02') or b2 in (select c2 from t3 where c2 LIKE '%03') group by b1, b2) and (a1, a2) in (select c1, c2 from t3 where (c1, c2) in (select b1, b2 from t2i where b2 > '0'))) UNION (select * from t1i where (a1, a2) in (select b1, b2 from t2i where b1 >  '0') and (a1, a2) in (select c1, c2 from t3i where (c1, c2) in (select b1, b2 from t2i where b2 > '0')));
/* GROUP BY clause */ create table columns (col int key);
/* ORDER BY clause */ explain select * from t1 order by (select col from columns limit 1);
