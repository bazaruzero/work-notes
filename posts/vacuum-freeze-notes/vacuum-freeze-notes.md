<!--
---
title: "Vacuum Freeze Notes"
slug: vacuum-freeze-notes
created: 2026-10-08
updated: 2026-10-08
author: admin
categories: [postgresql, theory-and-experiments]
tags: [postgres, vacuum, freeze, wraparound]
pinned: false
description: "About autovacuum thresholds and freeze mode."
---
-->

# Vacuum Freeze Notes

## Table of Contents

- [Docs](#docs)
- [Tools](#tools)
- [Environment](#environment)
- [Autovacuum triggers](#autovacuum-triggers)
- [Freeze modes and Wraparound](#freeze-modes-and-wraparound)
- [Practice](#practice)
- [Comparative table????](#comparative-table)

## Docs

- [Egor Rogov / PostgreSQL 14 Internals / 7.2 Tuple Freezing and Visibility Rules](https://edu.postgrespro.com/postgresql_internals-14_en.pdf)
- [Агрессивный автовакуум —  ужасный to prevent wraparound, зачем он нужен и как держать его в узде](https://habr.com/ru/companies/tbank/articles/919982/)
- [PostgreSQL 18 Vacuuming Improvements Explained](https://techcommunity.microsoft.com/blog/adforpostgresql/postgresql-18-vacuuming-improvements-explained/4459484)

## Environment

- Host
    - Provider: XXX
    - Device: XXX
    - CPU: XXX
    - RAM: XXX
    - Disk: XXX
    - OS: XXX
    - Virtualization: XXX
- Virtual Machine
    - vCPU: XXX
    - RAM: XXX
    - OS: XXX
- Soft:
    - PostgreSQL Database vXXX


![](images/example.png)

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
