begin;
create table test_p4 partition of test for values from (30) to (40);
select pg_sleep(15);
rollback;