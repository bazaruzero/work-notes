begin;
create table test_p4 (like test including all);
alter table test attach partition test_p4 for values from (30) to (40);
select pg_sleep(15);
rollback;