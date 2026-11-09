<!--
---
title: "DBA Incident Checklist"
slug: dba-incident-checklist
created: 2026-07-05
updated: 2026-11-09
author: admin
categories: []
tags: []
pinned: true
description: ""
---
-->

# DBA Incident Checklist

## Safety Rules

1. **Primary principle — "do no harm".** During an active incident, any production operation (restart, switchover, killing sessions, changing parameters) may make the situation worse. Diagnose first, treat second; destructive actions only after approval and with a rollback plan.
2. **Destructive actions only after approval:** DBMS restart, switchover/failover, pg_cancel_backend/pg_terminate_backend, VACUUM FULL, REINDEX, parameter changes. Before acting, capture the current state and understand the consequences.
3. **Before restarting a hung process, collect what will be lost with it:** stack traces (gdb/pstack — in coordination with the OS team), pg_stat_activity output, recent log excerpts.
4. **Change parameters carefully:** record values before and after; check whether a full DBMS restart is required or a reload is sufficient; a parameter may first need to be changed on the Replica and only then on the Master, otherwise the Replica "goes down" (max_connections and similar parameters).
5. **Have a rollback plan** before any change; prior to risky operations, verify that backups exist and are recent.
6. **Preserve evidence immediately:** logs rotate and metrics are overwritten — copy graphs, log excerpts and command output (with timestamps) into the incident artifacts.
7. **Mark the incident window** on monitoring graphs; do not disable alerts or monitoring "to stop the noise".
8. **Maintain an incident log:** time (single time zone), observation → action → result → who approved. This is the draft timeline for the RCA.
9. **Provide regular status updates** to the incident channel every 15–30 minutes, even if "we are working, nothing new".
10. **One owner of the diagnosis:** do not have multiple people making changes independently at the same time; record decisions in writing.
11. **Diagnostics must not cause harm:** run heavy queries on a replica, and make sure the diagnostic process itself does not become the cause of degradation.
12. **Do not confuse stabilization with recovery:** the service may be responding while replication lag is high or transactions are queued — the incident is closed only after all indicators have fully recovered.

## 1. Interview

- [ ] IP/FQDN of the DBMS instance (master/replicas) and of adjacent components (etcd, etc., if present)
- [ ] Period when the problem occurred (before/after)
- [ ] Exact text of the application error related to the DBMS (if any)
- [ ] Why was it concluded that the problem is in the database? (graphs dipped, timeouts, TPS dropped, etc.)
- [ ] How does it manifest in the application? "nothing works at all" / "no queries execute" / "only DDL fails" / "a specific feature does not work" => a group of queries related to that feature has probably degraded
- [ ] Were there any changes in the application / DBMS / OS / infrastructure (release, drills, switchovers, network and SAN work, migration to another virtualization platform, emergency relocation to another hypervisor, etc.)?
- [ ] Has the nature of the supplied workload changed (larger/smaller volume, different profile, non-standard day)?
- [ ] Have any elements in the chain appeared or disappeared (pgBouncer added or removed, HikariCP, Egress/Ingress, etc.)?

## 2. High-Level Diagnostics
- [ ] DBMS server utilization (CPU/MEM/IO/Free Disk Space/Network) now, before/during/after the problem period
- [ ] Wait Events in the DBMS
- [ ] DBMS and adjacent component logs (do they switch or fill up frequently, is there error spam or other suspicious messages)

**NOTE**: if the problem is already clear, proceed to resolving it.

## 3. In-Depth Diagnostics

[TOOLS](https://github.com/bazaruzero/work-notes/blob/main/posts/dba-toolset/dba-toolset.md)

### 3.1. Current Database State
- [ ] Cluster state (node roles, leader, presence of replication lag)
- [ ] Active queries and their wait events (pg_stat_activity)
- [ ] Connection count: how many are in use, by whom and from where
- [ ] Locks — capture the lock tree
- [ ] Long-running transactions and "idle in transaction"
- [ ] Temporary files: presence and growth rate
- [ ] Autovacuum: is it falling behind; are there anti-wraparound vacuums; xid age (age(datfrozenxid))
- [ ] Replication slots: activity, accumulated WAL
- [ ] WAL archiving: any archiver errors, is pg_wal growing
- [ ] Commit latency and its dynamics
- [ ] Database size and file system state

### 3.2. Logs
- [ ] The DBMS log itself
- [ ] Adjacent service logs: Patroni, PgBouncer, etcd
- [ ] dmesg / journalctl: Linux kernel errors related to Postgres (OOM-killer, segfault, I/O errors)
- [ ] Free space on file systems (PGDATA, pg_wal, log directories, temp)

### 3.3 Queries Performance
- [ ] Analysis of pg_profile reports
- [ ] Analysis of the DBMS wait event picture
- [ ] Be careful with heavy diagnostics: EXPLAIN ANALYZE on a heavy query over large tables can make the problem worse — start with EXPLAIN without ANALYZE and pg_stat_statements
- [ ] Information in the DBMS logs on long-running queries and their parameters

## 3.4. Verify Connection Limits
- [ ] In the database: max_connections, CONNECTION LIMIT of the role/database, superuser reserved slots
- [ ] In PgBouncer: max_client_conn, default_pool_size, min/max_pool_size, reserve pools
- [ ] On the application side: pool size and settings (HikariCP, etc.)
- [ ] Do the math: (number of application instances × pool size) ≤ pooler limit ≤ database limit

## 4. Retrospective Analysis for the Previous 2 Days (or from the "last known good point" to the moment of the problem)
- [ ] Wait Events
- [ ] Locks
- [ ] COMMITS and ROLLBACKS dynamics
- [ ] Connection dynamics
- [ ] Query duration
- [ ] CPU / RAM / swap utilization
- [ ] Disk response time
- [ ] pg_profile: reports BEFORE and DURING the problem — is there degradation in query execution (planning) time
- [ ] pg_store_plans: has the plan of the problematic query changed
- [ ] pg_stat_statements: top queries by time/IO before and during the problem

## 5. Deep Dive into the Problematic Query (if the problem is localized to a specific query)
- [ ] With which parameters it is called
- [ ] Which objects are used (partitioned tables, "global" indexes, etc.)
- [ ] How long ago statistics were collected (last_analyze / last_autoanalyze), when the last vacuum ran
- [ ] How fragmented/bloated (bloat) the involved objects are
- [ ] What the attribute statistics say: MCV, n_distinct and others — read via pg_stats
- [ ] Actual plan vs expected: first EXPLAIN without ANALYZE; if necessary EXPLAIN (ANALYZE, BUFFERS) — on a replica/test environment
- [ ] Try to apply [these tuning techniques](https://github.com/bazaruzero/work-notes/blob/main/posts/dba-recipes/dba-recipes.md#sql-tuning-algorithm)

## 7. Correlation "Database ↔ Server ↔ Application"
- [ ] Is there a link between database and server events: for example, higher SAN response time → average query execution time increased → a burst of connections (logon storm); or the reverse — a database problem → increased server utilization
- [ ] Does the onset of the problem coincide with a release / switchover / drills / infrastructure migration
- [ ] Is the picture the same on the master and replicas: if the problem occurs on both — a systemic cause is more likely; only on the master — load/writes are more likely
- [ ] Compare timestamps accounting for time zones and clock skew between monitoring systems and logs

## 8. Diagnostic Summary
- [ ] Hostname (FQDN) of the master and replica (if necessary)
- [ ] DBMS version
- [ ] Configuration (standalone / patroni cluster)
- [ ] Brief problem description: lock in the database / autovacuum falling behind / database not running, etc.
- [ ] Database state: running (not running)
- [ ] Errors in the database log: none (present — specify which)
- [ ] Errors in the pooler log: none (present — specify which)
- [ ] Locks in the database: none (present — attach the lock tree)
- [ ] Commit latency: none (present — N ms)
- [ ] Commit dynamics anomalies: none (present — attach a graph)
- [ ] Rollback dynamics anomalies: none (present — attach a graph)
- [ ] Connection dynamics anomalies: none (present — attach a graph)
- [ ] Segfaults: none (present — specify which)
- [ ] CPU utilization: X %
- [ ] RAM utilization: X GB free
- [ ] SWAP utilization: X GB free
- [ ] Disk response time: X ms

## 9. Artifacts

Collect all required artifacts (logs, traces, graphs, etc.) for the subsequent Postmortem analysis and retrospective.

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
