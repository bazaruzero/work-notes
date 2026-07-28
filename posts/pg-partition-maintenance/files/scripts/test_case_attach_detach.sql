select version();

-- create
drop table if exists test;
drop table if exists test_p1;
drop table if exists test_p2;
drop table if exists test_p3;
create table test(id bigint, data text) partition by range(id);
create table test_p1 partition of test for values from (1) to (10);
create table test_p2 partition of test for values from (10) to (20);

-- attach case 1

select 'ATTACH: create table YYY partition of XXX ...' as "CASE #1";

begin;

create table test_p3 partition of test for values from (20) to (30);

select l.pid, l.relation::regclass, l.mode, l.granted, l.fastpath
from pg_catalog.pg_stat_activity a, pg_catalog.pg_locks l, pg_class c
where 1=1
and a.pid = l.pid 
and l.relation = c.oid
and a.pid = (select pg_backend_pid())
and l.relation::regclass::text not like 'pg_%'
order by l.relation::regclass::text;

rollback;

-- attach case 2

select 'ATTACH: create table YYY ++ attach separately' as "CASE #2";

begin;

create table test_p3 (like test including all);

select l.pid, l.relation::regclass, l.mode, l.granted, l.fastpath
from pg_catalog.pg_stat_activity a, pg_catalog.pg_locks l, pg_class c
where 1=1
and a.pid = l.pid 
and l.relation = c.oid
and a.pid = (select pg_backend_pid())
and l.relation::regclass::text not like 'pg_%'
order by l.relation::regclass::text;

alter table test attach partition test_p3 for values from (20) to (30);

select l.pid, l.relation::regclass, l.mode, l.granted, l.fastpath
from pg_catalog.pg_stat_activity a, pg_catalog.pg_locks l, pg_class c
where 1=1
and a.pid = l.pid 
and l.relation = c.oid
and a.pid = (select pg_backend_pid())
and l.relation::regclass::text not like 'pg_%'
order by l.relation::regclass::text;

rollback;

-- detach case 3

select 'DETACH: drop table' as "CASE #3";

begin;

drop table test_p2;

select l.pid, l.relation::regclass, l.mode, l.granted, l.fastpath
from pg_catalog.pg_stat_activity a, pg_catalog.pg_locks l, pg_class c
where 1=1
and a.pid = l.pid 
and l.relation = c.oid
and a.pid = (select pg_backend_pid())
and l.relation::regclass::text not like 'pg_%'
order by l.relation::regclass::text;

rollback;

-- detach case 4

select 'DETACH: detach ++ drop' as "CASE #4";

begin;

alter table test detach partition test_p2;

select l.pid, l.relation::regclass, l.mode, l.granted, l.fastpath
from pg_catalog.pg_stat_activity a, pg_catalog.pg_locks l, pg_class c
where 1=1
and a.pid = l.pid 
and l.relation = c.oid
and a.pid = (select pg_backend_pid())
and l.relation::regclass::text not like 'pg_%'
order by l.relation::regclass::text;

drop table test_p2;

select l.pid, l.relation::regclass, l.mode, l.granted, l.fastpath
from pg_catalog.pg_stat_activity a, pg_catalog.pg_locks l, pg_class c
where 1=1
and a.pid = l.pid 
and l.relation = c.oid
and a.pid = (select pg_backend_pid())
and l.relation::regclass::text not like 'pg_%'
order by l.relation::regclass::text;

rollback;


-- detach case 5

select 'DETACH: detach concurrently' as "CASE #5";

-- ERROR:  ALTER TABLE ... DETACH CONCURRENTLY cannot run inside a transaction block
alter table test detach partition test_p2 concurrently;