<!--
---
title: "DBA Toolset"
slug: dba-toolset
created: 2026-07-08
updated: 2026-07-08
author: admin
categories: []
tags: []
pinned: true
description: ""
---
-->

# DBA Toolset

## Table of Contents

- [Docs](#docs)
- [Linux](#linux)
  - [Linux Observability Tools](#linux-observability-tools)
  - [CPU](#cpu)
  - [Disk (Block Devices)](#disk-block-devices)
  - [Memory](#memory)
  - [Network](#network)
  - [Approaches/Strategies](#approachesstrategies)
  - [Debug](#debug)
  - [Processes](#processes)
- [Postgres](#postgres)
  - [Postgres Observability Tools](#postgres-observability-tools)
  - [Online](#online)
  - [Historical](#historical)
  - [Objects and Bloat](#objects-and-bloat)
  - [SQL-tuning](#sql-tuning)
  - [Monitoring Agents](#monitoring-agents)
  - [Data Corruption](#data-corruption)
  - [Audit and Security](#audit-and-security)
  - [Migrations](#migrations)
  - [High Availability](#high-availability)
- [Automation / DevOps](#devops)
  - 123

## Docs

 - [Как PostgreSQL может сделать больно, когда не ожидаешь — Михаил Жилин](https://rutube.ru/video/fedb4d1409f5ff09a39ba130ea874479/?r=plwd)

## Linux

### Linux Observability Tools

![Linux Observability Tools](images/linux_observability_tools.png)

[source](https://www.brendangregg.com/linuxperf.html)

### CPU

- [perf](https://www.brendangregg.com/perf.html) + [flamegraph](https://www.brendangregg.com/flamegraphs.html)
- [sar](https://man7.org/linux/man-pages/man1/sar.1.html) + [ksar](https://github.com/vlsi/ksar), [sargraph](https://github.com/sargraph/sargraph.github.io)
- eBPF

### Disk (Block Devices)

- blktrace
- ioprof
- iostat
- iotop
- [sar](https://man7.org/linux/man-pages/man1/sar.1.html) + [ksar](https://github.com/vlsi/ksar), [sargraph](https://github.com/sargraph/sargraph.github.io)
- eBPF
- lvm
- parted
- multipath

### Memory

- [perf](https://www.brendangregg.com/perf.html)
- vmstat
- pmap
- Valgrind
- [sar](https://man7.org/linux/man-pages/man1/sar.1.html) + [ksar](https://github.com/vlsi/ksar), [sargraph](https://github.com/sargraph/sargraph.github.io)
- eBPF

### Network

- tcpdump
- wireshark
- [sar](https://man7.org/linux/man-pages/man1/sar.1.html) + [ksar](https://github.com/vlsi/ksar), [sargraph](https://github.com/sargraph/sargraph.github.io)
- eBPF

### Debug

- core-dumps ([one](https://support.postgrespro.ru/note/36), [two](https://www.pgcon.org/2014/schedule/attachments/321_pgcon2014-coredump.pdf))
- gdb
- strace
- DTrace

### Processes

- strace
- pidstat
- vmstat
- gdb
- awk / grep / sed

### Approaches/Strategies

- Ansible + AWX
- Jenkins
- Terraform
- ArgoCD
- Docker
- K8s
- Python / Golang


## Postgres

### Postgres Observability Tools

![Postgres Observability Tools](images/postgres_observability_tools.png)

[source](https://pgstats.ru/?version=15)

### Online

TODO

### Historical

TODO

### Objects and Bloat

TODO

### SQL-tuning

TODO

### Monitoring Agents

TODO

### Data Corruption

TODO

### Audit and Security

TODO

### Migrations

TODO

### High Availability

TODO

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
