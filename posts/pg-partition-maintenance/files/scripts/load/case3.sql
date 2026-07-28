begin;
drop table test_p3;
select pg_sleep(15);
rollback;