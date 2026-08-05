<!--
---
title: "DBA Skillset"
slug: dba-skillset
created: 2026-07-06
updated: 2026-07-06
author: admin
categories: []
tags: []
pinned: true
description: ""
---
-->

# DBA Skillset

# Table of Contents

- [Architecture & Infrastructure Design](#architecture--infrastructure-design)
- [Capacity & Storage Planning](#capacity--storage-planning)
- [Installation & Configuration](#installation--configuration)
- [Monitoring, Alerting & Logging](#monitoring-alerting--logging)
- [Backup & Recovery](#backup--recovery)
- [Replication, High Availability & Disaster Recovery](#replication-high-availability--disaster-recovery)
- [Security & Auditing](#security--auditing)
- [Database Maintenance & Performance Tuning](#database-maintenance--performance-tuning)
- [Troubleshooting & Incident Management](#troubleshooting--incident-management)
- [Additional Competencies](#additional-competencies)

---

# Architecture & Infrastructure Design

Designing a PostgreSQL platform that satisfies business, operational, and technical requirements throughout its lifecycle. This includes infrastructure topology, replication architecture, disaster recovery strategy, storage layout, data flow, and scalability planning.

## Knowledge Areas

- Standalone vs Clustered deployment
- Single DC / Multi-DC / Multi-Region
- Availability Zones
- Primary / Replica topology
- Physical Replication
- Logical Replication
- Read Scaling
- Data Lifecycle
- Archive Strategy
- Shared Nothing Architecture
- Disaster Recovery Architecture

## Concepts

- SLA / SLO / SLI
- RPO / RTO
- Failure Domains
- N+1 Redundancy
- CAP Theorem (high-level understanding)
- Scalability vs Availability trade-offs

---

# Capacity & Storage Planning

Planning infrastructure resources to ensure stable performance and future scalability. A DBA should understand hardware sizing, storage growth, backup requirements, WAL generation, and long-term capacity forecasting.

## Knowledge Areas

### Hardware

- CPU sizing
- Memory sizing
- NUMA awareness
- Storage performance
- IOPS
- Throughput

### Storage

- Local SSD
- SAN
- NAS
- XFS
- EXT4
- ZFS
- Storage Snapshots

### Planning

- Growth forecasting
- Data retention
- Archive planning
- WAL generation estimation
- Backup storage sizing

---

# Installation & Configuration

Deploying PostgreSQL and surrounding infrastructure according to production best practices.

## Knowledge Areas

### Linux

- Kernel parameters
- Huge Pages
- Transparent Huge Pages
- NUMA
- I/O Scheduler
- Filesystems

### PostgreSQL

- Standalone deployment
- Streaming Replication
- Patroni
- Stolon
- Pacemaker / Corosync

### Infrastructure

- PgBouncer
- Odyssey
- HAProxy
- Keepalived / VIP Manager
- etcd
- Consul
- ZooKeeper
- confd

---

# Monitoring, Alerting & Logging

Building observability to detect issues before they impact production.

## Knowledge Areas

### Monitoring

- Prometheus
- VictoriaMetrics
- Zabbix
- Grafana
- ASH Viewer

### Alerting

- Alertmanager
- Zabbix Triggers

### Logging

- ELK
- EFK
- Loki
- Fluent Bit

### Metrics

- PostgreSQL Exporter
- Node Exporter
- Custom Exporters

## Concepts

- RED Metrics
- USE Method
- Golden Signals
- OpenTelemetry (awareness)

---

# Backup & Recovery

Designing backup strategies that satisfy business recovery objectives and regularly validating recovery procedures.

## Knowledge Areas

### Backup

- pg_basebackup
- pgBackRest
- pg_probackup
- WAL-G
- Barman

### Logical Backup

- pg_dump
- pg_dumpall

### Recovery

- PITR
- Timeline Recovery
- Recovery Validation

## Concepts

- RPO
- RTO
- Recovery Drills

---

# Replication, High Availability & Disaster Recovery

Designing resilient PostgreSQL environments that minimize downtime and data loss.

## Knowledge Areas

### Replication

- Physical Replication
- Logical Replication
- Cascading Replication
- Synchronous Replication
- Replication Slots

### High Availability

- Patroni
- Stolon
- Pacemaker / Corosync

### Connection Routing

- PgBouncer
- HAProxy
- Odyssey
- Keepalived

### Third-party Replication

- Debezium
- Oracle GoldenGate

### Operations

- Switchover
- Failover
- Replica Re-initialization

---

# Security & Auditing

Protecting PostgreSQL infrastructure while ensuring compliance and traceability.

## Knowledge Areas

### Authentication

- SCRAM
- LDAP
- Kerberos
- Active Directory

### Authorization

- Role-Based Access Control / Model
- Least Privilege Principle

### Security

- SSL/TLS
- Secrets Management
- HashiCorp Vault

### Auditing

- pgAudit
- Logging
- SOC Awareness
- CIS Benchmark

---

# Database Maintenance & Performance Tuning

Maintaining PostgreSQL systems throughout their operational lifecycle. Optimizing PostgreSQL performance across SQL, storage, operating system, and hardware.

## Knowledge Areas

### Upgrades

- Minor Upgrade
- Major Upgrade
- pg_upgrade
- Rolling Upgrade
- Logical Replication Upgrade

### Routine Maintenance

- VACUUM
- VACUUM FULL
- ANALYZE
- REINDEX
- Bloat Management
- Statistics Maintenance
- Extension Upgrades

### Environment Management

- Replica Re-init
- Production Cloning
- Snapshot-based Cloning
- LVM Snapshots

### Schema Management

- Liquibase
- Flyway

### Database Migration

- Oracle → PostgreSQL
- ora2pg
- pgloader

### Query Optimization

- Query Plan Analysis (EXPLAIN / EXPLAIN (ANALYZE, BUFFERS))
- Query Rewriting
- Index Design
- Partitioning

### Database Tuning

- Autovacuum
- Checkpoints
- WAL

---

# Troubleshooting & Incident Management

Investigating production incidents efficiently while minimizing downtime.

## Knowledge Areas

### Incident Response

- Root Cause Analysis
- Incident Management
- Postmortems

### Troubleshooting

- Deadlocks
- Blocking Sessions
- Replication Failures
- Corruption Analysis
- Performance Degradation

---

# Additional Competencies

## Automation

Automating operational tasks to improve consistency, reliability, and efficiency.

### Knowledge Areas

#### Scripting

- Bash
- Python
- PowerShell

#### Configuration Management

- Ansible

#### Infrastructure as Code

- Terraform

#### CI/CD

- GitHub Actions
- GitLab CI
- Jenkins

#### Containers

- Docker
- Kubernetes
- Helm

#### Version Control

- Git

---

## Development Collaboration

Working closely with developers to improve database quality before production deployment.

### Knowledge Areas

- SQL Code Review
- Schema Review
- Migration Review
- Query Optimization
- Index Review
- Database Standards
- Naming Conventions

---

## Testing & Validation

Validating infrastructure changes before production rollout.

### Knowledge Areas

#### Performance Testing

- Load Testing
- Stress Testing
- Benchmarking

#### Reliability Testing

- Backup Restore Testing
- PITR Testing
- Failover Testing
- Disaster Recovery Exercises

#### Validation

- Upgrade Testing
- Migration Testing
- Capacity Testing
- Chaos Engineering (awareness)

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
