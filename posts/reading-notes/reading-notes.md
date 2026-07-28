<!--
---
title: "Reading Notes"
slug: reading-notes
created: 2026-07-01
updated: 2026-07-01
author: admin
categories: []
tags: []
pinned: true
description: ""
---
-->

# Reading Notes

## 29.06.26 - 05.07.26

- [О залипании процесса checkpoint и archive_timeout в Postgres](https://habr.com/ru/companies/gnivc/articles/945742/)
- [Нетипичные методы карьерного развития или как переоткрыть себя](https://habr.com/ru/companies/gnivc/articles/1041244/)
- [Почему PostgreSQL не использует ваш индекс](https://habr.com/ru/articles/1011998/)
- [Неудобные вопросы про бэкап PostgreSQL: где заканчивается СУБД и начинается оркестрация](https://habr.com/ru/companies/hstx/articles/1015500/)

## 08.06.26 - 14.06.26

- [Книга «PostgreSQL 16. Оптимизация запросов»: учимся читать мысли планировщика](https://habr.com/ru/companies/postgrespro/articles/1014956/)
- [LWLock:LockManager, fastpath блокировки в PostgreSQL 18](https://habr.com/ru/articles/1003330/)

## 25.05.26 - 31.05.26

- [On the performance impact of REPLICA IDENTITY FULL in Postgres](https://xata.io/blog/replica-identity-full-performance)
- [Avoiding performance issues with REPLICA IDENTITY FULL in RDS for PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.ReplicaIdentityFull.html)
- [PostgreSQL — особенности работы с памятью для 1С-систем. Часть 1](https://habr.com/ru/companies/softpoint/articles/854316/)
- [PostgreSQL — особенности работы с памятью для 1С-систем. Часть 2](https://habr.com/ru/companies/softpoint/articles/861738/)
- [PostgreSQL — особенности работы с памятью для 1С-систем. Часть 3](https://habr.com/ru/companies/softpoint/articles/869446/)

## 20.04.26 - 26.04.26

- [Записки оптимизатора 1С (ч.16). Риски падения Postgres: потребление и высвобождение памяти процессами postgres](https://habr.com/ru/companies/softpoint/articles/1016828/)

  The article describes a situation where inactive PostgreSQL processes were consuming memory, and how the author arrived at that conclusion. The author conducted an experiment to test their hypothesis across different database versions. The root cause of the observed behavior remains unclear - only the fact that the problem exists is certain. The author emphasizes the importance of having a good monitoring system, since without it, they wouldn't have been able to understand the situation and figure out that idle connections (which failed to release memory after completing their work) were responsible for the memory issues. In this case, the author used Perfexpert for monitoring. The article also includes many links to other useful resources about memory management in PostgreSQL and related topics.

- [Определение фактического профиля нагрузки в PostgreSQL и динамические состояния БД](https://habr.com/ru/companies/vtb/articles/1011188/)

  For "online" monitoring: DB Time (ASH) based on pg_stat_activity.

  For "completed" monitoring: DB Time (Committed) based on pg_stat_statements.

- [Влияние удержания горизонта базы данных PostgreSQL на производительность по тесту pgbench](https://habr.com/ru/articles/890044/)

  The article examines how holding back the database horizon (vacuum cleanup horizon) degrades performance — for example, reducing TPS in benchmark tests. It also provides a query for monitoring the database horizon, along with parameters that can be used to protect against long-running transactions and queries.

## 06.04.26 - 12.04.26

- [Монолит с отчётами на 30 секунд: как я переписал архитектуру и что из этого вышло](https://habr.com/ru/articles/1019516/)

  A short article on why developers need to know how to work with ORM, look at query plans in the database, build an index strategy tailored to their queries, and generally pay attention to code quality.

- [EXPLAIN Prettier или пост-процессинг планов запросов в Postgres](https://habr.com/ru/companies/tantor/articles/1019340/)

  A brief article about a new tool for handling long query plans. Worth testing and adding to the toolkit.

- [Осваиваем replication slots в Postgres: как предотвратить разрастание WAL и другие проблемы в продакшене](https://habr.com/ru/companies/otus/articles/1018444/)

  Good advice on what to watch out for when working with logical replication slots. Includes some configuration examples for CDC with Debezium. Also has [useful links to Grafana dashboards](https://github.com/gunnarmorling/streaming-examples/tree/main/postgres-replication-slots) for monitoring.

- [Почему PostgreSQL не использует ваш индекс](https://habr.com/ru/articles/1011998/)

  A solid summary on indexes in general, including descriptions of the index types available in Postgres. A good one to keep handy — especially for index types that don't come up often in daily work.

## 23.03.26 - 29.03.26

- [Отсечь змейке хвост: останавливаем разнос базы данных, когда времени на это нет](https://habr.com/ru/companies/avito/articles/1009204/)

  About partitioning and how the problem of freeing up disk space was solved. Not very detailed, but it might be useful, for example, when migrating a standalone table to a partitioned one (the approach itself).

- [Почему VACUUM не спасает от раздувания индексов в PostgreSQL](https://habr.com/ru/companies/otus/articles/1012266/)

  A lot of interesting material on how VACUUM works with indexes and why it doesn't reduce their size. It also describes the tools to use and their specifics, as well as in which real-world situations it makes sense to take action and when it does not.

- [Как одно изменение конфигурации PostgreSQL улучшило производительность медленных запросов в 50 раз](https://habr.com/ru/articles/444018/)

  How the `random_page_cost` parameter helped stabilize Postgres to choose an index scan plan instead of a sequential scan.

- [The Search Tree (B-Tree) Makes the Index Fast](https://use-the-index-luke.com/sql/anatomy/the-tree)

  A short, schematic overview of how a B-Tree index works internally and what the letter B stands for (it means balanced, NOT binary).

## 16.03.26 - 22.03.26

- [Cybertec | What you should know about Linux memory overcommit in PostgreSQL](https://www.cybertec-postgresql.com/en/what-you-should-know-about-linux-memory-overcommit-in-postgresql/)

  Explains what Linux memory overcommit is, why it causes dangerous PostgreSQL crashes via the OOM killer, how to disable it with kernel parameters, how to correctly set memory limits to avoid out-of-memory errors, and offers practical sizing formulas for `shared_buffers` and `work_mem` - especially useful for DBAs deploying PostgreSQL on bare metal or in containers.

## 09.02.26 - 15.02.26

- [25 железных правил проектирования баз данных в PostgreSQL](https://habr.com/ru/articles/996560/)

  Fair advice. Not my favorite, but I'll keep it in mind.

- [Один "странный" случай индексного сканирования](https://habr.com/ru/companies/gnivc/articles/992660/)

  Worth a read. Key insight: PostgreSQL might switch from seq scan to index scan (bitmapscan) when the table is sparse - i.e., pages > rows. Good comments.

- [Считаем ресурсы под PostgreSQL](https://habr.com/ru/articles/995722/)

  Interesting article, but nothing super specific. Has links to config calculators. Nice AI-prompt example.

- [10 000 RPS и доступность 99,99%: как устроено шардирование PG в процессинге Яндекс Такси](https://habr.com/ru/companies/oleg-bunin/articles/985030/)

  Interesting, but more for architects and dev leads. A good reference for developers who need concrete examples.

- [База по шардированию базы](https://habr.com/ru/companies/ozontech/articles/705912/)

  Interesting example on how to shard your database with code examples on Go.

- [Очереди на PostgreSQL: антипаттерн или реальность жизни](https://habr.com/ru/companies/yandex/articles/972164/)

  Good read on PostgreSQL queue implementations - includes examples and rationale. Handy reference for developers.

---

<p align="center"><strong><sub>DISCLAIMER</sub></strong></p>

<p align="center">
<sub>
The information presented here is intended for informational purposes only.
The author assumes no responsibility or liability for any damages resulting
from the application of the techniques described herein. Use this content at
your own risk.
<br><br>
Always create backups and test configurations thoroughly before implementing
them in live environments.
</sub>
</p>
