begin;
alter table test detach partition test_p3;
select pg_sleep(15);
drop table test_p3;
rollback;